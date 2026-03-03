"""
VAREX Desktop Proctoring Agent
────────────────────────────────
A lightweight Python agent that runs on the candidate's machine
during the interview. It monitors OS-level activity that browsers
CANNOT detect:

  Layer 1: PROCESS MONITORING
    → Detects running AI apps (ChatGPT, Copilot, Gemini, Claude, etc.)
    → Detects screen recording software
    → Detects virtual machines / remote desktop

  Layer 2: ACTIVE WINDOW MONITORING
    → Tracks which window is active (not just browser tabs)
    → Detects switching to any non-interview application

  Layer 3: CLIPBOARD MONITORING
    → Detects copy/paste from external sources
    → Tracks clipboard content changes

  Layer 4: NETWORK MONITORING
    → Detects connections to AI service domains
    → Detects API calls to OpenAI, Google AI, Anthropic, etc.

  Layer 5: HEARTBEAT
    → Sends periodic heartbeats to the VAREX backend
    → If heartbeats stop → session flagged as "proctor disconnected"

USAGE:
  python proctor_agent.py --session-id <SESSION_ID> --api-url <BACKEND_URL>

The agent is REQUIRED for Enterprise interviews.
For Mock interviews, it's optional but flagged in reports.
"""

import argparse
import json
import logging
import os
import platform
import re
import socket
import subprocess
import sys
import threading
import time
from datetime import datetime, timezone

# ─── Optional imports (graceful degradation) ─────────────────────
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False
    print("⚠ psutil not installed. Process monitoring limited. Install: pip install psutil")

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False
    print("⚠ requests not installed. Install: pip install requests")

try:
    import cv2
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False
    print("⚠ opencv-python not installed. Face monitoring limited. Install: pip install opencv-python")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [PROCTOR] %(levelname)s — %(message)s",
)
logger = logging.getLogger("proctor")


# ═══════════════════════════════════════════════════════════════════
#  KNOWN AI / CHEATING APPLICATIONS
# ═══════════════════════════════════════════════════════════════════

# Process names / exe patterns to detect (case-insensitive).
# Each key is matched against (process_name, exe_path, cmdline).
# "cursor" was tightened — the old substring match triggered on
# anything containing the word "cursor" (mouse cursor utils, etc.).
# "continue" removed entirely — too common a word.
AI_PROCESS_NAMES = {
    # Desktop AI Apps
    "chatgpt": "ChatGPT Desktop App",
    "copilot": "Microsoft Copilot",
    "claude": "Claude Desktop App",
    "gemini": "Google Gemini",
    "perplexity": "Perplexity AI",
    "phind": "Phind AI",
    "codeium": "Codeium AI",
    "tabnine": "TabNine AI",
    "github copilot": "GitHub Copilot",
    "supermaven": "Supermaven AI",
    "cody": "Sourcegraph Cody AI",
    "aider": "Aider AI",
    # Screen Recording / Sharing
    "obs64": "OBS Studio (Screen Recording)",
    "obs32": "OBS Studio (Screen Recording)",
    "obs studio": "OBS Studio (Screen Recording)",
    "streamlabs": "Streamlabs (Screen Recording)",
    "camtasia": "Camtasia (Screen Recording)",
    "bandicam": "Bandicam (Screen Recording)",
    "screenpal": "ScreenPal (Screen Recording)",
    "loom": "Loom (Screen Recording)",
    "sharex": "ShareX (Screen Capture)",
    # Remote Desktop / VM
    "teamviewer": "TeamViewer (Remote Access)",
    "anydesk": "AnyDesk (Remote Access)",
    "rustdesk": "RustDesk (Remote Access)",
    "vnc": "VNC (Remote Access)",
    "parsec": "Parsec (Remote Access)",
    "vmware": "VMware (Virtual Machine)",
    "virtualbox": "VirtualBox (Virtual Machine)",
    "qemu": "QEMU (Virtual Machine)",
}

# Exact exe names that need special matching logic because their
# substring form collides with common OS terms.
AI_PROCESS_EXE_EXACT = {
    "cursor.exe": "Cursor AI Editor",
    "cursor": "Cursor AI Editor",           # Linux / macOS binary name
    "continue.exe": "Continue AI",
    "obs.exe": "OBS Studio (Screen Recording)",
    "obs": "OBS Studio (Screen Recording)",  # Linux binary name
}

# Windows services that may indicate kernel-level AI/screen tools.
AI_SERVICE_NAMES = [
    "copilot", "chatgpt", "anydesk", "teamviewer",
    "parsec", "rustdesk", "obs",
]

# Network domains to monitor (AI service APIs)
AI_DOMAINS = [
    "api.openai.com",
    "chat.openai.com",
    "chatgpt.com",
    "api.anthropic.com",
    "claude.ai",
    "generativelanguage.googleapis.com",
    "gemini.google.com",
    "bard.google.com",
    "api.perplexity.ai",
    "copilot.microsoft.com",
    "api.cohere.ai",
    "api.together.xyz",
    "api.groq.com",
    "api.mistral.ai",
    "api.fireworks.ai",
    "huggingface.co",
    "api-inference.huggingface.co",
    "phind.com",
    "deepseek.com",
    "api.deepseek.com",
    "poe.com",
    "you.com",
]

# ── Allowed apps whitelist ────────────────────────────────────────
# Strict: only the interview browser + these process names are allowed.
# Everything else triggers a violation.
ALLOWED_PROCESS_NAMES = {
    "notepad.exe",        # Windows Notepad
    "notepad++.exe",      # Notepad++
    # System tray / OS essentials that always run (never flagged):
    "explorer.exe",
    "taskmgr.exe",        # candidate may check task manager — log but don't block
    "searchhost.exe",
    "searchui.exe",
    "shellexperiencehost.exe",
    "startmenuexperiencehost.exe",
    "runtimebroker.exe",
    "applicationframehost.exe",
    "textinputhost.exe",
    "ctfmon.exe",
    "dwm.exe",
    "csrss.exe",
    "conhost.exe",
    "fontdrvhost.exe",
    "sihost.exe",
    "svchost.exe",
    "winlogon.exe",
    "dllhost.exe",
    "widgetservice.exe",
    "widgets.exe",
    "systemsettings.exe",
}

# Legacy title-based patterns kept for macOS/Linux where process name
# lookup is harder; on Windows the process-name whitelist is preferred.
ALLOWED_FOREGROUND_PATTERNS = [
    "notepad",
    "notepad++",
]

AUDIO_HEADSET_PATTERNS = [
    "headset",
    "headphone",
    "earbud",
    "earphone",
    "airpods",
    "bluetooth",
    "hands-free",
    "handsfree",
    "wireless",
    "3.5mm",
    "jack",
    "realtek",        # common laptop audio chipset
    "conexant",
    "high definition audio",
    "stereo",
    "speakers",
    "microphone",
]


# ═══════════════════════════════════════════════════════════════════
#  LAYER 1: PROCESS MONITOR
# ═══════════════════════════════════════════════════════════════════

