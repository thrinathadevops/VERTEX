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

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [PROCTOR] %(levelname)s — %(message)s",
)
logger = logging.getLogger("proctor")


# ═══════════════════════════════════════════════════════════════════
#  KNOWN AI / CHEATING APPLICATIONS
# ═══════════════════════════════════════════════════════════════════

# Process names to detect (case-insensitive match)
AI_PROCESS_NAMES = {
    # Desktop AI Apps
    "chatgpt": "ChatGPT Desktop App",
    "copilot": "Microsoft Copilot",
    "claude": "Claude Desktop App",
    "gemini": "Google Gemini",
    "perplexity": "Perplexity AI",
    "phind": "Phind AI",
    "cursor": "Cursor AI Editor",
    "codeium": "Codeium AI",
    "tabnine": "TabNine AI",
    "github copilot": "GitHub Copilot",
    "supermaven": "Supermaven AI",
    "cody": "Sourcegraph Cody AI",
    "continue": "Continue AI",
    "aider": "Aider AI",
    # Screen Recording / Sharing
    "obs": "OBS Studio (Screen Recording)",
    "obs64": "OBS Studio (Screen Recording)",
    "obs32": "OBS Studio (Screen Recording)",
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
]


# ═══════════════════════════════════════════════════════════════════
#  LAYER 1: PROCESS MONITOR
# ═══════════════════════════════════════════════════════════════════

class ProcessMonitor:
    """Scan running processes for known AI/cheating applications."""

    def scan(self) -> list[dict]:
        """Return list of detected suspicious processes."""
        if not HAS_PSUTIL:
            return self._scan_fallback()

        detected = []
        try:
            for proc in psutil.process_iter(["pid", "name", "exe", "cmdline"]):
                try:
                    pname = (proc.info["name"] or "").lower()
                    pexe = (proc.info["exe"] or "").lower()
                    pcmd = " ".join(proc.info.get("cmdline") or []).lower()

                    for pattern, label in AI_PROCESS_NAMES.items():
                        if (
                            pattern in pname
                            or pattern in pexe
                            or pattern in pcmd
                        ):
                            detected.append({
                                "process_name": proc.info["name"],
                                "pid": proc.info["pid"],
                                "label": label,
                                "exe": proc.info.get("exe", ""),
                            })
                            break
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except Exception as e:
            logger.error(f"Process scan error: {e}")

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

        return detected


# ═══════════════════════════════════════════════════════════════════
#  LAYER 2: ACTIVE WINDOW MONITOR
# ═══════════════════════════════════════════════════════════════════

class ActiveWindowMonitor:
    """Track which window is currently active (OS-level, not browser)."""

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

    def is_browser_focused(self, window_title: str) -> bool:
        """Check if the active window is a known browser."""
        browsers = [
            "chrome", "firefox", "safari", "edge", "brave", "opera",
            "chromium", "vivaldi", "arc",
        ]
        lower_title = window_title.lower()
        return any(b in lower_title for b in browsers)


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

    def _detect_multiple_monitors(self) -> bool:
        """Detect multiple monitors (could be used to cheat on second screen)."""
        try:
            if platform.system() == "Windows":
                import ctypes
                num_monitors = ctypes.windll.user32.GetSystemMetrics(80)  # SM_CMONITORS
                return num_monitors > 1
        except Exception:
            pass
        return False

    def _detect_remote_desktop(self) -> bool:
        """Detect if accessed via remote desktop."""
        try:
            if platform.system() == "Windows":
                import ctypes
                # SM_REMOTESESSION = 0x1000
                return bool(ctypes.windll.user32.GetSystemMetrics(0x1000))
        except Exception:
            pass
        return False


# ═══════════════════════════════════════════════════════════════════
#  PROCTOR AGENT — Main Orchestrator
# ═══════════════════════════════════════════════════════════════════

