import random
from typing import Dict, Any, Optional, List
from .config import PRODUCT_CATEGORIES, ALI_PRODUCTS_FETCH_LIMIT
from .aliexpress_api import AliExpressApiClient


class ProductSelector:
    def __init__(self, ali_client: AliExpressApiClient):
        self.ali_client = ali_client

    def choose_random_category(self) -> Dict[str, Any]:
        return random.choice(PRODUCT_CATEGORIES)

    def get_products_for_category(self, category: Dict[str, Any]) -> List[Dict[str, Any]]:
        products = self.ali_client.search_products(
            category_info=category,
            limit=ALI_PRODUCTS_FETCH_LIMIT,
        )
        return products

    def get_random_product(self) -> Optional[Dict[str, Any]]:
        """
        اختيار فئة عشوائية ثم منتج عشوائي منها، مع فلترة قوية للهواتف.
        """
        category = self.choose_random_category()
        products = self.get_products_for_category(category)
        if not products:
            return None

        phone_keywords = [
            "smartphone", "mobile phone", "cell phone",
            "blackview", "android", "xiaomi", "redmi",
            "poco", "realme", "huawei", "oneplus",
        ]

        def is_phone(p: Dict[str, Any]) -> bool:
            title = (p.get("title") or "").lower()
            # استبعد كلمات شائعة في الإكسسوارات
            bad = ["case", "cover", "holder", "stand", "charger", "cable", "earphone", "headphone"]
            if any(b in title for b in bad):
                return False
            return any(k in title for k in phone_keywords)

        # فلترة هواتف فقط وبسعر معقول مثلاً >= 50$
        filtered = [
            p for p in products
            if is_phone(p) and p.get("original_price", 0) >= 500
        ]

        if not filtered:
            # لو لم نجد هواتف، نرجع لأي منتج (fallback)
            filtered = products

        return random.choice(filtered)