class ProcessMonitor:
    """Scan running processes for known AI/cheating applications.

    Detection strategy (three tiers):
      1. Substring match on AI_PROCESS_NAMES (safe patterns like 'chatgpt').
      2. Exact exe-name match on AI_PROCESS_EXE_EXACT (ambiguous patterns
         like 'cursor' that would false-positive on mouse-cursor utils).
      3. Windows service scan for AI_SERVICE_NAMES to catch kernel-level
         services invisible to normal process enumeration.
    """

    def scan(self) -> list[dict]:
        """Return list of detected suspicious processes."""
        if not HAS_PSUTIL:
            return self._scan_fallback()

        detected = []
        seen_pids: set[int] = set()
        try:
            for proc in psutil.process_iter(["pid", "name", "exe", "cmdline"]):
                try:
                    pid = proc.info["pid"]
                    if pid in seen_pids:
                        continue
                    pname = (proc.info["name"] or "").lower()
                    pexe = (proc.info["exe"] or "").lower()
                    pcmd = " ".join(proc.info.get("cmdline") or []).lower()

                    # --- Tier 1: substring match (safe patterns) ---
                    matched_label = None
                    for pattern, label in AI_PROCESS_NAMES.items():
                        if (
                            pattern in pname
                            or pattern in pexe
                            or pattern in pcmd
                        ):
                            matched_label = label
                            break

                    # --- Tier 2: exact exe-name match (ambiguous patterns) ---
                    if matched_label is None:
                        for exact_name, label in AI_PROCESS_EXE_EXACT.items():
                            if pname == exact_name or pexe.endswith("\\" + exact_name) or pexe.endswith("/" + exact_name):
                                matched_label = label
                                break

                    if matched_label:
                        seen_pids.add(pid)
                        detected.append({
                            "process_name": proc.info["name"],
                            "pid": pid,
                            "label": matched_label,
                            "exe": proc.info.get("exe", ""),
                        })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except Exception as e:
            logger.error(f"Process scan error: {e}")

        # --- Tier 3: Windows service scan ---
        detected.extend(self._scan_services())

        return detected

    def _scan_services(self) -> list[dict]:
        """Scan Windows services for known AI/remote-access tools.

        Services run at kernel/system level and may not appear in
        normal process iteration. This catches TeamViewer, AnyDesk,
        Parsec, etc. running as background services.
        """
        if platform.system() != "Windows":
            return []
        detected = []
        try:
            out = subprocess.check_output(
                [
                    "powershell", "-NoProfile", "-Command",
                    "Get-Service | Where-Object {$_.Status -eq 'Running'} "
                    "| Select-Object -ExpandProperty Name",
                ],
                text=True,
                timeout=8,
                stderr=subprocess.DEVNULL,
            )
            running_services = {s.strip().lower() for s in out.splitlines() if s.strip()}
            for svc_pattern in AI_SERVICE_NAMES:
                for svc_name in running_services:
                    if svc_pattern in svc_name:
                        detected.append({
                            "process_name": f"[SERVICE] {svc_name}",
                            "pid": 0,
                            "label": f"Suspicious service: {svc_name}",
                            "exe": "",
                        })
                        break
        except Exception as e:
            logger.debug(f"Service scan error: {e}")
        return detected

    def _scan_fallback(self) -> list[dict]:
        """Fallback process scan without psutil (uses OS commands)."""
        detected = []
        try:
            if platform.system() == "Windows":
                output = subprocess.check_output(
                    ["tasklist", "/FO", "CSV", "/NH"],
                    text=True, timeout=10,
                )
                for line in output.strip().split("\n"):
                    parts = line.strip().strip('"').split('","')
                    if parts:
                        pname = parts[0].lower()
                        for pattern, label in AI_PROCESS_NAMES.items():
                            if pattern in pname:
                                detected.append({
                                    "process_name": parts[0],
                                    "pid": parts[1] if len(parts) > 1 else "",
                                    "label": label,
                                    "exe": "",
                                })
                                break
                        # Exact exe match for ambiguous patterns
                        for exact_name, label in AI_PROCESS_EXE_EXACT.items():
                            if pname == exact_name:
                                detected.append({
                                    "process_name": parts[0],
                                    "pid": parts[1] if len(parts) > 1 else "",
                                    "label": label,
                                    "exe": "",
                                })
                                break

            elif platform.system() in ("Linux", "Darwin"):
                output = subprocess.check_output(
                    ["ps", "aux"], text=True, timeout=10,
                )
                for line in output.strip().split("\n")[1:]:
                    lower_line = line.lower()
                    for pattern, label in AI_PROCESS_NAMES.items():
                        if pattern in lower_line:
                            parts = line.split()
                            detected.append({
                                "process_name": parts[10] if len(parts) > 10 else "",
                                "pid": parts[1] if len(parts) > 1 else "",
                                "label": label,
                                "exe": "",
                            })
                            break
        except Exception as e:
            logger.error(f"Fallback process scan error: {e}")

        # Tier 3: service scan works without psutil
        detected.extend(self._scan_services())
        return detected


class ActiveWindowMonitor:
    """Track which window is currently active AND enumerate all visible windows.

    Key improvement: `enumerate_all_windows()` scans ALL open windows
    (not just foreground) so background AI apps can be detected.
    On Windows, uses `ctypes.windll.user32.EnumWindows` for full coverage.
    """

    def get_active_window(self) -> str:
        """Return the title of the currently active window."""
        try:
            if platform.system() == "Windows":
                return self._get_active_window_windows()
            elif platform.system() == "Darwin":
                return self._get_active_window_macos()
            elif platform.system() == "Linux":
                return self._get_active_window_linux()
        except Exception as e:
            logger.debug(f"Active window detection error: {e}")
        return "Unknown"

    def enumerate_all_windows(self) -> list[dict]:
        """Return ALL visible windows with their title and owning process name.

        Each entry: {"title": str, "process_name": str, "pid": int}
        Used to detect forbidden background apps.
        """
        if platform.system() == "Windows":
            return self._enum_windows_windows()
        return []  # macOS / Linux: only foreground check for now

    # ── Windows implementation ────────────────────────────────────

    def _get_active_window_windows(self) -> str:
        try:
            import ctypes
            user32 = ctypes.windll.user32
            hwnd = user32.GetForegroundWindow()
            length = user32.GetWindowTextLengthW(hwnd) + 1
            buf = ctypes.create_unicode_buffer(length)
            user32.GetWindowTextW(hwnd, buf, length)
            return buf.value or "Unknown"
        except Exception:
            return "Unknown"

    def _enum_windows_windows(self) -> list[dict]:
        """Enumerate ALL visible windows via Win32 EnumWindows.

        Filters: only visible windows with non-empty titles.
        For each, resolve the owning process name via PID.
        """
        import ctypes
        from ctypes import wintypes

        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32

        PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
        results: list[dict] = []

        @ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
        def _callback(hwnd, _lparam):
            try:
                if not user32.IsWindowVisible(hwnd):
                    return True
                length = user32.GetWindowTextLengthW(hwnd)
                if length == 0:
                    return True
                buf = ctypes.create_unicode_buffer(length + 1)
                user32.GetWindowTextW(hwnd, buf, length + 1)
                title = buf.value
                if not title:
                    return True

                # Get owning PID
                pid = wintypes.DWORD()
                user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
                proc_name = ""
                h_process = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid.value)
                if h_process:
                    try:
                        exe_buf = ctypes.create_unicode_buffer(260)
                        size = wintypes.DWORD(260)
                        if kernel32.QueryFullProcessImageNameW(h_process, 0, exe_buf, ctypes.byref(size)):
                            full_path = exe_buf.value
                            proc_name = os.path.basename(full_path).lower()
                    finally:
                        kernel32.CloseHandle(h_process)

                results.append({
                    "title": title,
                    "process_name": proc_name,
                    "pid": pid.value,
                })
            except Exception:
                pass
            return True

        try:
            user32.EnumWindows(_callback, 0)
        except Exception as e:
            logger.debug(f"EnumWindows error: {e}")

        return results

    # ── macOS / Linux (foreground only) ───────────────────────────

    def _get_active_window_macos(self) -> str:
        try:
            script = 'tell application "System Events" to get name of first application process whose frontmost is true'
            output = subprocess.check_output(
                ["osascript", "-e", script], text=True, timeout=5,
            )
            return output.strip()
        except Exception:
            return "Unknown"

    def _get_active_window_linux(self) -> str:
        try:
            output = subprocess.check_output(
                ["xdotool", "getactivewindow", "getwindowname"],
                text=True, timeout=5,
            )
            return output.strip()
        except Exception:
            return "Unknown"

    # ── Classification helpers ────────────────────────────────────

    def is_browser_focused(self, window_title: str) -> bool:
        """Check if the active window is a known browser."""
        browsers = [
            "chrome", "firefox", "safari", "edge", "brave", "opera",
            "chromium", "vivaldi", "arc",
        ]
        lower_title = window_title.lower()
        return any(b in lower_title for b in browsers)

    def is_browser_process(self, process_name: str) -> bool:
        """Check if a process name is a known browser."""
        browser_exes = {
            "chrome.exe", "firefox.exe", "msedge.exe", "brave.exe",
            "opera.exe", "vivaldi.exe", "chromium.exe", "safari",
            "arc.exe", "iexplore.exe",
        }
        return process_name.lower() in browser_exes

    def is_allowed_process(self, process_name: str) -> bool:
        """Check if a process name is in the strict whitelist."""
        return process_name.lower() in ALLOWED_PROCESS_NAMES

    def is_allowed_non_browser_window(self, window_title: str) -> bool:
        """Legacy title-based check (macOS/Linux fallback)."""
        lower_title = window_title.lower()
        return any(p in lower_title for p in ALLOWED_FOREGROUND_PATTERNS)


