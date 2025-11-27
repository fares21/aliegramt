import time
import hashlib
import hmac
import requests
from typing import Dict, Any, List, Optional
from .config import (
    ALI_APP_KEY,
    ALI_APP_SECRET,
    ALI_TRACKING_ID,
)

ALI_GATEWAY = "https://api.taobao.com/router/rest"  # شائع مع Affiliate API [web:126][web:128]


class AliExpressApiError(Exception):
    pass


class AliExpressApiClient:
    """
    عميل مبسط لـ AliExpress Affiliate API.
    - search_products: يستخدم aliexpress.affiliate.product.query أو listPromotionProduct.
    - get_affiliate_links: يحول productUrl إلى promotionUrl.
    """

    def __init__(
        self,
        app_key: str = ALI_APP_KEY,
        app_secret: str = ALI_APP_SECRET,
        tracking_id: str = ALI_TRACKING_ID,
    ):
        if not app_key or not app_secret:
            raise ValueError("AliExpress APP_KEY/APP_SECRET not configured")
        if not tracking_id:
            raise ValueError("ALI_TRACKING_ID is not set")

        self.app_key = app_key
        self.app_secret = app_secret
        self.tracking_id = tracking_id

    def _sign(self, params: Dict[str, Any]) -> str:
        """
        إنشاء توقيع HMAC-MD5 أو MD5 حسب متطلبات AliExpress/Taobao.
        هنا مثال تقليدي: sign = MD5(SECRET + concat(sorted_params) + SECRET).
        ستحتاج لتعديلها إذا تغيّر بروتوكول التوقيع في وثائقهم. [web:128]
        """
        # ترتيب البارامترات أبجدياً
        sorted_items = sorted((k, v) for k, v in params.items() if v is not None)
        query = "".join(f"{k}{v}" for k, v in sorted_items)
        sign_str = f"{self.app_secret}{query}{self.app_secret}"
        return hashlib.md5(sign_str.encode("utf-8")).hexdigest().upper()

    def _build_common_params(self, method: str) -> Dict[str, Any]:
        return {
            "app_key": self.app_key,
            "method": method,
            "format": "json",
            "sign_method": "md5",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "v": "2.0",
        }

    def _request(self, method: str, api_params: Dict[str, Any]) -> Dict[str, Any]:
        params = self._build_common_params(method)
        params.update(api_params)
        params["sign"] = self._sign(params)

        resp = requests.post(
            ALI_GATEWAY,
            data=params,
            headers={
                "Content-Type": "application/x-www-form-urlencoded;charset=utf-8"
            },
            timeout=20,
        )
        resp.raise_for_status()
        data = resp.json()
        # يمكن هنا معالجة أخطاء AliExpress (كود خطأ، إلخ)
        return data

       def search_products(
        self,
        category_info: Dict[str, Any],
        limit: int = 20,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """
        بحث عن منتجات حسب الفئة/الكلمات المفتاحية.
        يلفّ حول aliexpress.affiliate.product.query (أو listPromotionProduct).
        """
        keywords = category_info.get("keywords")
        category_id = category_info.get("category_id")

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

        # سطر التشخيص المهم:
        print("DEBUG ALI RAW:", raw)

        items = self._extract_products_from_response(raw)
        return items


    def _extract_products_from_response(self, raw: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        تحويل استجابة API إلى قائمة منتجات قياسية تحتوي على:
        id, title, original_price, image_url, product_url
        """
        products: List[Dict[str, Any]] = []

        # هذه الشجرة مثال؛ اطبع raw لترى الشكل الحقيقي ثم عدّل.
        # كثير من الأمثلة تضع النتائج في مفتاح مثل:
        # raw["aliexpress_affiliate_product_query_response"]["resp_result"]["result"]["products"]
        # [web:126][web:31]
        try:
            resp = raw.get("aliexpress_affiliate_product_query_response", {})
            resp_result = resp.get("resp_result", {})
            result = resp_result.get("result", {})
            items = result.get("products", [])
        except AttributeError:
            items = []

        for item in items:
            product = {
                "id": item.get("product_id") or item.get("productId"),
                "title": item.get("product_title") or item.get("productTitle"),
                "original_price": self._extract_price(item),
                "image_url": item.get("product_main_image_url")
                or item.get("imageUrl")
                or (item.get("allImageUrls") or "").split("|")[0],
                "product_url": item.get("product_detail_url")
                or item.get("productUrl"),
            }
            if product["id"] and product["title"] and product["product_url"]:
                products.append(product)

        return products

    def _extract_price(self, item: Dict[str, Any]) -> float:
        """
        استخراج السعر من الحقول المحتملة (site_price, target_original_price, originalPrice...). [web:20]
        """
        price_fields = [
            "target_sale_price",
            "target_original_price",
            "site_price",
            "originalPrice",
            "salePrice",
        ]
        for f in price_fields:
            v = item.get(f)
            if v:
                try:
                    return float(v)
                except ValueError:
                    continue
        return 0.0

    def get_affiliate_link(self, product_url: str) -> Optional[str]:
        """
        تحويل productUrl إلى promotionUrl مكتوب برقم التتبع. [web:4][web:103]
        """
        api_params = {
            "tracking_id": self.tracking_id,
            "urls": product_url,
        }
        method_name = "aliexpress.affiliate.link.generate"  # أو getPromotionLinks/listPromotionLinks [web:4][web:103]
        raw = self._request(method_name, api_params)

        # قراءة الاستجابة واستخراج promotionUrl
        try:
            resp = raw.get("aliexpress_affiliate_link_generate_response", {})
            links = resp.get("resp_result", {}).get("result", {}).get("promotion_links", [])
        except AttributeError:
            links = []

        if not links:
            return None

        # نأخذ أول رابط
        link_info = links[0]
        promo_url = link_info.get("promotion_url") or link_info.get("promotionUrl")
        return promo_url or product_url
