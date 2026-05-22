"""Simple LLM response cache to avoid repeated API calls."""
import hashlib
import json
import os
import time
from typing import Dict, Optional


class LLMCache:
    """Caches LLM responses by prompt hash. Supports TTL-based expiry."""

    def __init__(self, cache_dir: str = ".llm_cache", ttl_seconds: int = 3600):
        self.cache_dir = cache_dir
        self.ttl_seconds = ttl_seconds
        self._memory_cache: Dict[str, dict] = {}
        os.makedirs(cache_dir, exist_ok=True)

    def _hash_key(self, prompt: str) -> str:
        return hashlib.sha256(prompt.encode()).hexdigest()[:16]

    def _file_path(self, key: str) -> str:
        return os.path.join(self.cache_dir, f"{key}.json")

    def get(self, prompt: str) -> Optional[str]:
        """Get cached response for a prompt. Returns None if miss or expired."""
        key = self._hash_key(prompt)

        # Memory cache first
        if key in self._memory_cache:
            entry = self._memory_cache[key]
            if time.time() - entry["timestamp"] < self.ttl_seconds:
                return entry["response"]
            else:
                del self._memory_cache[key]

        # Disk cache
        path = self._file_path(key)
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                entry = json.load(f)
            if time.time() - entry["timestamp"] < self.ttl_seconds:
                self._memory_cache[key] = entry
                return entry["response"]
            else:
                os.remove(path)

        return None

    def set(self, prompt: str, response: str) -> None:
        """Cache a response for a prompt."""
        key = self._hash_key(prompt)
        entry = {
            "prompt": prompt[:200],
            "response": response,
            "timestamp": time.time(),
        }
        self._memory_cache[key] = entry
        with open(self._file_path(key), "w", encoding="utf-8") as f:
            json.dump(entry, f, ensure_ascii=False)

    def clear(self) -> None:
        """Clear all cached responses."""
        self._memory_cache.clear()
        for f in os.listdir(self.cache_dir):
            if f.endswith(".json"):
                os.remove(os.path.join(self.cache_dir, f))

    def stats(self) -> Dict:
        """Return cache stats."""
        files = [f for f in os.listdir(self.cache_dir) if f.endswith(".json")]
        return {
            "memory_entries": len(self._memory_cache),
            "disk_entries": len(files),
            "ttl_seconds": self.ttl_seconds,
        }