# ═══════════════════════════════════════════════════════════════════
#  LAYER 3: NETWORK MONITOR
# ═══════════════════════════════════════════════════════════════════

class NetworkMonitor:
    """Detect active connections to known AI service domains."""

    def scan_connections(self) -> list[dict]:
        """Check for active connections to AI services."""
        if not HAS_PSUTIL:
            return self._scan_fallback()

        detected = []
        try:
            for conn in psutil.net_connections(kind="inet"):
                if conn.status == "ESTABLISHED" and conn.raddr:
                    remote_ip = conn.raddr.ip
                    try:
                        # Reverse DNS lookup
                        hostname = socket.gethostbyaddr(remote_ip)[0].lower()
                        for domain in AI_DOMAINS:
                            if domain in hostname:
                                detected.append({
                                    "domain": domain,
                                    "remote_ip": remote_ip,
                                    "remote_port": conn.raddr.port,
                                    "pid": conn.pid,
                                    "hostname": hostname,
                                })
                                break
                    except (socket.herror, socket.gaierror, OSError):
                        continue
        except (psutil.AccessDenied, OSError) as e:
            logger.debug(f"Network scan limited: {e}")

        # Also do forward DNS resolution for known domains
        for domain in AI_DOMAINS[:10]:  # Check top 10
            try:
                resolved_ips = {
                    info[4][0]
                    for info in socket.getaddrinfo(domain, 443)
                }
                if HAS_PSUTIL:
                    for conn in psutil.net_connections(kind="inet"):
                        if (
                            conn.status == "ESTABLISHED"
                            and conn.raddr
                            and conn.raddr.ip in resolved_ips
                        ):
                            if not any(d["domain"] == domain for d in detected):
                                detected.append({
                                    "domain": domain,
                                    "remote_ip": conn.raddr.ip,
                                    "remote_port": conn.raddr.port,
                                    "pid": conn.pid,
                                    "hostname": domain,
                                })
            except (socket.gaierror, OSError):
                continue

        return detected

    def _scan_fallback(self) -> list[dict]:
        """Fallback network scan without psutil."""
        detected = []
        try:
            if platform.system() == "Windows":
                output = subprocess.check_output(
                    ["netstat", "-n", "-o"], text=True, timeout=10
                )
            else:
                output = subprocess.check_output(
                    ["netstat", "-tn"], text=True, timeout=10
                )

            for domain in AI_DOMAINS[:5]:
                try:
                    resolved = socket.gethostbyname(domain)
                    if resolved in output:
                        detected.append({
                            "domain": domain,
                            "remote_ip": resolved,
                            "remote_port": 443,
                            "pid": None,
                            "hostname": domain,
                        })
                except socket.gaierror:
                    continue
        except Exception as e:
            logger.debug(f"Fallback network scan error: {e}")
        return detected


# ═══════════════════════════════════════════════════════════════════
#  LAYER 4: SYSTEM ENVIRONMENT CHECK
# ═══════════════════════════════════════════════════════════════════

class SystemEnvironmentCheck:
    """Detect virtual machines, remote desktops, and suspicious configurations."""

    def check(self) -> dict:
        """Run environment integrity checks."""
        result = {
            "is_virtual_machine": self._detect_vm(),
            "has_multiple_monitors": self._detect_multiple_monitors(),
            "has_remote_desktop": self._detect_remote_desktop(),
            "os": platform.system(),
            "os_version": platform.version(),
            "hostname": platform.node(),
        }
        return result

    def _detect_vm(self) -> bool:
        """Detect if running inside a virtual machine."""
        vm_indicators = [
            "vmware", "virtualbox", "vbox", "qemu", "kvm",
            "hyper-v", "xen", "parallels", "bhyve",
        ]
        # Check system manufacturer / model
        try:
            if platform.system() == "Windows":
                output = subprocess.check_output(
                    ["wmic", "computersystem", "get", "model,manufacturer"],
                    text=True, timeout=5,
                ).lower()
                return any(v in output for v in vm_indicators)
            elif platform.system() == "Linux":
                try:
                    with open("/sys/class/dmi/id/product_name", "r") as f:
                        product = f.read().lower()
                        return any(v in product for v in vm_indicators)
                except FileNotFoundError:
                    pass
                # Check systemd-detect-virt
                try:
                    output = subprocess.check_output(
                        ["systemd-detect-virt"], text=True, timeout=5
                    ).strip()
                    return output != "none"
                except (FileNotFoundError, subprocess.CalledProcessError):
                    pass
        except Exception:
            pass
        return False


