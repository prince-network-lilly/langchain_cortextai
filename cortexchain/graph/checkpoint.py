import json
import os
from typing import Any, Dict, Optional


class MemoryCheckpointer:
    """In-memory checkpointer for graph state. Data is lost when the process exits."""

    def __init__(self):
        self._store: Dict[str, Dict[str, Any]] = {}

    def save(self, thread_id: str, data: Dict[str, Any]) -> None:
        self._store[thread_id] = data

    def load(self, thread_id: str) -> Optional[Dict[str, Any]]:
        return self._store.get(thread_id)

    def delete(self, thread_id: str) -> None:
        self._store.pop(thread_id, None)

    def list_threads(self):
        return list(self._store.keys())


class FileCheckpointer:
    """Persists graph state to disk as JSON files. Survives process restarts."""

    def __init__(self, directory: str = ".checkpoints"):
        self.directory = directory
        os.makedirs(directory, exist_ok=True)

    def _path(self, thread_id: str) -> str:
        safe_id = thread_id.replace("/", "_").replace("\\", "_")
        return os.path.join(self.directory, f"{safe_id}.json")

    def save(self, thread_id: str, data: Dict[str, Any]) -> None:
        with open(self._path(thread_id), "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, default=str)

    def load(self, thread_id: str) -> Optional[Dict[str, Any]]:
        path = self._path(thread_id)
        if not os.path.exists(path):
            return None
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def delete(self, thread_id: str) -> None:
        path = self._path(thread_id)
        if os.path.exists(path):
            os.remove(path)

    def list_threads(self):
        return [f.replace(".json", "") for f in os.listdir(self.directory) if f.endswith(".json")]
