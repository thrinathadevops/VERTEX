from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status


class LoginThrottleState:
    def __init__(self) -> None:
        self.failures = 0
        self.locked_until: datetime | None = None


_login_failures: dict[str, LoginThrottleState] = {}
_request_windows: dict[str, deque[datetime]] = defaultdict(deque)

_ACTION_LIMITS = {
    "login": (10, timedelta(minutes=5)),
    "register": (5, timedelta(hours=1)),
    "forgot-password": (5, timedelta(hours=1)),
    "reset-password": (10, timedelta(hours=1)),
}


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _rate_key(action: str, ip_address: str, identifier: str | None = None) -> str:
    return f"{action}:{ip_address}:{identifier or '-'}"


def enforce_rate_limit(action: str, ip_address: str, identifier: str | None = None) -> None:
    now = _utcnow()
    max_attempts, window = _ACTION_LIMITS[action]
    key = _rate_key(action, ip_address, identifier)
    bucket = _request_windows[key]

    while bucket and now - bucket[0] > window:
        bucket.popleft()

    if len(bucket) >= max_attempts:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests. Please try again later.",
        )

    bucket.append(now)


def get_progressive_delay_seconds(ip_address: str, email: str) -> float:
    key = _rate_key("login", ip_address, email)
    state = _login_failures.get(key)
    if not state:
        return 0.0

    now = _utcnow()
    if state.locked_until and state.locked_until > now:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests. Please try again later.",
        )

    if state.failures < 3:
        return 0.0

    return float(min(2 ** (state.failures - 3), 8))


def record_login_failure(ip_address: str, email: str) -> None:
    key = _rate_key("login", ip_address, email)
    state = _login_failures.setdefault(key, LoginThrottleState())
    state.failures += 1

    if state.failures >= 5:
        state.locked_until = _utcnow() + timedelta(minutes=15)


def clear_login_failures(ip_address: str, email: str) -> None:
    key = _rate_key("login", ip_address, email)
    _login_failures.pop(key, None)