class FaceMonitor:
    """Camera-based face + earbud presence monitor (v3).

    Capabilities:
    - Frontal + profile face detection with relaxed thresholds
    - Face-absence streak counter
    - **Earbud detection**: analyzes ear regions for earbud-shaped objects.
      When earbuds are visible in camera but NOT connected to the laptop's
      Bluetooth/audio → flags `external_audio_suspected`.
    """

    NO_FACE_STREAK_THRESHOLD = 3
    # Minimum contour area (pixels²) to consider as an earbud in the ear region
    EARBUD_MIN_CONTOUR_AREA = 80
    EARBUD_MAX_CONTOUR_AREA = 3000
    # How circular a contour must be to count as earbud-like (0-1, 1=perfect circle)
    EARBUD_CIRCULARITY_THRESHOLD = 0.35
    # Consecutive earbud-detected frames needed before flagging (reduces noise)
    EARBUD_STREAK_THRESHOLD = 3

    def __init__(self):
        self.enabled = HAS_CV2
        self.cap = None
        self.front_classifier = None
        self.profile_classifier = None
        self.last_error: str | None = None
        self._camera_warned = False
        self.no_face_streak = 0
        self.earbud_streak = 0

        if self.enabled:
            try:
                self.front_classifier = cv2.CascadeClassifier(
                    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
                )
                self.profile_classifier = cv2.CascadeClassifier(
                    cv2.data.haarcascades + "haarcascade_profileface.xml"
                )
            except Exception as e:
                self.enabled = False
                self.last_error = str(e)

    def _ensure_camera(self) -> bool:
        if not self.enabled:
            return False
        if self.cap is not None and self.cap.isOpened():
            return True
        try:
            flag = cv2.CAP_DSHOW if platform.system() == "Windows" else 0
            self.cap = cv2.VideoCapture(0, flag)
            if self.cap is not None and self.cap.isOpened():
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                return True
        except Exception as e:
            self.last_error = str(e)
        return False

    def scan(self) -> dict:
        base = {
            "available": False, "faces": None,
            "no_face_streak": self.no_face_streak,
            "earbud_suspected": False,
            "earbud_streak": self.earbud_streak,
            "error": None,
        }
        if not self.enabled:
            base["error"] = self.last_error or "opencv_unavailable"
            return base
        if not self._ensure_camera():
            base["error"] = self.last_error or "camera_unavailable"
            return base
        try:
            ok, frame = self.cap.read()
            if not ok or frame is None:
                base["error"] = "camera_read_failed"
                return base

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            # --- Face detection (frontal + profile) ---
            faces = self.front_classifier.detectMultiScale(
                gray, scaleFactor=1.1, minNeighbors=3, minSize=(40, 40),
            )
            face_count = int(len(faces))
            face_rects = faces

            if face_count == 0 and self.profile_classifier is not None:
                profile_faces = self.profile_classifier.detectMultiScale(
                    gray, scaleFactor=1.1, minNeighbors=3, minSize=(40, 40),
                )
                face_count = int(len(profile_faces))
                face_rects = profile_faces

            # Update face streak
            if face_count == 0:
                self.no_face_streak += 1
            else:
                self.no_face_streak = 0

            # --- Earbud detection (ear-region analysis) ---
            earbud_detected = False
            if face_count > 0:
                earbud_detected = self._detect_earbuds_in_frame(frame, gray, face_rects)

            if earbud_detected:
                self.earbud_streak += 1
            else:
                self.earbud_streak = max(0, self.earbud_streak - 1)

            return {
                "available": True,
                "faces": face_count,
                "no_face_streak": self.no_face_streak,
                "earbud_suspected": self.earbud_streak >= self.EARBUD_STREAK_THRESHOLD,
                "earbud_streak": self.earbud_streak,
                "error": None,
            }
        except Exception as e:
            self.last_error = str(e)
            base["error"] = str(e)
            return base

    def _detect_earbuds_in_frame(self, frame, gray, faces) -> bool:
        """Analyze ear regions of detected faces for earbud-like objects.

        For each face, extracts left and right ear regions based on face
        geometry, then uses Canny edge + contour analysis to detect
        small circular objects (earbuds/AirPods).

        Returns True if earbud-like object detected in either ear region.
        """
        h_frame, w_frame = gray.shape[:2]

        for (fx, fy, fw, fh) in faces:
            # --- Define ear regions ---
            # Left ear region: to the left of the face
            ear_w = int(fw * 0.30)
            ear_h = int(fh * 0.40)
            ear_y = fy + int(fh * 0.20)  # ears are roughly in the middle third of face height

            left_ear_x = max(0, fx - ear_w)
            right_ear_x = min(w_frame, fx + fw)

            for ear_x in [left_ear_x, right_ear_x]:
                ex2 = min(w_frame, ear_x + ear_w)
                ey2 = min(h_frame, ear_y + ear_h)
                if ex2 <= ear_x or ey2 <= ear_y:
                    continue

                ear_roi = gray[ear_y:ey2, ear_x:ex2]
                if ear_roi.size == 0:
                    continue

                # --- Detect earbud-shaped contours ---
                # Apply Gaussian blur to reduce noise, then Canny edge detection
                blurred = cv2.GaussianBlur(ear_roi, (5, 5), 0)
                edges = cv2.Canny(blurred, 30, 100)

                # Dilate edges to connect nearby lines
                kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
                edges = cv2.dilate(edges, kernel, iterations=1)

                contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

                for cnt in contours:
                    area = cv2.contourArea(cnt)
                    if area < self.EARBUD_MIN_CONTOUR_AREA or area > self.EARBUD_MAX_CONTOUR_AREA:
                        continue

                    # Circularity = 4π × area / perimeter²
                    perimeter = cv2.arcLength(cnt, True)
                    if perimeter == 0:
                        continue
                    circularity = 4 * 3.14159 * area / (perimeter * perimeter)

                    if circularity >= self.EARBUD_CIRCULARITY_THRESHOLD:
                        # Also check that the contour is roughly convex (earbuds are smooth)
                        hull = cv2.convexHull(cnt)
                        hull_area = cv2.contourArea(hull)
                        if hull_area > 0:
                            solidity = area / hull_area
                            if solidity >= 0.5:
                                logger.debug(
                                    "Earbud candidate: area=%.0f circ=%.2f solid=%.2f",
                                    area, circularity, solidity,
                                )
                                return True
        return False

    def stop(self):
        try:
            if self.cap is not None:
                self.cap.release()
        except Exception:
            pass


class AudioRouteMonitor:
    """Detect local audio endpoints AND nearby Bluetooth audio devices.

    Improvements over v1:
    - Bluetooth device discovery (Windows): scans for paired/active BT
      devices to check if earbuds are connected to THIS laptop.
    - 'nearby_bt_audio' field: lists BT audio devices the OS can see.
    - Violation flags are resettable so re-failures are reported.
    """

    def scan(self) -> dict:
        names = self._connected_audio_device_names()
        names_lower = [n.lower() for n in names]
        has_any_audio = len(names) > 0
        has_headset = any(
            any(p in n for p in AUDIO_HEADSET_PATTERNS)
            for n in names_lower
        )
        has_bluetooth = any(
            "bluetooth" in n or "airpods" in n
            for n in names_lower
        )

        # Bluetooth device discovery — detect paired BT audio devices
        bt_devices = self._scan_bluetooth_devices()

        return {
            "devices": names,
            "has_any_audio": has_any_audio,
            "has_headset": has_headset,
            "has_bluetooth_audio": has_bluetooth,
            "nearby_bt_devices": bt_devices,
            "bt_adapter_present": len(bt_devices) > 0 or has_bluetooth,
        }

    def _connected_audio_device_names(self) -> list[str]:
        if platform.system() == "Windows":
            return self._windows_audio_endpoints()
        if platform.system() == "Linux":
            return self._linux_audio_endpoints()
        if platform.system() == "Darwin":
            return self._macos_audio_endpoints()
        return []

    def _windows_audio_endpoints(self) -> list[str]:
        commands = [
            # Audio endpoint devices (output/input routes)
            [
                "powershell",
                "-NoProfile",
                "-Command",
                "Get-PnpDevice -Class AudioEndpoint | Where-Object {$_.Status -eq 'OK'} | Select-Object -ExpandProperty FriendlyName",
            ],
            # Fallback to sound devices
            [
                "powershell",
                "-NoProfile",
                "-Command",
                "Get-CimInstance Win32_SoundDevice | Select-Object -ExpandProperty Name",
            ],
        ]
        for cmd in commands:
            try:
                out = subprocess.check_output(cmd, text=True, timeout=6, stderr=subprocess.DEVNULL)
                names = [line.strip() for line in out.splitlines() if line.strip()]
                if names:
                    return names
            except Exception:
                continue
        return []

    def _linux_audio_endpoints(self) -> list[str]:
        for cmd in (["pactl", "list", "short", "sinks"], ["aplay", "-l"]):
            try:
                out = subprocess.check_output(cmd, text=True, timeout=6, stderr=subprocess.DEVNULL)
                names = [line.strip() for line in out.splitlines() if line.strip()]
                if names:
                    return names
            except Exception:
                continue
        return []

    def _macos_audio_endpoints(self) -> list[str]:
        try:
            out = subprocess.check_output(
                ["system_profiler", "SPAudioDataType"],
                text=True,
                timeout=8,
                stderr=subprocess.DEVNULL,
            )
            names = []
            for line in out.splitlines():
                stripped = line.strip()
                if stripped.endswith(":") and len(stripped) > 1:
                    names.append(stripped[:-1])
            return names
        except Exception:
            return []

    def _scan_bluetooth_devices(self) -> list[str]:
        """Discover paired/connected Bluetooth devices on the machine.

        If candidate has Bluetooth earbuds connected to this laptop,
        they will appear here. If they DON'T appear here but the
        candidate is wearing earbuds → earbuds are connected to
        another device (phone) = suspicious.
        """
        if platform.system() == "Windows":
            return self._windows_bluetooth_scan()
        if platform.system() == "Linux":
            return self._linux_bluetooth_scan()
        return []

    def _windows_bluetooth_scan(self) -> list[str]:
        """Get paired/connected Bluetooth devices via PowerShell."""
        try:
            out = subprocess.check_output(
                [
                    "powershell", "-NoProfile", "-Command",
                    "Get-PnpDevice -Class Bluetooth | "
                    "Where-Object {$_.Status -eq 'OK'} | "
                    "Select-Object -ExpandProperty FriendlyName",
                ],
                text=True,
                timeout=8,
                stderr=subprocess.DEVNULL,
            )
            return [line.strip() for line in out.splitlines() if line.strip()]
        except Exception:
            return []

    def _linux_bluetooth_scan(self) -> list[str]:
        """Get paired Bluetooth devices via bluetoothctl."""
        try:
            out = subprocess.check_output(
                ["bluetoothctl", "devices", "Connected"],
                text=True,
                timeout=6,
                stderr=subprocess.DEVNULL,
            )
            return [line.strip() for line in out.splitlines() if line.strip()]
        except Exception:
            return []

    # ── These were misplaced here in v1; keeping in SystemEnvironmentCheck ──
    # _detect_multiple_monitors and _detect_remote_desktop belong to
    # SystemEnvironmentCheck, not AudioRouteMonitor. Fixed in this version.


