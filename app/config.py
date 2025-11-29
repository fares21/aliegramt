import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from typing import Dict, Any, List

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / ".env"

if ENV_PATH.exists():
    load_dotenv(ENV_PATH)
else:
    print("⚠️  ملف .env غير موجود. باستخدام متغيرات البيئة النظامية.")

class ConfigError(Exception):
    """استثناء مخصص لأخطاء التهيئة"""
    pass

def get_required_env(var_name: str, default: Any = None) -> str:
    """
    جلب متغير بيئي مطلوب مع التحقق من وجوده
    """
    value = os.getenv(var_name, default)
    if value is None:
        raise ConfigError(f"❌ المتغير البيئي المطلوب {var_name} غير موجود!")
    
    if not value.strip():
        raise ConfigError(f"❌ المتغير البيئي {var_name} فارغ!")
    
    return value

def get_optional_env(var_name: str, default: Any = None) -> Any:
    """
    جلب متغير بيئي اختياري
    """
    value = os.getenv(var_name, default)
    return value if value is not None else default

# Telegram Configuration
try:
    TELEGRAM_BOT_TOKEN = get_required_env("TELEGRAM_BOT_TOKEN")
    TELEGRAM_CHANNEL_ID = get_required_env("TELEGRAM_CHANNEL_ID")
    
    # التحقق من صحة تنسيق Channel ID
    if not (TELEGRAM_CHANNEL_ID.startswith('@') or 
            (TELEGRAM_CHANNEL_ID.startswith('-100') and TELEGRAM_CHANNEL_ID[1:].isdigit())):
        print("⚠️  تحذير: TELEGRAM_CHANNEL_ID قد لا يكون بصيغة صحيحة")
        
except ConfigError as e:
    print(f"❌ خطأ في إعدادات تيليجرام: {e}")
    sys.exit(1)

# AliExpress Affiliate API Configuration
try:
    AE_APP_KEY = get_required_env("AE_APP_KEY")
    AE_APP_SECRET = get_required_env("AE_APP_SECRET")
    ALI_TRACKING_ID = get_required_env("ALI_TRACKING_ID")
except ConfigError as e:
    print(f"❌ خطأ في إعدادات AliExpress API: {e}")
    sys.exit(1)

# AliExpress API Endpoints
ALI_API_BASE = "https://api-sg.aliexpress.com/sync"
ALI_OAUTH_BASE = "https://api-sg.aliexpress.com/rest"

# File Paths
DATA_DIR = BASE_DIR / "data"
COUPONS_FILE = DATA_DIR / "coupons.json"
SENT_PRODUCTS_FILE = DATA_DIR / "sent_products.json"
LOG_FILE = DATA_DIR / "app.log"

# إنشاء المجلدات إذا لم تكن موجودة
DATA_DIR.mkdir(exist_ok=True)

# Content Settings
POST_PREFIX_TEXT = get_optional_env("POST_PREFIX_TEXT", "🔥 عرض اليوم")

# Product Categories - قائمة موسعة ومتنوعة
PRODUCT_CATEGORIES: List[Dict[str, Any]] = [
    # هواتف العلامات التجارية الشهيرة
    {"name": "Xiaomi", "keywords": "xiaomi smartphone mobile phone", "category_id": "5090801"},
    {"name": "Redmi", "keywords": "redmi smartphone", "category_id": "5090801"},
    {"name": "Poco", "keywords": "poco smartphone", "category_id": "5090801"},
    {"name": "Realme", "keywords": "realme smartphone", "category_id": "5090801"},
    {"name": "Samsung", "keywords": "samsung smartphone", "category_id": "5090801"},
    {"name": "Oppo", "keywords": "oppo smartphone", "category_id": "5090801"},
    {"name": "Vivo", "keywords": "vivo smartphone", "category_id": "5090801"},
    {"name": "Huawei", "keywords": "huawei smartphone", "category_id": "5090801"},
    {"name": "OnePlus", "keywords": "oneplus smartphone", "category_id": "5090801"},
    {"name": "Apple", "keywords": "iphone smartphone", "category_id": "5090801"},
    
    # هواتف المقاومة للماء والطبيعة
    {"name": "Blackview", "keywords": "blackview rugged smartphone", "category_id": "5090801"},
    {"name": "Doogee", "keywords": "doogee rugged smartphone", "category_id": "5090801"},
    {"name": "Ulefone", "keywords": "ulefone smartphone", "category_id": "5090801"},
    {"name": "Oukitel", "keywords": "oukitel smartphone", "category_id": "5090801"},
    
    # هواتف الألعاب
    {"name": "Gaming Phones", "keywords": "gaming smartphone", "category_id": "5090801"},
    
    # هواتف الميزانية
    {"name": "Budget Phones", "keywords": "cheap smartphone under 100", "category_id": "5090801"},
    {"name": "Infinix", "keywords": "infinix smartphone", "category_id": "5090801"},
    {"name": "Tecno", "keywords": "tecno smartphone", "category_id": "5090801"},
    {"name": "Nokia", "keywords": "nokia smartphone", "category_id": "5090801"},
    
    # هواتف 5G
    {"name": "5G Phones", "keywords": "5g smartphone", "category_id": "5090801"},
]

