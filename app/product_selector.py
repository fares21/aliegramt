import random
from typing import Dict, Any, Optional, List
from .config import PRODUCT_CATEGORIES, ALI_PRODUCTS_FETCH_LIMIT
from .aliexpress_api import AliExpressApiClient


class ProductSelector:
    def __init__(self, ali_client: AliExpressApiClient):
        self.ali_client = ali_client

    def choose_random_category(self) -> Dict[str, Any]:
        """اختيار فئة عشوائية مع إمكانية ترجيح بعض الفئات"""
        return random.choice(PRODUCT_CATEGORIES)

    def get_products_for_category(self, category: Dict[str, Any]) -> List[Dict[str, Any]]:
        """جلب المنتجات لفئة معينة مع معالجة الأخطاء"""
        try:
            products = self.ali_client.search_products(
                category_info=category,
                limit=ALI_PRODUCTS_FETCH_LIMIT,
            )
            return products or []
        except Exception as e:
            print(f"❌ خطأ في جلب المنتجات للفئة {category.get('name')}: {e}")
            return []

    def is_phone_product(self, product: Dict[str, Any]) -> bool:
        """
        تحديد إذا كان المنتج هاتفاً حقيقياً وليس إكسسوارات
        """
        title = (product.get("title") or "").lower()
        
        # الكلمات الدالة على الهواتف
        phone_keywords = [
            "smartphone", "mobile phone", "cell phone", "android phone",
            "blackview", "xiaomi", "redmi", "poco", "realme", 
            "huawei", "oneplus", "samsung", "oppo", "vivo",
            "infinix", "tecno", "umidigi", "doogee", "nokia",
            "iphone", "5g phone", "4g phone", "unlocked phone"
        ]
        
        # الكلمات التي تشير إلى إكسسوارات وليست هواتف
        accessory_keywords = [
            "case", "cover", "holder", "stand", "charger", 
            "cable", "earphone", "headphone", "headset",
            "battery", "protector", "film", "glass",
            "adapter", "dock", "strap", "grip", "lanyard",
            "repair", "part", "housing", "back cover"
        ]
        
        # يجب أن تحتوي على كلمة هاتف ولا تحتوي على كلمة إكسسوار
        has_phone_keyword = any(keyword in title for keyword in phone_keywords)
        has_accessory_keyword = any(keyword in title for keyword in accessory_keywords)
        
        return has_phone_keyword and not has_accessory_keyword

    def filter_and_rank_products(self, products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        تصفية وترتيب المنتجات حسب الجودة والسعر
        """
        if not products:
            return []
        
        filtered_products = []
        
        for product in products:
            price = product.get("original_price", 0)
            title = product.get("title", "")
            
            # 1. تصفية الهواتف الحقيقية
            if not self.is_phone_product(product):
                continue
                
            # 2. تصفية بالسعر المنطقي للهواتف
            if price < 30 or price > 500:  # نطاق سعر معقول للهواتف
                continue
                
            # 3. التأكد من وجود بيانات كافية
            if not title or not product.get("product_url"):
                continue
                
            # حساب نقاط الجودة للمنتج
            quality_score = 0
            
            # نقاط للسعر المعقول
            if 50 <= price <= 300:
                quality_score += 2
            elif 30 <= price < 50 or 300 < price <= 500:
                quality_score += 1
                
            # نقاط لوجود كلمات دالة إضافية
            title_lower = title.lower()
            if any(word in title_lower for word in ["new", "2024", "2023", "latest"]):
                quality_score += 1
            if "unlocked" in title_lower:
                quality_score += 1
            if "global" in title_lower:
                quality_score += 1
                
            product["quality_score"] = quality_score
            filtered_products.append(product)
        
        # ترتيب المنتجات حسب النقاط (الأفضل أولاً)
        filtered_products.sort(key=lambda x: x.get("quality_score", 0), reverse=True)
        
        return filtered_products

    def get_random_product(self, max_attempts: int = 3) -> Optional[Dict[str, Any]]:
        """
        اختيار منتج عشوائي مع محاولات متعددة وفلترة ذكية
        """
        attempts = 0
        
        while attempts < max_attempts:
            attempts += 1
            
            # 1. اختيار فئة عشوائية
            category = self.choose_random_category()
            print(f"🔍 محاولة {attempts}: البحث في فئة {category.get('name')}")
            
            # 2. جلب المنتجات للفئة
            products = self.get_products_for_category(category)
            if not products:
                print(f"⚠️ لا توجد منتجات في الفئة {category.get('name')}")
                continue
            
            # 3. تصفية وترتيب المنتجات
            filtered_products = self.filter_and_rank_products(products)
            
            if not filtered_products:
                print(f"⚠️ لا توجد هواتف مناسبة في الفئة {category.get('name')}")
                continue
            
            # 4. اختيار منتج (نفضل المنتجات ذات النقاط الأعلى)
            if len(filtered_products) >= 3:
                # اختيار من أفضل 3 منتجات
                top_products = filtered_products[:3]
                selected_product = random.choice(top_products)
            else:
                selected_product = random.choice(filtered_products)
            
            print(f"✅ تم اختيار منتج: {selected_product.get('title')}")
            print(f"💰 السعر: {selected_product.get('original_price')} دولار")
            print(f"🎯 نقاط الجودة: {selected_product.get('quality_score', 0)}")
            
            return selected_product
        
        print(f"❌ فشل في العثور على منتج مناسب بعد {max_attempts} محاولات")
        return None

    def get_products_with_fallback(self, primary_categories: List[str] = None) -> Optional[Dict[str, Any]]:
        """
        جلب منتج مع إعطاء أولوية لفئات معينة
        """
        if primary_categories:
            # ترتيب الفئات حسب الأولوية
            prioritized_categories = []
            other_categories = []
            
            for category in PRODUCT_CATEGORIES:
                if category.get('name') in primary_categories:
                    prioritized_categories.append(category)
                else:
                    other_categories.append(category)
            
            # محاولة الفئات ذات الأولوية أولاً
            for category in prioritized_categories:
                products = self.get_products_for_category(category)
                filtered_products = self.filter_and_rank_products(products)
                if filtered_products:
                    return random.choice(filtered_products[:2])  # أفضل منتجين
        
        # إذا فشلت الفئات ذات الأولوية، العودة للطريقة العادية
        return self.get_random_product()
