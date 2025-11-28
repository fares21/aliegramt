import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / ".env"
if ENV_PATH.exists():
    load_dotenv(ENV_PATH)

# Telegram
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID")  # مثال: "@my_channel" أو -1001234567890

# AliExpress Affiliate API
AE_APP_KEY = os.getenv("AE_APP_KEY")
AE_APP_SECRET = os.getenv("AE_APP_SECRET")
ALI_TRACKING_ID = os.getenv("ALI_TRACKING_ID")

ALI_API_BASE = "https://api-some-endpoint.aliexpress.com"

DATA_DIR = BASE_DIR / "data"
COUPONS_FILE = DATA_DIR / "coupons.json"
SENT_PRODUCTS_FILE = DATA_DIR / "sent_products.json"

POST_PREFIX_TEXT = os.getenv(
    "POST_PREFIX_TEXT",
    "🔥 عرض اليوم "
)

PRODUCT_CATEGORIES = [
    {"name": "هواتف", "keywords": "smartphone mobile phone"},
]
ALI_PRODUCTS_FETCH_LIMIT = 20
