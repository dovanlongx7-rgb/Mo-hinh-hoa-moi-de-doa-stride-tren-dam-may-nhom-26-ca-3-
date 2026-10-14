"""Giới hạn trượt trong RAM; có khóa thread; không phải giải pháp phân tán."""
from collections import defaultdict, deque
from threading import Lock
import math
import time
from fastapi import HTTPException

class RateLimiter:
    def __init__(self):
        self.windows = defaultdict(deque)
        self.lock = Lock()

    def check(self, bucket, limit, seconds):
        now = time.monotonic()
        with self.lock:
            # Dọn các bucket cũ để tránh lưu vô hạn sau khi hết cửa sổ.
            for key in list(self.windows):
                if not self.windows[key] or now-self.windows[key][-1] >= seconds:
                    del self.windows[key]
            events = self.windows[bucket]
            while events and now-events[0] >= seconds:
                events.popleft()
            if len(events) >= limit:
                retry = max(1, math.ceil(seconds-(now-events[0])))
                raise HTTPException(429, "RATE_LIMITED", headers={"Retry-After": str(retry)})
            events.append(now)