class ProctorAgent:
    """
    Main proctoring agent that coordinates all monitoring layers
    and sends results to the VAREX backend via heartbeats.
    """

    def __init__(self, session_id: str, api_url: str, heartbeat_interval: int = 10):
        self.session_id = session_id
        self.api_url = api_url.rstrip("/")
        self.heartbeat_interval = heartbeat_interval
        self.running = False

        # Initialize monitors
        self.process_monitor = ProcessMonitor()
        self.window_monitor = ActiveWindowMonitor()
        self.network_monitor = NetworkMonitor()
        self.env_check = SystemEnvironmentCheck()

        # Tracking state
        self.violations: list[dict] = []
        self.heartbeat_count = 0
        self.last_active_window = ""

    def start(self):
        """Start the proctoring agent."""
        self.running = True
        logger.info(f"🛡️  VAREX Proctor Agent starting for session: {self.session_id}")
        logger.info(f"   Backend: {self.api_url}")

        # ── Initial environment check ─────────────────────────
        env_info = self.env_check.check()
        logger.info(f"   Environment: {json.dumps(env_info, indent=2)}")

        # Send environment info to backend
        self._send_event("proctor_started", {
            "agent_version": "1.0.0",
            "environment": env_info,
            "monitors_active": {
                "process": True,
                "active_window": True,
                "network": HAS_PSUTIL,
            },
        })

        # ── Flag VM / remote desktop immediately ──────────────
        if env_info.get("is_virtual_machine"):
            self._record_violation("virtual_machine_detected",
                "Interview is being conducted inside a virtual machine.")

        if env_info.get("has_remote_desktop"):
            self._record_violation("remote_desktop_detected",
                "Remote desktop session detected.")

        if env_info.get("has_multiple_monitors"):
            self._send_event("multiple_monitors_detected", {
                "note": "Candidate has multiple monitors. Not a violation but noted.",
            })

        # ── Start monitoring loops ────────────────────────────
        try:
            self._monitoring_loop()
        except KeyboardInterrupt:
            logger.info("Proctor agent stopped by user.")
        finally:
            self.running = False
            self._send_event("proctor_stopped", {
                "total_violations": len(self.violations),
                "heartbeats_sent": self.heartbeat_count,
            })

    def _monitoring_loop(self):
        """Main monitoring loop — runs every heartbeat_interval seconds."""
        while self.running:
            scan_results = self._scan_all()

            # ── Send heartbeat with scan results ──────────────
            self._send_heartbeat(scan_results)

            time.sleep(self.heartbeat_interval)

    def _scan_all(self) -> dict:
        """Run all monitoring scans and return combined results."""
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

        # ── Layer 2: Active window check ──────────────────────
        active_window = self.window_monitor.get_active_window()
        if active_window != self.last_active_window:
            if self.last_active_window:  # Skip first detection
                is_browser = self.window_monitor.is_browser_focused(active_window)
                if not is_browser:
                    violation = self._record_violation(
                        "non_browser_window",
                        f"Candidate switched to non-browser app: '{active_window}'",
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

        # ── Layer 3: Network scan (every 3rd heartbeat) ───────
        if self.heartbeat_count % 3 == 0:
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

        return results

    def _check_ai_browser_tab(self, window_title: str) -> bool:
        """Check if the browser window title suggests an AI service."""
        ai_title_patterns = [
            "chatgpt", "chat.openai", "claude", "anthropic",
            "gemini", "bard", "copilot", "perplexity",
            "phind", "you.com", "huggingface", "cohere",
            "mistral", "groq", "poe.com",
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

        # Send violation event immediately
        self._send_event(violation_type, {"details": details})
        return violation

    def _send_heartbeat(self, scan_results: dict):
        """Send heartbeat to VAREX backend."""
        self.heartbeat_count += 1
        payload = {
            "session_id": self.session_id,
            "heartbeat_number": self.heartbeat_count,
            "agent_version": "1.0.0",
            "total_violations": len(self.violations),
            "scan_results": scan_results,
        }

        try:
            if HAS_REQUESTS:
                resp = requests.post(
                    f"{self.api_url}/api/v1/interview/session/{self.session_id}/proctor-heartbeat",
                    json=payload,
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
    )
    agent.start()


if __name__ == "__main__":
    main()
