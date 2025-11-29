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
        # إزالة القيم الفارغة وترتيب المعلمات
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

    def generate_affiliate_link(self, product_url: str) -> str:
        """إنشاء رابط تابع مختصر - الدالة الأساسية"""
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
            
            print(f"🔧 إرسال طلب إلى AliExpress API...")
            response = requests.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            print(f"📨 استجابة API: {json.dumps(data, indent=2)}")
            
            # استخراج الرابط المختصر من الاستجابة
            result = data.get("aliexpress_affiliate_link_generate_response", {})
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
            
        except requests.exceptions.RequestException as e:
            print(f"❌ خطأ في الاتصال: {e}")
            return product_url
        except Exception as e:
            print(f"❌ خطأ غير متوقع: {e}")
            return product_url
