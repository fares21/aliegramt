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
        # يمكنك لاحقاً ضبط min_price/max_price لتتناسب مع شرائح الكوبونات
        products = self.ali_client.search_products(
            category_info=category,
            limit=ALI_PRODUCTS_FETCH_LIMIT,
        )
        return products

    def get_random_product(self) -> Optional[Dict[str, Any]]:
        """
        اختيار فئة عشوائية ثم منتج عشوائي منها.
        يمكنك توسيعها لتتجنب المنتجات ذات سعر خارج نطاق الكوبونات.
        """
        category = self.choose_random_category()
        products = self.get_products_for_category(category)
        if not products:
            return None

        # يمكن هنا فلترة حسب السعر (مثال: >= 18)
        filtered = [p for p in products if p.get("original_price", 0) >= 18]
        if not filtered:
            filtered = products

        return random.choice(filtered)
