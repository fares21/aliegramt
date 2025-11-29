import json
import time
from pathlib import Path
from typing import Dict, Any, List
from .config import SENT_PRODUCTS_FILE

DEFAULT_TTL_SECONDS = 7 * 24 * 60 * 60  # 7 أيام

class SentProductsStore:
    def __init__(self, path: Path = SENT_PRODUCTS_FILE, max_products: int = 10000):
        self.path = Path(path)
        self.max_products = max_products
        self.data: Dict[str, Any] = {"products": []}
        self._product_index: Dict[str, Dict[str, Any]] = {}
        self._load()

    def _load(self) -> None:
        if not self.path.exists():
            self._save()
            return
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                self.data = json.load(f)
            self._rebuild_index()
        except Exception as e:
            print(f"❌ خطأ في تحميل البيانات: {e}")
            self.data = {"products": []}
            self._product_index = {}
            self._save()

    def _rebuild_index(self):
        """إعادة بناء الفهرس للبحث السريع"""
        self._product_index = {
            str(p["id"]): p for p in self.data.get("products", [])
        }

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"❌ خطأ في حفظ البيانات: {e}")

    def _now_ts(self) -> int:
        return int(time.time())

    def _auto_cleanup(self):
        """تنظيف تلقائي عند الوصول للحد الأقصى"""
        if len(self.data["products"]) <= self.max_products:
            return
            
        sorted_products = sorted(
            self.data["products"], 
            key=lambda x: x.get("last_sent_ts", 0)
        )
        self.data["products"] = sorted_products[-self.max_products:]
        self._rebuild_index()

    def mark_sent(self, product_id: str) -> None:
        product_id = str(product_id)
        ts = self._now_ts()
        
        if product_id in self._product_index:
            self._product_index[product_id]["last_sent_ts"] = ts
        else:
            new_product = {"id": product_id, "last_sent_ts": ts}
            self.data.setdefault("products", []).append(new_product)
            self._product_index[product_id] = new_product
            
            if len(self.data["products"]) > self.max_products:
                self._auto_cleanup()

        self._save()

    def was_sent_recently(self, product_id: str, ttl_seconds: int) -> bool:
        product_id = str(product_id)
        
        if product_id not in self._product_index:
            return False
            
        product = self._product_index[product_id]
        last_ts = int(product.get("last_sent_ts", 0))
        return (self._now_ts() - last_ts) <= ttl_seconds

    def cleanup_older_than(self, ttl_seconds: int) -> None:
        now = self._now_ts()
        new_list: List[Dict[str, Any]] = []
        
        for p in self.data.get("products", []):
            last_ts = int(p.get("last_sent_ts", 0))
            if now - last_ts <= ttl_seconds * 4:
                new_list.append(p)
                
        self.data["products"] = new_list
        self._rebuild_index()
        self._save()

    def get_stats(self) -> Dict[str, Any]:
        """الحصول على إحصائيات التخزين"""
        now = self._now_ts()
        products = self.data.get("products", [])
        
        recent_24h = [p for p in products if now - p.get("last_sent_ts", 0) <= 86400]
        recent_7d = [p for p in products if now - p.get("last_sent_ts", 0) <= 604800]
        
        return {
            "total_products": len(products),
            "recent_24h": len(recent_24h),
            "recent_7d": len(recent_7d),
            "file_size_kb": self.path.stat().st_size / 1024 if self.path.exists() else 0,
        }
