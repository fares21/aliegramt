import os
from pathlib import Path
from dotenv import load_dotenv

# تحميل المتغيرات من .env (محلياً)؛ على Render ستضعها في Environment
BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / ".env"
if ENV_PATH.exists():
    load_dotenv(ENV_PATH)

# Telegram
TELEGRAM_BOT_TOKEN = os.getenv("8249940703:AAFDY4WfZy0UKas3DHyilpMPKnJ3YhI6EtU")
TELEGRAM_CHANNEL_ID = os.getenv("@best_coupons_ali_dz")  # مثال: "@my_channel" أو -1001234567890

# AliExpress Affiliate API
ALI_APP_KEY = os.getenv("521886")
ALI_APP_SECRET = os.getenv("6IHcTDDFyHZG8LTKon2oXH2XZjSPUB3s")
ALI_TRACKING_ID = os.getenv("Aliepresxrper")  # PID أو trackingId حسب النظام
ALI_API_BASE = "https://api-some-endpoint.aliexpress.com"  # ستُعدل لاحقاً حسب الدوكيمنت [web:2][web:8]

# مسارات الملفات
DATA_DIR = BASE_DIR / "data"
COUPONS_FILE = DATA_DIR / "coupons.json"
SENT_PRODUCTS_FILE = DATA_DIR / "sent_products.json"

# إعدادات عامة للبوت
POST_PREFIX_TEXT = os.getenv(
    "POST_PREFIX_TEXT",
    "🔥 عرض اليوم "
)

# فئات البحث: يمكنك استخدام categoryId أو كلمات مفتاحية
PRODUCT_CATEGORIES = [
    {
        "name": "phones",
        "keywords": "smartphone mobile phone",
        "category_id": None  # ضع ID الفئة لو تعرفه
    },
    {
        "name": "pc_accessories",
        "keywords": "laptop accessories computer accessories",
        "category_id": None
    }
]

# عدد المنتجات التي نجلبها من API قبل اختيار واحد منها عشوائياً
ALI_PRODUCTS_FETCH_LIMIT = 20
