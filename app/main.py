from flask import Flask, jsonify, request
from .config import POST_PREFIX_TEXT
from .coupons import CouponManager
from .telegram_bot import TelegramBot
from .product_selector import ProductSelector
from .aliexpress_api import AliExpressApiClient


def create_app():
    app = Flask(__name__)

    coupon_manager = CouponManager()
    telegram_bot = TelegramBot()
    ali_client = AliExpressApiClient()
    product_selector = ProductSelector(ali_client)

    @app.route("/health", methods=["GET"])
    def health():
        return jsonify({"status": "ok"}), 200

    @app.route("/ali-callback", methods=["GET"])
    def ali_callback():
        code = request.args.get("code")
        print("ALI OAUTH CODE:", code)
        return jsonify({"status": "ok", "code": code}), 200

    @app.route("/publish", methods=["GET"])
    def publish():
        try:
            # 1) اختيار منتج
            product = product_selector.get_random_product()
            if not product:
                return jsonify({"status": "error", "message": "No products found"}), 500

            title = product.get("title")
            original_price = float(product.get("original_price", 0))
            image_url = product.get("image_url")
            product_url = product.get("product_url")
            
            # 2) الإصلاح الحقيقي: إنشاء رابط مختصر جديد
            print(f"🔗 الرابط الأصلي: {product_url}")
            
            # استخدام AliExpress API لإنشاء رابط تابع مختصر
            affiliate_url = ali_client.generate_affiliate_link(product_url)
            
            if affiliate_url == product_url:
                print("❌ فشل في إنشاء رابط مختصر، استخدام الرابط الأصلي")
            else:
                print(f"✅ تم إنشاء رابط مختصر: {affiliate_url}")

            # 3) اختيار كوبون مناسب للسعر
            coupon, final_price = coupon_manager.get_random_coupon_for_price(original_price)

            if coupon is None or final_price is None:
                coupon_text = "لا يوجد كوبون مناسب لهذا السعر حالياً"
                final_price_value = original_price
            else:
                code = coupon.get("code")
                discount = coupon.get("discount")
                coupon_text = f"الكوبون المستخدم: {code} (خصم {discount} دولار)"
                final_price_value = final_price

            # 4) بناء نص الرسالة (مع أسطر جديدة)
            lines = [
                f"{POST_PREFIX_TEXT}: {title}",
                f"💰 السعر الأصلي: {original_price:.2f} دولار",
                coupon_text,
                f"💵 السعر بعد الخصم: {final_price_value:.2f} دولار",
                "",
                f"🛒 رابط المنتج: {affiliate_url}",
                "",
                "#عروض_AliExpress 🎯"
            ]
            message_text = "\n".join(lines)

            # 5) إرسال الرسالة إلى تيليجرام
            if image_url:
                telegram_bot.send_photo_with_caption(
                    photo_url=image_url,
                    caption=message_text,
                )
            else:
                telegram_bot.send_text(text=message_text)

            return jsonify({
                "status": "ok", 
                "original_url": product_url,
                "affiliate_url": affiliate_url,
                "is_shortened": affiliate_url != product_url,
                "message": "تم النشر بنجاح" if affiliate_url != product_url else "تم النشر ولكن الرابط لم يتم تقصيره"
            }), 200

        except Exception as e:
            print("PUBLISH ERROR:", repr(e))
            return jsonify({"status": "error", "message": str(e)}), 500

    # إضافة نقطة نهاية جديدة لاختبار تقصير الروابط
    @app.route("/test-shorten", methods=["GET"])
    def test_shorten():
        """اختبار تقصير الروابط"""
        test_url = request.args.get("url", "https://www.aliexpress.com/item/1005001234567890.html")
        
        try:
            short_url = ali_client.generate_affiliate_link(test_url)
            
            return jsonify({
                "original_url": test_url,
                "short_url": short_url,
                "is_shortened": short_url != test_url,
                "length_original": len(test_url),
                "length_short": len(short_url),
                "success": short_url != test_url
            })
            
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    return app