# API Limits and Settings
ALI_PRODUCTS_FETCH_LIMIT = int(get_optional_env("ALI_PRODUCTS_FETCH_LIMIT", "20"))
MAX_PRODUCT_PRICE = float(get_optional_env("MAX_PRODUCT_PRICE", "500"))
MIN_PRODUCT_PRICE = float(get_optional_env("MIN_PRODUCT_PRICE", "30"))

# Application Settings
DEBUG = get_optional_env("DEBUG", "False").lower() == "true"
LOG_LEVEL = get_optional_env("LOG_LEVEL", "INFO")
REQUEST_TIMEOUT = int(get_optional_env("REQUEST_TIMEOUT", "30"))

# Price Settings for Coupons
PRICE_RANGES = {
    "low": (30, 50),
    "medium": (50, 100),
    "high": (100, 200),
    "premium": (200, 500)
}

def validate_config() -> bool:
    """
    التحقق من صحة جميع الإعدادات
    """
    try:
        # التحقق من إعدادات تيليجرام
        if not TELEGRAM_BOT_TOKEN or len(TELEGRAM_BOT_TOKEN) < 10:
            raise ConfigError("TELEGRAM_BOT_TOKEN غير صالح")
        
        # التحقق من إعدادات AliExpress
        if not AE_APP_KEY or not AE_APP_SECRET:
            raise ConfigError("مفاتيح API لـ AliExpress غير صالحة")
        
        # التحقق من الملفات والمجلدات
        if not DATA_DIR.exists():
            DATA_DIR.mkdir(parents=True, exist_ok=True)
        
        # التحقق من القيم العددية
        if ALI_PRODUCTS_FETCH_LIMIT <= 0 or ALI_PRODUCTS_FETCH_LIMIT > 100:
            raise ConfigError("حد جلب المنتجات يجب أن يكون بين 1 و 100")
        
        print("✅ جميع الإعدادات صالحة ومهيأة للعمل")
        return True
        
    except Exception as e:
        print(f"❌ خطأ في التحقق من الإعدادات: {e}")
        return False

def get_config_summary() -> Dict[str, Any]:
    """
    الحصول على ملخص للإعدادات (بدون المعلومات الحساسة)
    """
    return {
        "telegram_configured": bool(TELEGRAM_BOT_TOKEN and TELEGRAM_CHANNEL_ID),
        "aliexpress_configured": bool(AE_APP_KEY and AE_APP_SECRET),
        "categories_count": len(PRODUCT_CATEGORIES),
        "products_fetch_limit": ALI_PRODUCTS_FETCH_LIMIT,
        "data_directory": str(DATA_DIR),
        "debug_mode": DEBUG,
        "price_range": f"${MIN_PRODUCT_PRICE} - ${MAX_PRODUCT_PRICE}"
    }

# التحقق من الإعدادات عند الاستيراد
if __name__ == "__main__":
    validate_config()
    summary = get_config_summary()
    print("📊 ملخص الإعدادات:")
    for key, value in summary.items():
        print(f"   {key}: {value}")
