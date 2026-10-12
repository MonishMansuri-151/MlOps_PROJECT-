"""
Small in-memory sliding-window rate limiter.

Used for: login attempts (stop password guessing) and chat messages
(stop LLM cost abuse). In-memory = per server process; if you run several
workers, move this to Redis.
"""
import threading
import time
from collections import defaultdict, deque


class RateLimiter:
    def __init__(self, max_events: int, window_seconds: int):
        self.max_events = max_events
        self.window = window_seconds
        self._events: dict[str, deque] = defaultdict(deque)
        self._lock = threading.Lock()

    def _prune(self, key: str, now: float) -> deque:
        events = self._events[key]
        while events and now - events[0] > self.window:
            events.popleft()
        return events

    def is_blocked(self, key: str) -> bool:
        """True when `key` already used up its allowance."""
        now = time.monotonic()
        with self._lock:
            events = self._prune(key, now)
            if not events:
                self._events.pop(key, None)
            return len(events) >= self.max_events

    def hit(self, key: str) -> None:
        """Record one event for `key`."""
        now = time.monotonic()
        with self._lock:
            self._prune(key, now).append(now)

    def check_and_hit(self, key: str) -> bool:
        """Record an event; return False if the limit is exceeded."""
        now = time.monotonic()
        with self._lock:
            events = self._prune(key, now)
            if len(events) >= self.max_events:
                return False
            events.append(now)
            return True

    def reset(self, key: str) -> None:
        with self._lock:
            self._events.pop(key, None)

    def retry_after(self, key: str) -> int:
        now = time.monotonic()
        with self._lock:
            events = self._prune(key, now)
            if not events:
                return 0
            return max(1, int(self.window - (now - events[0])))