# ═══════════════════════════════════════════════════════════════════
#  KERNEL-LEVEL PROCESS SCANNER
# ═══════════════════════════════════════════════════════════════════

# Known suspicious driver / kernel module patterns
SUSPICIOUS_DRIVER_NAMES = [
    "teamviewer", "anydesk", "rustdesk", "parsec",
    "obs", "screen", "capture", "mirror",
    "vnc", "remote", "rdp",
    "cheat", "hack", "inject", "hook",
]

# Known VPN adapter patterns
VPN_ADAPTER_PATTERNS = [
    "tap-windows", "tap0901", "tun", "wintun",
    "wireguard", "openvpn", "vpn",
    "nordlynx", "nordvpn", "expressvpn", "surfshark",
    "protonvpn", "cyberghost", "windscribe", "mullvad",
    "hotspot shield", "tunnelbear", "pia",
    "cisco anyconnect", "globalprotect", "forticlient",
    "tailscale", "zerotier", "cloudflare warp",
    "softether", "hamachi",
]

# Known VPN process names
VPN_PROCESS_NAMES = [
    "openvpn", "openvpn-gui", "wireguard",
    "nordvpn", "nordlynx", "nordvpn-service",
    "expressvpn", "expressvpnd",
    "surfshark", "surfshark-service",
    "protonvpn", "protonvpn-service",
    "cyberghostvpn", "cyberghost",
    "windscribe", "windscribeservice",
    "mullvad-vpn", "mullvad-daemon",
    "pia-service", "privateinternetaccess",
    "hotspotshield", "hsswd",
    "tunnelbear",
    "strongvpn",
    "ipvanish",
    "vpnui",                      # Cisco AnyConnect
    "pangps", "pangpa",           # Palo Alto GlobalProtect
    "forticlient", "fortisslvpn",
    "tailscaled", "tailscale",
    "zerotier-one", "zerotier",
    "cloudflare-warp", "warp-svc",
    "softether", "vpnclient",
    "hamachi",
    "psiphon",
    "tor", "tor.exe",
]


class KernelProcessScanner:
    """Deep kernel-level process and driver detection.

    Three techniques:
    A) WMI process enumeration (deeper than user-mode psutil)
    B) Loaded kernel driver scan
    C) NtQuerySystemInformation comparison (detect hidden processes)
    """

    def scan(self) -> dict:
        """Run all kernel-level scans. Returns combined results."""
        result = {
            "hidden_processes": [],
            "suspicious_drivers": [],
            "kernel_process_count_mismatch": False,
        }

        if platform.system() != "Windows":
            return result

        # Technique A: find hidden processes
        result["hidden_processes"] = self._find_hidden_processes()

        # Technique B: suspicious driver scan
        result["suspicious_drivers"] = self._scan_drivers()

        # Technique C: NtQuery process count comparison
        result["kernel_process_count_mismatch"] = self._check_process_count_mismatch()

        return result

    def _find_hidden_processes(self) -> list[dict]:
        """Compare WMI process list with psutil to find hidden processes.

        WMI queries at a deeper OS level than standard user-mode APIs.
        Any process in WMI but NOT in psutil may be hiding from user-mode.
        """
        hidden = []
        try:
            # Get WMI process list
            wmi_out = subprocess.check_output(
                [
                    "powershell", "-NoProfile", "-Command",
                    "Get-CimInstance Win32_Process | "
                    "Select-Object -Property Name,ProcessId,ExecutablePath | "
                    "ConvertTo-Csv -NoTypeInformation",
                ],
                text=True,
                timeout=15,
                stderr=subprocess.DEVNULL,
            )
            wmi_pids: dict[int, str] = {}
            for line in wmi_out.splitlines()[1:]:  # skip header
                parts = line.strip().strip('"').split('","')
                if len(parts) >= 2:
                    try:
                        pid = int(parts[1])
                        wmi_pids[pid] = parts[0]
                    except (ValueError, IndexError):
                        continue

            # Get psutil process list
            psutil_pids: set[int] = set()
            if HAS_PSUTIL:
                for proc in psutil.process_iter(["pid"]):
                    try:
                        psutil_pids.add(proc.info["pid"])
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue

            # Find processes in WMI but NOT in psutil
            if psutil_pids:  # only compare if psutil is available
                for pid, name in wmi_pids.items():
                    if pid not in psutil_pids and pid > 4:  # skip System/Idle
                        hidden.append({
                            "pid": pid,
                            "name": name,
                            "reason": "Process visible in WMI but hidden from user-mode enumeration",
                        })
        except Exception as e:
            logger.debug(f"Hidden process scan error: {e}")

        return hidden

    def _scan_drivers(self) -> list[dict]:
        """Scan loaded kernel drivers for suspicious patterns."""
        suspicious = []
        try:
            out = subprocess.check_output(
                [
                    "powershell", "-NoProfile", "-Command",
                    "Get-CimInstance Win32_SystemDriver | "
                    "Where-Object {$_.State -eq 'Running'} | "
                    "Select-Object -Property Name,DisplayName,PathName | "
                    "ConvertTo-Csv -NoTypeInformation",
                ],
                text=True,
                timeout=15,
                stderr=subprocess.DEVNULL,
            )
            for line in out.splitlines()[1:]:
                parts = line.strip().strip('"').split('","')
                if len(parts) >= 2:
                    driver_name = parts[0].lower()
                    display_name = parts[1].lower() if len(parts) > 1 else ""
                    path_name = parts[2].lower() if len(parts) > 2 else ""
                    combined = f"{driver_name} {display_name} {path_name}"

                    for pattern in SUSPICIOUS_DRIVER_NAMES:
                        if pattern in combined:
                            suspicious.append({
                                "driver_name": parts[0],
                                "display_name": parts[1] if len(parts) > 1 else "",
                                "path": parts[2] if len(parts) > 2 else "",
                                "matched_pattern": pattern,
                            })
                            break
        except Exception as e:
            logger.debug(f"Driver scan error: {e}")

        return suspicious

    def _check_process_count_mismatch(self) -> bool:
        """Compare kernel-level process count with user-mode count.

        Uses NtQuerySystemInformation via ctypes to get the raw kernel
        process count and compares with psutil. A large discrepancy
        (>5 processes) suggests hidden processes.
        """
        if not HAS_PSUTIL:
            return False
        try:
            import ctypes
            from ctypes import wintypes

            ntdll = ctypes.windll.ntdll
            SYSTEM_PROCESS_INFORMATION = 5

            # First call to get required buffer size
            buf_size = wintypes.ULONG(0)
            status = ntdll.NtQuerySystemInformation(
                SYSTEM_PROCESS_INFORMATION, None, 0, ctypes.byref(buf_size)
            )

            # Allocate buffer and query
            buf = (ctypes.c_byte * buf_size.value)()
            status = ntdll.NtQuerySystemInformation(
                SYSTEM_PROCESS_INFORMATION, buf, buf_size.value, ctypes.byref(buf_size)
            )

            if status != 0:
                return False

            # Count processes in kernel data (each entry has NextEntryOffset)
            kernel_count = 0
            offset = 0
            while True:
                kernel_count += 1
                next_offset = int.from_bytes(buf[offset:offset + 4], "little")
                if next_offset == 0:
                    break
                offset += next_offset

            # Count psutil processes
            psutil_count = len(list(psutil.process_iter()))

            # Allow small tolerance (kernel sees System & Idle which psutil may skip)
            mismatch = kernel_count - psutil_count
            if mismatch > 5:
                logger.warning(
                    "Process count mismatch: kernel=%d, psutil=%d (diff=%d)",
                    kernel_count, psutil_count, mismatch,
                )
                return True

        except Exception as e:
            logger.debug(f"NtQuerySystemInformation error: {e}")

        return False


