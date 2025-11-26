import json
import time
from pathlib import Path
from typing import Dict, Any, List
from .config import SENT_PRODUCTS_FILE


DEFAULT_TTL_SECONDS = 7 * 24 * 60 * 60  # 7 أيام


class SentProductsStore:
    def __init__(self, path: Path = SENT_PRODUCTS_FILE):
        self.path = Path(path)
        self.data: Dict[str, Any] = {"products": []}
        self._load()

    def _load(self) -> None:
        if not self.path.exists():
            self._save()
            return
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                self.data = json.load(f)
        except Exception:
            self.data = {"products": []}
            self._save()

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)

    def _now_ts(self) -> int:
        return int(time.time())

    def mark_sent(self, product_id: str) -> None:
        product_id = str(product_id)
        ts = self._now_ts()
        found = False

        for p in self.data.get("products", []):
            if str(p.get("id")) == product_id:
                p["last_sent_ts"] = ts
                found = True
                break

        if not found:
            self.data.setdefault("products", []).append(
                {"id": product_id, "last_sent_ts": ts}
            )

        self._save()

    def was_sent_recently(self, product_id: str, ttl_seconds: int) -> bool:
        product_id = str(product_id)
        now = self._now_ts()
        for p in self.data.get("products", []):
            if str(p.get("id")) == product_id:
                last_ts = int(p.get("last_sent_ts", 0))
                if now - last_ts <= ttl_seconds:
                    return True
                return False
        return False

    def cleanup_older_than(self, ttl_seconds: int) -> None:
        now = self._now_ts()
        new_list: List[Dict[str, Any]] = []
        for p in self.data.get("products", []):
            last_ts = int(p.get("last_sent_ts", 0))
            if now - last_ts <= ttl_seconds * 4:
                new_list.append(p)
        self.data["products"] = new_list
        self._save()
