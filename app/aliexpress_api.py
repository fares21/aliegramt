import random
from typing import Dict, Any, Optional
from .config import PRODUCT_CATEGORIES, ALI_PRODUCTS_FETCH_LIMIT
# لاحقاً سنستورد AliExpressApiClient من aliexpress_api.py


class ProductSelector:
    def __init__(self, ali_client):
        """
        ali_client: كائن مسؤول عن الاتصال بـ AliExpress API
        يجب أن يوفّر دالة مثل:
        search_products(category_info, limit) -> List[Dict]
        """
        self.ali_client = ali_client

    def choose_random_category(self) -> Dict[str, Any]:
        return random.choice(PRODUCT_CATEGORIES)

    def get_random_product(self) -> Optional[Dict[str, Any]]:
        """
        - اختيار فئة عشوائية.
        - جلب مجموعة منتجات من AliExpress API.
        - اختيار منتج واحد عشوائي.
        حالياً مجرد واجهة؛ المنطق الدقيق للفلترة حسب السعر سنضيفه بعد ربط API.
        """
        category = self.choose_random_category()
        products = self.ali_client.search_products(
            category_info=category,
            limit=ALI_PRODUCTS_FETCH_LIMIT,
        )
        if not products:
            return None
        return random.choice(products)
