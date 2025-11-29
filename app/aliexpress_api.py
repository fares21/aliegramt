import hashlib
import hmac
import time
import requests
import json
from typing import Dict, Any, List, Optional

class AliExpressApiClient:
    def __init__(self, app_key: str = None, app_secret: str = None, tracking_id: str = None):
        from .config import AE_APP_KEY, AE_APP_SECRET, ALI_TRACKING_ID
        
        self.app_key = app_key or AE_APP_KEY
        self.app_secret = app_secret or AE_APP_SECRET
        self.tracking_id = tracking_id or ALI_TRACKING_ID
        self.base_url = "https://api-sg.aliexpress.com/sync"

    def _sign(self, params: Dict[str, Any]) -> str:
        """توقيع الطلبات لـ AliExpress API"""
        sorted_params = sorted([
            (k, str(v)) for k, v in params.items() 
            if v is not None and k != 'sign'
        ])
        
        concatenated = ''.join(f"{k}{v}" for k, v in sorted_params)
        
        signature = hmac.new(
            self.app_secret.encode('utf-8'),
            concatenated.encode('utf-8'),
            hashlib.sha256
        ).hexdigest().upper()
        
        return signature

    def _request(self, method: str, api_params: Dict[str, Any]) -> Dict[str, Any]:
        """إرسال طلب إلى AliExpress API"""
        timestamp = str(int(time.time() * 1000))
        
        params = {
            "method": method,
            "app_key": self.app_key,
            "timestamp": timestamp,
            "sign_method": "sha256",
            **api_params
        }
        
        # إضافة التوقيع
        params["sign"] = self._sign(params)
        
        print(f"🔧 إرسال طلب {method} إلى AliExpress API...")
        response = requests.get(self.base_url, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        return data

    def search_products(self, category_info: Dict[str, Any], limit: int = 20, 
                       min_price: Optional[float] = None, max_price: Optional[float] = None) -> List[Dict[str, Any]]:
        """بحث عن المنتجات - الدالة المفقودة!"""
        try:
            keywords = category_info.get("keywords", "")
            category_id = category_info.get("category_id", "")
            
            api_params = {
                "keywords": keywords,
                "page_size": limit,
                "tracking_id": self.tracking_id,
            }
            
            if category_id:
                api_params["category_id"] = category_id
            if min_price is not None:
                api_params["min_price"] = min_price
            if max_price is not None:
                api_params["max_price"] = max_price

            method_name = "aliexpress.affiliate.product.query"
            raw = self._request(method_name, api_params)

            items = self._extract_products_from_response(raw)
            print(f"✅ تم العثور على {len(items)} منتج للفئة {category_info.get('name')}")
            return items
            
        except Exception as e:
            print(f"❌ خطأ في البحث عن المنتجات: {e}")
            return []

    def _extract_products_from_response(self, raw: Dict[str, Any]) -> List[Dict[str, Any]]:
        """استخراج المنتجات من استجابة API"""
        products = []
        
        try:
            resp = raw.get("aliexpress_affiliate_product_query_response", {})
            resp_result = resp.get("resp_result", {})
            result = resp_result.get("result", {})
            products_node = result.get("products", {})
            
            if isinstance(products_node, list):
                items = products_node
            elif isinstance(products_node, dict):
                items = products_node.get("product", []) or []
            else:
                items = []

            for item in items:
                if isinstance(item, dict):
                    product = {
                        "id": item.get("product_id") or item.get("productId"),
                        "title": item.get("product_title") or item.get("productTitle"),
                        "original_price": self._extract_price(item),
                        "image_url": (
                            item.get("product_main_image_url") or
                            item.get("imageUrl") or
                            (item.get("allImageUrls") or "").split("|")[0]
                        ),
                        "product_url": (
                            item.get("promotion_link") or
                            item.get("promotionLink") or
                            item.get("product_detail_url") or
                            item.get("productUrl")
                        ),
                    }
                    
                    if product["id"] and product["title"] and product["product_url"]:
                        products.append(product)

        except Exception as e:
            print(f"❌ خطأ في استخراج المنتجات: {e}")

        return products

    def _extract_price(self, item: Dict[str, Any]) -> float:
        """استخراج سعر المنتج"""
        price_fields = [
            "target_sale_price", "target_original_price", 
            "site_price", "originalPrice", "salePrice"
        ]
        for field in price_fields:
            v = item.get(field)
            if v:
                try:
                    return float(v)
                except ValueError:
                    continue
        return 0.0

    def generate_affiliate_link(self, product_url: str) -> str:
        """إنشاء رابط تابع مختصر"""
        try:
            api_params = {
                "urls": product_url,
                "tracking_id": self.tracking_id,
            }
            
            method_name = "aliexpress.affiliate.link.generate"
            raw = self._request(method_name, api_params)

            # استخراج الرابط المختصر من الاستجابة
            result = raw.get("aliexpress_affiliate_link_generate_response", {})
            resp_result = result.get("resp_result", {})
            
            if "error" in resp_result:
                error_msg = resp_result.get("error", "Unknown error")
                print(f"❌ خطأ من API: {error_msg}")
                return product_url
            
            promotion_links = resp_result.get("result", {}).get("promotion_links", [])
            
            if promotion_links and len(promotion_links) > 0:
                short_link = promotion_links[0].get("promotion_url") or promotion_links[0].get("promotion_link")
                if short_link and short_link != product_url:
                    print(f"✅ تم إنشاء رابط مختصر: {short_link}")
                    return short_link
            
            print("❌ لم يتم إنشاء رابط مختصر")
            return product_url
            
        except Exception as e:
            print(f"❌ خطأ في إنشاء الرابط التابع: {e}")
            return product_url