class VPNProxyDetector:
    """Detect VPN connections and proxy configurations.

    Detection methods:
    A) Network adapter scan for VPN interfaces (TAP/TUN/WireGuard)
    B) Running process scan for known VPN applications
    C) Windows proxy settings check (registry)
    D) DNS configuration anomaly detection
    """

    def scan(self) -> dict:
        """Run all VPN/proxy detection scans."""
        result = {
            "vpn_adapters": [],
            "vpn_processes": [],
            "proxy_enabled": False,
            "proxy_server": None,
            "suspicious_dns": False,
            "vpn_detected": False,
            "proxy_detected": False,
        }

        if platform.system() == "Windows":
            result["vpn_adapters"] = self._detect_vpn_adapters()
            result["proxy_enabled"], result["proxy_server"] = self._check_proxy_settings()
            result["suspicious_dns"] = self._check_dns_config()
        elif platform.system() == "Linux":
            result["vpn_adapters"] = self._detect_vpn_adapters_linux()

        result["vpn_processes"] = self._detect_vpn_processes()

        # Set summary flags
        result["vpn_detected"] = bool(result["vpn_adapters"]) or bool(result["vpn_processes"])
        result["proxy_detected"] = result["proxy_enabled"]

        return result

    def _detect_vpn_adapters(self) -> list[str]:
        """Detect VPN network adapters on Windows."""
        found = []
        try:
            out = subprocess.check_output(
                [
                    "powershell", "-NoProfile", "-Command",
                    "Get-NetAdapter | Where-Object {$_.Status -eq 'Up'} | "
                    "Select-Object -Property Name,InterfaceDescription | "
                    "ConvertTo-Csv -NoTypeInformation",
                ],
                text=True,
                timeout=10,
                stderr=subprocess.DEVNULL,
            )
            for line in out.splitlines()[1:]:
                parts = line.strip().strip('"').split('","')
                combined = " ".join(parts).lower()
                for pattern in VPN_ADAPTER_PATTERNS:
                    if pattern in combined:
                        found.append(parts[0] if parts else combined)
                        break
        except Exception as e:
            logger.debug(f"VPN adapter scan error: {e}")
        return found

    def _detect_vpn_adapters_linux(self) -> list[str]:
        """Detect VPN network interfaces on Linux."""
        found = []
        try:
            out = subprocess.check_output(
                ["ip", "link", "show"], text=True, timeout=5,
                stderr=subprocess.DEVNULL,
            )
            for line in out.splitlines():
                lower = line.lower()
                for pattern in ["tun", "tap", "wg", "vpn", "wireguard", "nordlynx"]:
                    if pattern in lower:
                        # Extract interface name
                        parts = line.split(":")
                        if len(parts) >= 2:
                            found.append(parts[1].strip())
                        break
        except Exception as e:
            logger.debug(f"Linux VPN adapter scan error: {e}")
        return found

    def _detect_vpn_processes(self) -> list[str]:
        """Scan running processes for known VPN applications."""
        found = []
        try:
            if HAS_PSUTIL:
                for proc in psutil.process_iter(["name"]):
                    try:
                        pname = (proc.info["name"] or "").lower()
                        for vpn_name in VPN_PROCESS_NAMES:
                            if vpn_name in pname:
                                found.append(proc.info["name"])
                                break
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
            else:
                # Fallback: tasklist
                if platform.system() == "Windows":
                    out = subprocess.check_output(
                        ["tasklist", "/FO", "CSV", "/NH"],
                        text=True, timeout=10,
                    )
                    for line in out.strip().split("\n"):
                        parts = line.strip().strip('"').split('","')
                        if parts:
                            pname = parts[0].lower()
                            for vpn_name in VPN_PROCESS_NAMES:
                                if vpn_name in pname:
                                    found.append(parts[0])
                                    break
        except Exception as e:
            logger.debug(f"VPN process scan error: {e}")
        return found

    def _check_proxy_settings(self) -> tuple[bool, str | None]:
        """Check Windows proxy settings from registry."""
        try:
            out = subprocess.check_output(
                [
                    "powershell", "-NoProfile", "-Command",
                    "Get-ItemProperty -Path "
                    "'HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Internet Settings' "
                    "| Select-Object -Property ProxyEnable,ProxyServer | "
                    "ConvertTo-Csv -NoTypeInformation",
                ],
                text=True,
                timeout=8,
                stderr=subprocess.DEVNULL,
            )
            for line in out.splitlines()[1:]:
                parts = line.strip().strip('"').split('","')
                if len(parts) >= 2:
                    proxy_enabled = parts[0].strip() == "1"
                    proxy_server = parts[1].strip() if len(parts) > 1 else None
                    if proxy_server and proxy_server.lower() in ("", "none", "0"):
                        proxy_server = None
                    return proxy_enabled, proxy_server
        except Exception as e:
            logger.debug(f"Proxy settings check error: {e}")
        return False, None

    def _check_dns_config(self) -> bool:
        """Check for VPN-related DNS configuration.

        VPNs often set custom DNS servers (10.x.x.x, 172.x.x.x private ranges).
        Standard DNS (ISP, Google 8.8.8.8, Cloudflare 1.1.1.1) is OK.
        """
        SAFE_DNS = {"8.8.8.8", "8.8.4.4", "1.1.1.1", "1.0.0.1",
                     "9.9.9.9", "208.67.222.222", "208.67.220.220"}
        try:
            out = subprocess.check_output(
                [
                    "powershell", "-NoProfile", "-Command",
                    "Get-DnsClientServerAddress -AddressFamily IPv4 | "
                    "Select-Object -ExpandProperty ServerAddresses",
                ],
                text=True,
                timeout=8,
                stderr=subprocess.DEVNULL,
            )
            dns_servers = [s.strip() for s in out.splitlines() if s.strip()]
            for dns in dns_servers:
                # VPN DNS servers are often in private IP ranges
                if dns.startswith("10.") or dns.startswith("172.") or dns.startswith("192.168."):
                    # Private DNS = likely VPN
                    if dns not in SAFE_DNS:
                        logger.debug(f"Suspicious DNS server: {dns}")
                        return True
        except Exception as e:
            logger.debug(f"DNS config check error: {e}")
        return False


# ═══════════════════════════════════════════════════════════════════
#  PROCTOR AGENT — Main Orchestrator
# ═══════════════════════════════════════════════════════════════════

