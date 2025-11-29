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
        """جلب المنتجات للفئة مع معالجة الأخطاء المبسطة"""
        try:
            products = self.ali_client.search_products(
                category_info=category,
                limit=ALI_PRODUCTS_FETCH_LIMIT,
            )
            return products or []
        except Exception as e:
            print(f"❌ خطأ في جلب المنتجات للفئة {category.get('name')}: {e}")
            return []

    def get_random_product(self, max_attempts: int = 3) -> Optional[Dict[str, Any]]:
        """اختيار منتج عشوائي - نسخة مبسطة"""
        attempts = 0
        
        while attempts < max_attempts:
            attempts += 1
            
            category = self.choose_random_category()
            print(f"🔍 محاولة {attempts}: البحث في فئة {category.get('name')}")
            
            products = self.get_products_for_category(category)
            
            if products:
                selected_product = random.choice(products)
                print(f"✅ تم اختيار منتج: {selected_product.get('title')}")
                return selected_product
            else:
                print(f"⚠️ لا توجد منتجات في الفئة {category.get('name')}")
        
        print(f"❌ فشل في العثور على منتج مناسب بعد {max_attempts} محاولات")
        return None
