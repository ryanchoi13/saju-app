"""Small in-process cache for the fixed Gyeongju clothing forecast."""

from copy import deepcopy
from threading import Lock
import time

from fashion_v2.weather_outfit import fetch_gyeongju_weather


class WeatherOutfitCache:
    def __init__(self, ttl_seconds=1800, retry_seconds=300):
        self.ttl_seconds = ttl_seconds
        self.retry_seconds = retry_seconds
        self._lock = Lock()
        self._value = None
        self._fetched_at = 0.0
        self._retry_after = 0.0

    def get(self, fetcher=fetch_gyeongju_weather, now=None):
        timestamp = time.monotonic() if now is None else float(now)
        with self._lock:
            fresh = self._value is not None and timestamp - self._fetched_at < self.ttl_seconds
            if fresh or timestamp < self._retry_after:
                return deepcopy(self._value)
            try:
                value = fetcher()
            except Exception:
                self._retry_after = timestamp + self.retry_seconds
                return deepcopy(self._value)
            self._value = deepcopy(value)
            self._fetched_at = timestamp
            self._retry_after = 0.0
            return deepcopy(self._value)

    def peek(self):
        with self._lock:
            return deepcopy(self._value)

    def clear(self):
        with self._lock:
            self._value = None
            self._fetched_at = 0.0
            self._retry_after = 0.0


gyeongju_weather_cache = WeatherOutfitCache()


def weather_api_payload(profile):
    if profile is None:
        return {
            "available": False,
            "location": "경주",
            "location_mode": "fixed_gyeongju",
            "guidance": "",
        }
    return {"available": True, **profile}
