"""In-memory conversation context (current item, multi-step flow state)."""
import threading
import time
from config import SESSION_TTL_SECONDS


class ContextManager:
    def __init__(self):
        self._data = {}
        self._lock = threading.Lock()

    def get(self, sid: str) -> dict:
        with self._lock:
            self._purge()
            ctx = self._data.setdefault(sid, {"item": None, "state": None, "data": {}, "last_intent": None,
                                                "turns": 0, "touched": time.time()})
            ctx["touched"] = time.time()
            return ctx

    def reset_flow(self, sid: str):
        ctx = self.get(sid)
        ctx["state"], ctx["data"] = None, {}

    def _purge(self):
        now = time.time()
        for k in [k for k, v in self._data.items() if now - v["touched"] > SESSION_TTL_SECONDS]:
            del self._data[k]
