import os
import time
import hashlib
import hmac
import requests
from typing import Dict, Any, List, Optional
from .config import AE_APP_KEY, AE_APP_SECRET, ALI_TRACKING_ID

ALI_GATEWAY = "https://api-sg.aliexpress.com/sync"
ALI_ACCESS_TOKEN = os.getenv("ALI_ACCESS_TOKEN")


class AliExpressApiError(Exception):
    pass


class AliExpressApiClient:
    """
    عميل مبسط لـ AliExpress Affiliate API (البيئة الجديدة api-sg + OAuth).
    """

    def __init__(
        self,
        app_key: str = AE_APP_KEY,
        app_secret: str = AE_APP_SECRET,
        tracking_id: str = ALI_TRACKING_ID,
    ):
        if not app_key or not app_secret:
            raise ValueError("AliExpress APP_KEY/APP_SECRET not configured")
        if not tracking_id:
            raise ValueError("ALI_TRACKING_ID is not set")
        if not ALI_ACCESS_TOKEN:
            raise ValueError("ALI_ACCESS_TOKEN env var is not set")

        self.app_key = app_key
        self.app_secret = app_secret
        self.tracking_id = tracking_id
        self.access_token = ALI_ACCESS_TOKEN

        print(
            "DEBUG ALI CREDS:",
            self.app_key,
            (self.app_secret[:4] + "****") if self.app_secret else "NO_SECRET",
            self.tracking_id,
        )

    # ---------- توقيع Business Interface (Case 1) ----------

    def _sign(self, params: Dict[str, Any]) -> str:
        """
        Signature algorithm (Business Interface):
        1) sort all params by name (ASCII), excluding sign and None
        2) concat key+value
        3) HMAC-SHA256(concatenated, app_secret) -> HEX UPPER
        """
        items = [
            (k, v) for k, v in params.items()
            if v is not None and k != "sign"
        ]
        items.sort(key=lambda x: x[0])

        concatenated = "".join(f"{k}{v}" for k, v in items)

        digest = hmac.new(
            self.app_secret.encode("utf-8"),
            concatenated.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest().upper()

        return digest

    def _build_common_params(self, method: str) -> Dict[str, Any]:
        # Business Interfaces
        timestamp = int(time.time() * 1000)  # ms
        return {
            "app_key": self.app_key,
            "access_token": self.access_token,
            "timestamp": timestamp,
            "sign_method": "sha256",
            "method": method,
        }

    def _request(self, method: str, api_params: Dict[str, Any]) -> Dict[str, Any]:
        params = self._build_common_params(method)
        params.update(api_params)
        params["sign"] = self._sign(params)

        resp = requests.get(
            ALI_GATEWAY,
            params=params,
            timeout=20,
        )
        resp.raise_for_status()
        data = resp.json()
        print("DEBUG ALI RAW:", data)
        return data

    # ---------- دوال العمل ----------

    def search_products(
        self,
        category_info: Dict[str, Any],
        limit: int = 20,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """
        بحث عن منتجات حسب الكلمات المفتاحية/الفئة وإرجاع لائحة منتجات
        مع محاولة تضمين promotion_link إن وجد.
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

        items = self._extract_products_from_response(raw)
        return items

    def _extract_products_from_response(
        self, raw: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        استخراج المنتجات من استجابة aliexpress.affiliate.product.query،
        مع تفضيل promotion_link كرابط أفلييت قصير إن وجد.
        """
        products: List[Dict[str, Any]] = []

        # لو raw جاء كسلسلة JSON، حوّله إلى dict
        if isinstance(raw, str):
            try:
                import json
                raw = json.loads(raw)
            except Exception:
                return []

        try:
            resp = raw.get("aliexpress_affiliate_product_query_response", {})
            resp_result = resp.get("resp_result", {})
            result = resp_result.get("result", {})
            products_node = result.get("products", {})
        except AttributeError:
            return []

        # products يمكن أن تكون قائمة أو dict فيه key "product"
        if isinstance(products_node, list):
            items = products_node
        elif isinstance(products_node, dict):
            items = products_node.get("product", []) or []
        else:
            items = []

        for item in items:
            if not isinstance(item, dict):
                continue

            # أولوية للرابط المختصر لو أعاده الـ API
            promotion_link = (
                item.get("promotion_link")
                or item.get("promotionLink")
                or item.get("promotion_url")
            )

            product_url = (
                promotion_link
                or item.get("product_detail_url")
                or item.get("productUrl")
                or item.get("product_url")
            )

            product = {
                "id": item.get("product_id") or item.get("productId"),
                "title": item.get("product_title") or item.get("productTitle"),
                "original_price": self._extract_price(item),
                "image_url": (
                    item.get("product_main_image_url")
                    or item.get("imageUrl")
                    or (item.get("allImageUrls") or "").split("|")[0]
                ),
                # هذا الذي سيُستخدم في الرسائل
                "product_url": product_url,
                # حفظ promotion_link منفصلًا لو أردنا التحقق منه أو تفضيله
                "promotion_link": promotion_link,
            }

            print(
                "DEBUG PRODUCT:",
                "ID=", product["id"],
                "| HasPromotion=", bool(promotion_link),
                "| URL=", product_url,
            )

            if product["id"] and product["title"] and product["product_url"]:
                products.append(product)

        return products

    def _extract_price(self, item: Dict[str, Any]) -> float:
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
        توليد رابط أفلييت مختصر لمنتج معيّن باستخدام
        aliexpress.affiliate.link.generate
        """
        try:
            api_params = {
                "tracking_id": self.tracking_id,
                "urls": product_url,
            }

            method_name = "aliexpress.affiliate.link.generate"
            raw = self._request(method_name, api_params)

            print(f"DEBUG AFFILIATE RESPONSE: {raw}")

            resp = raw.get("aliexpress_affiliate_link_generate_response", {})
            resp_result = resp.get("resp_result", {})
            result = resp_result.get("result", {})

            promotion_links = result.get("promotion_links", [])

            # بعض الأحيان يكون dict بدل list
            if isinstance(promotion_links, dict):
                promotion_links = promotion_links.get("promotion_link", []) or promotion_links

            if not promotion_links:
                print("❌ لم يتم إنشاء رابط مختصر - استخدام الرابط الأصلي")
                return product_url

            link_info = promotion_links[0] if isinstance(promotion_links, list) else promotion_links
            promo_url = (
                link_info.get("promotion_url")
                or link_info.get("promotion_link")
                or link_info.get("promotionUrl")
            )

            if promo_url:
                print(f"✅ تم إنشاء رابط مختصر: {promo_url}")
                return promo_url

            print("❌ لم يتم العثور على promotion_url في الاستجابة - استخدام الرابط الأصلي")
            return product_url

        except Exception as e:
            print(f"❌ Error generating affiliate link: {e}")
            return product_url

    def ensure_short_link(self, product: Dict[str, Any]) -> Optional[str]:
        """
        يتأكد من وجود رابط أفلييت مختصر للمنتج:
        - إن وُجد promotion_link في المنتج يستخدمه مباشرة.
        - إن لم يوجد، يولّد رابط مختصر عبر get_affiliate_link.
        - إن فشل كل شيء، يرجع للرابط الأصلي.
        """
        promotion_link = product.get("promotion_link")
        if promotion_link:
            return promotion_link

        product_url = product.get("product_url")
        if not product_url:
            return None

        short_link = self.get_affiliate_link(product_url)
        if short_link and short_link != product_url:
            return short_link

        return product_url
