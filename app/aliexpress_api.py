import hashlib
import hmac
import time
import requests
from typing import Dict, Any, List, Optional

class AliExpressApiClient:
    def __init__(self, app_key: str, app_secret: str, tracking_id: str):
        self.app_key = app_key
        self.app_secret = app_secret
        self.tracking_id = tracking_id
        self.base_url = "https://api-sg.aliexpress.com/sync"

    def _sign(self, params: Dict[str, Any]) -> str:
        """توقيع الطلبات لـ AliExpress API"""
        sorted_params = sorted([(k, v) for k, v in params.items() if v is not None and k != 'sign'])
        concatenated = ''.join(f"{k}{v}" for k, v in sorted_params)
        signature = hmac.new(
            self.app_secret.encode('utf-8'),
            concatenated.encode('utf-8'),
            hashlib.sha256
        ).hexdigest().upper()
        return signature

    def generate_affiliate_link(self, product_url: str) -> Optional[str]:
        """إنشاء رابط تابع مختصر - الإصلاح الحقيقي هنا"""
        try:
            method = "aliexpress.affiliate.link.generate"
            timestamp = str(int(time.time() * 1000))
            
            params = {
                "method": method,
                "app_key": self.app_key,
                "timestamp": timestamp,
                "sign_method": "sha256",
                "urls": product_url,
                "tracking_id": self.tracking_id,
            }
            
            # إضافة التوقيع
            params["sign"] = self._sign(params)
            
            response = requests.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            print(f"🔍 استجابة API: {data}")
            
            # استخراج الرابط المختصر من الاستجابة
            result = data.get("aliexpress_affiliate_link_generate_response", {})
            promotion_links = result.get("resp_result", {}).get("result", {}).get("promotion_links", [])
            
            if promotion_links and len(promotion_links) > 0:
                short_link = promotion_links[0].get("promotion_url")
                if short_link and short_link != product_url:
                    print(f"✅ تم إنشاء رابط مختصر: {short_link}")
                    return short_link
            
            print("❌ لم يتم إنشاء رابط مختصر")
            return product_url
            
        except Exception as e:
            print(f"❌ خطأ في إنشاء الرابط التابع: {e}")
            return product_url

    def get_product_details(self, product_url: str) -> Dict[str, Any]:
        """الحصول على تفاصيل المنتج وإنشاء رابط مختصر"""
        # أولاً: إنشاء الرابط المختصر
        affiliate_link = self.generate_affiliate_link(product_url)
        
        return {
            "affiliate_link": affiliate_link,
            "original_link": product_url,
            "is_shortened": affiliate_link != product_url
        }