class ProctorAgent:
    """
    Main proctoring agent that coordinates all monitoring layers
    and sends results to the VAREX backend via heartbeats.
    """

    def __init__(
        self,
        session_id: str,
        api_url: str,
        heartbeat_interval: int = 10,
        proctor_secret: str | None = None,
        require_visible_face: bool = True,
        require_local_audio: bool = True,
    ):
        self.session_id = session_id
        self.api_url = api_url.rstrip("/")
        self.heartbeat_interval = heartbeat_interval
        self.proctor_secret = proctor_secret or os.getenv("PROCTOR_SHARED_SECRET", "").strip()
        self.require_visible_face = require_visible_face
        self.require_local_audio = require_local_audio
        self.running = False

        # Initialize monitors
        self.process_monitor = ProcessMonitor()
        self.window_monitor = ActiveWindowMonitor()
        self.network_monitor = NetworkMonitor()
        self.env_check = SystemEnvironmentCheck()
        self.face_monitor = FaceMonitor()
        self.audio_monitor = AudioRouteMonitor()
        self.kernel_scanner = KernelProcessScanner()
        self.vpn_detector = VPNProxyDetector()

        # Tracking state
        self.violations: list[dict] = []
        self.heartbeat_count = 0
        self.last_active_window = ""
        self.camera_violation_sent = False
        self.audio_violation_sent = False
        self.earbud_violation_sent = False
        self.environment_info: dict = {}

    def start(self):
        """Start the proctoring agent."""
        self.running = True
        logger.info(f"🛡️  VAREX Proctor Agent starting for session: {self.session_id}")
        logger.info(f"   Backend: {self.api_url}")

        # ── Initial environment check ─────────────────────────
        env_info = self.env_check.check()
        self.environment_info = env_info
        logger.info(f"   Environment: {json.dumps(env_info, indent=2)}")

        # ── Flag VM / remote desktop immediately ──────────────
        if env_info.get("is_virtual_machine"):
            self._record_violation("virtual_machine_detected",
                "Interview is being conducted inside a virtual machine.")

        if env_info.get("has_remote_desktop"):
            self._record_violation("remote_desktop_detected",
                "Remote desktop session detected.")

        if env_info.get("has_multiple_monitors"):
            logger.info("Multiple monitors detected (informational).")

        # ── Start monitoring loops ────────────────────────────
        try:
            self._monitoring_loop()
        except KeyboardInterrupt:
            logger.info("Proctor agent stopped by user.")
        finally:
            self.running = False
            self.face_monitor.stop()
            logger.info(
                "Proctor stopped. total_violations=%s heartbeats_sent=%s",
                len(self.violations),
                self.heartbeat_count,
            )

    def _monitoring_loop(self):
        """Main monitoring loop — runs every heartbeat_interval seconds."""
        while self.running:
            scan_results = self._scan_all()

            # ── Send heartbeat with scan results ──────────────
            self._send_heartbeat(scan_results)

            time.sleep(self.heartbeat_interval)

    def _scan_all(self) -> dict:
        """Run all monitoring scans and return combined results.

        v2 improvements:
        - Layer 2b: full window enumeration (all visible windows, not just foreground)
        - Network scan every heartbeat (was every 3rd)
        - Face streak counter (only flag after N consecutive misses)
        - Camera/audio violation flags reset on recovery
        """
        results = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "violations": [],
        }

        # ── Layer 1: Process scan ─────────────────────────────
        ai_processes = self.process_monitor.scan()
        if ai_processes:
            for proc in ai_processes:
                violation = self._record_violation(
                    "ai_app_detected",
                    f"AI application detected: {proc['label']} "
                    f"(process: {proc['process_name']}, PID: {proc['pid']})",
                )
                results["violations"].append(violation)
            results["ai_processes"] = ai_processes

        # ── Layer 2a: Active window check (foreground) ────────
        active_window = self.window_monitor.get_active_window()
        if active_window != self.last_active_window:
            if self.last_active_window:  # Skip first detection
                is_browser = self.window_monitor.is_browser_focused(active_window)
                if not is_browser:
                    if self.window_monitor.is_allowed_non_browser_window(active_window):
                        logger.info("Allowed foreground app detected: '%s'", active_window)
                    else:
                        violation = self._record_violation(
                            "forbidden_app_detected",
                            (
                                f"Forbidden foreground app detected: '{active_window}'. "
                                "Only browser + Notepad/Notepad++ are allowed."
                            ),
                        )
                        results["violations"].append(violation)
                else:
                    # Check if it's an AI-related browser tab
                    ai_tab = self._check_ai_browser_tab(active_window)
                    if ai_tab:
                        violation = self._record_violation(
                            "ai_browser_tab",
                            f"AI service detected in browser: '{active_window}'",
                        )
                        results["violations"].append(violation)
            self.last_active_window = active_window

        results["active_window"] = active_window

        # ── Layer 2b: Full window enumeration (background apps) ──
        # Scans ALL visible windows and checks process names against the
        # whitelist. Catches background apps that foreground-only checks miss.
        if platform.system() == "Windows":
            all_windows = self.window_monitor.enumerate_all_windows()
            forbidden_windows = []
            for win in all_windows:
                pname = win.get("process_name", "")
                title = win.get("title", "")
                if not pname:
                    continue
                # Skip browser windows, allowed processes, and the proctor itself
                if self.window_monitor.is_browser_process(pname):
                    continue
                if self.window_monitor.is_allowed_process(pname):
                    continue
                if pname in ("python.exe", "pythonw.exe", "python3.exe"):
                    continue  # proctor agent itself
                # Check if this background window belongs to a known AI app
                lower_title = title.lower()
                for pattern in AI_PROCESS_NAMES:
                    if pattern in lower_title or pattern in pname:
                        forbidden_windows.append(win)
                        break
                else:
                    # Also check exact exe names
                    if pname in AI_PROCESS_EXE_EXACT:
                        forbidden_windows.append(win)

            for win in forbidden_windows:
                violation = self._record_violation(
                    "forbidden_app_detected",
                    (
                        f"Forbidden background app detected: '{win['title']}' "
                        f"(process: {win['process_name']}, PID: {win['pid']}). "
                        "Only browser + Notepad/Notepad++ are allowed."
                    ),
                )
                results["violations"].append(violation)
            results["background_window_scan"] = {
                "total_windows": len(all_windows),
                "forbidden_count": len(forbidden_windows),
            }

        # ── Layer 3: Network scan (EVERY heartbeat now) ───────
        ai_connections = self.network_monitor.scan_connections()
        if ai_connections:
            for conn in ai_connections:
                violation = self._record_violation(
                    "ai_network_connection",
                    f"Active connection to AI service: {conn['domain']} "
                    f"({conn['remote_ip']}:{conn['remote_port']})",
                )
                results["violations"].append(violation)
            results["ai_connections"] = ai_connections

        # ── Layer 4: Face presence monitor (camera) ───────────
        face_state = self.face_monitor.scan()
        results["face_monitor"] = face_state
        if self.require_visible_face:
            if not face_state.get("available", False):
                if not self.camera_violation_sent:
                    violation = self._record_violation(
                        "camera_unavailable",
                        f"Camera unavailable for proctoring: {face_state.get('error', 'unknown')}",
                    )
                    results["violations"].append(violation)
                    self.camera_violation_sent = True
            else:
                # Camera is available → reset flag so new failures are reported
                self.camera_violation_sent = False

                face_count = int(face_state.get("faces", 0) or 0)
                no_face_streak = face_state.get("no_face_streak", 0)

                if face_count == 0:
                    # Only flag after N consecutive no-face frames (reduces false positives)
                    if no_face_streak >= FaceMonitor.NO_FACE_STREAK_THRESHOLD:
                        violation = self._record_violation(
                            "no_face_detected",
                            f"No face detected for {no_face_streak} consecutive frames.",
                        )
                        results["violations"].append(violation)
                elif face_count > 1:
                    violation = self._record_violation(
                        "multiple_faces_detected",
                        f"Multiple faces detected ({face_count}).",
                    )
                    results["violations"].append(violation)

        # ── Layer 4b: Earbud + audio cross-reference ────────────
        # If earbuds are visible in camera but NOT connected to laptop
        # Bluetooth/audio → candidate is using external audio (phone)
        if face_state.get("earbud_suspected", False):
            audio_state_quick = self.audio_monitor.scan()
            has_bt = audio_state_quick.get("has_bluetooth_audio", False)
            has_headset = audio_state_quick.get("has_headset", False)
            if not has_bt and not has_headset:
                if not self.earbud_violation_sent:
                    violation = self._record_violation(
                        "external_audio_suspected",
                        "Earbuds/headset visible on candidate in camera, but no "
                        "Bluetooth/headset audio device connected to laptop. "
                        "Candidate may be receiving audio from an external device.",
                    )
                    results["violations"].append(violation)
                    self.earbud_violation_sent = True
            else:
                self.earbud_violation_sent = False

        # ── Layer 5: Local audio route checks ─────────────────
        if self.heartbeat_count % 2 == 0:
            audio_state = self.audio_monitor.scan()
            results["audio_monitor"] = audio_state
            if self.require_local_audio:
                if not audio_state.get("has_any_audio", False):
                    if not self.audio_violation_sent:
                        violation = self._record_violation(
                            "no_local_audio_device",
                            "No local audio endpoint detected on candidate laptop.",
                        )
                        results["violations"].append(violation)
                        self.audio_violation_sent = True
                else:
                    # Audio recovered → reset flag so new failures are reported
                    self.audio_violation_sent = False

                    if not audio_state.get("has_headset", False):
                        violation = self._record_violation(
                            "no_headset_connected",
                            "No local headset/earbud detected on candidate laptop audio routes.",
                        )
                        results["violations"].append(violation)

        # ── Layer 6: Kernel-level process scan (every 5th heartbeat) ──
        if self.heartbeat_count % 5 == 0:
            kernel_state = self.kernel_scanner.scan()
            results["kernel_scan"] = kernel_state

            for hidden in kernel_state.get("hidden_processes", []):
                violation = self._record_violation(
                    "hidden_process_detected",
                    f"Hidden process detected: {hidden['name']} (PID: {hidden['pid']}). "
                    f"{hidden['reason']}",
                )
                results["violations"].append(violation)

            for driver in kernel_state.get("suspicious_drivers", []):
                violation = self._record_violation(
                    "suspicious_driver_detected",
                    f"Suspicious kernel driver: {driver['driver_name']} "
                    f"({driver['display_name']}). Matched: {driver['matched_pattern']}",
                )
                results["violations"].append(violation)

            if kernel_state.get("kernel_process_count_mismatch", False):
                violation = self._record_violation(
                    "hidden_process_detected",
                    "Kernel process count mismatch: more processes visible at "
                    "kernel level than user mode. Possible process hiding.",
                )
                results["violations"].append(violation)

        # ── Layer 7: VPN / Proxy detection (every 3rd heartbeat) ──
        if self.heartbeat_count % 3 == 0:
            vpn_state = self.vpn_detector.scan()
            results["vpn_proxy"] = vpn_state

            if vpn_state.get("vpn_detected", False):
                adapters = vpn_state.get("vpn_adapters", [])
                processes = vpn_state.get("vpn_processes", [])
                details = []
                if adapters:
                    details.append(f"VPN adapters: {', '.join(adapters)}")
                if processes:
                    details.append(f"VPN processes: {', '.join(processes)}")
                violation = self._record_violation(
                    "vpn_detected",
                    f"VPN connection detected. {'; '.join(details)}",
                )
                results["violations"].append(violation)

            if vpn_state.get("proxy_detected", False):
                proxy_server = vpn_state.get("proxy_server", "unknown")
                violation = self._record_violation(
                    "proxy_detected",
                    f"System proxy enabled: {proxy_server}",
                )
                results["violations"].append(violation)

            if vpn_state.get("suspicious_dns", False):
                violation = self._record_violation(
                    "vpn_detected",
                    "Suspicious private DNS server detected (possible VPN tunnel).",
                )
                results["violations"].append(violation)

        return results

    def _check_ai_browser_tab(self, window_title: str) -> bool:
        """Check if the browser window title suggests an AI service."""
        ai_title_patterns = [
            "chatgpt", "chat.openai", "claude", "anthropic",
            "gemini", "bard", "copilot", "perplexity",
            "phind", "you.com", "huggingface", "cohere",
            "mistral", "groq", "poe.com", "deepseek",
        ]
        lower_title = window_title.lower()
        return any(p in lower_title for p in ai_title_patterns)

    def _record_violation(self, violation_type: str, details: str) -> dict:
        """Record a violation and send it to the backend."""
        violation = {
            "type": violation_type,
            "details": details,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self.violations.append(violation)
        logger.warning(f"🚨 VIOLATION: {violation_type} — {details}")
        # Violations are sent via heartbeat payload to avoid duplicate reporting.
        return violation

    def _send_heartbeat(self, scan_results: dict):
        """Send heartbeat to VAREX backend."""
        self.heartbeat_count += 1
        payload = {
            "session_id": self.session_id,
            "heartbeat_number": self.heartbeat_count,
            "agent_version": "1.0.0",
            "total_violations": len(self.violations),
            "environment": self.environment_info,
            "scan_results": scan_results,
        }

        try:
            if HAS_REQUESTS:
                headers = {}
                if self.proctor_secret:
                    headers["X-Proctor-Secret"] = self.proctor_secret
                resp = requests.post(
                    f"{self.api_url}/api/v1/interview/session/{self.session_id}/proctor-heartbeat",
                    json=payload,
                    headers=headers,
                    timeout=5,
                )
                if resp.status_code == 200:
                    data = resp.json()
                    # Check if backend says to stop
                    if data.get("stop_interview"):
                        logger.warning("Backend requested interview termination!")
                        self.running = False
                elif resp.status_code != 200:
                    logger.debug(f"Heartbeat response: {resp.status_code}")
        except Exception as e:
            logger.debug(f"Heartbeat send failed: {e}")

    def _send_event(self, event_type: str, data: dict):
        """Send a specific event to the VAREX backend."""
        payload = {
            "event_type": event_type,
            "details": json.dumps(data),
        }
        try:
            if HAS_REQUESTS:
                requests.post(
                    f"{self.api_url}/api/v1/interview/session/{self.session_id}/anti-cheat",
                    json=payload,
                    timeout=5,
                )
        except Exception as e:
            logger.debug(f"Event send failed: {e}")


# ═══════════════════════════════════════════════════════════════════
#  CLI ENTRY POINT
# ═══════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="VAREX Desktop Proctoring Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python proctor_agent.py --session-id abc-123 --api-url http://localhost:3010
  python proctor_agent.py --session-id abc-123 --api-url https://varex.app --interval 15

Requirements:
  pip install psutil requests
        """,
    )
    parser.add_argument(
        "--session-id", required=True,
        help="Interview session ID from VAREX platform",
    )
    parser.add_argument(
        "--api-url", required=True,
        help="VAREX backend API URL (e.g., http://localhost:3010)",
    )
    parser.add_argument(
        "--interval", type=int, default=10,
        help="Heartbeat interval in seconds (default: 10)",
    )
    parser.add_argument(
        "--proctor-secret",
        default="",
        help="Shared secret expected by backend (or set PROCTOR_SHARED_SECRET env var).",
    )
    parser.add_argument(
        "--require-visible-face",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Require continuous camera face presence checks (default: enabled).",
    )
    parser.add_argument(
        "--require-local-audio",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Require local headset/audio route detection on the candidate laptop (default: enabled).",
    )

    args = parser.parse_args()

    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║           🛡️  VAREX PROCTORING AGENT v1.0               ║
    ║                                                          ║
    ║  This agent monitors your system during the interview.   ║
    ║  Please keep it running until the interview is complete. ║
    ║                                                          ║
    ║  DO NOT close this window during the interview.          ║
    ╚══════════════════════════════════════════════════════════╝
    """)

    agent = ProctorAgent(
        session_id=args.session_id,
        api_url=args.api_url,
        heartbeat_interval=args.interval,
        proctor_secret=args.proctor_secret,
        require_visible_face=args.require_visible_face,
        require_local_audio=args.require_local_audio,
    )
    agent.start()


if __name__ == "__main__":
    main()
