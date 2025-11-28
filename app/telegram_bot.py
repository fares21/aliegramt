import requests
from typing import Optional
from .config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHANNEL_ID

TELEGRAM_API_BASE = "https://api.telegram.org"


class TelegramBot:
    def __init__(
        self,
        token: str = TELEGRAM_BOT_TOKEN,
        channel_id: str = TELEGRAM_CHANNEL_ID,
    ):
        if not token:
            raise ValueError("TELEGRAM_BOT_TOKEN is not set")
        if not channel_id:
            raise ValueError("TELEGRAM_CHANNEL_ID is not set")

        self.token = token
        self.channel_id = channel_id

    def _build_url(self, method: str) -> str:
        return f"{TELEGRAM_API_BASE}/bot{self.token}/{method}"

    def _clean_caption(self, text: str, max_len: int = 1024) -> str:
        """
        تنظيف بسيط للكابشن حتى يناسب HTML وتيليجرام:
        - قصه لو تجاوزه max_len (الكابشن حدّه 1024).
        - حذف أو استبدال المحارف التي قد تكسر HTML.
        """
        if not text:
            return ""

        text = text.strip()
        if len(text) > max_len:
            text = text[: max_len - 3] + "..."

        # إزالة محارف HTML الخطيرة
        unsafe = ["<", ">", "&"]
        for ch in unsafe:
            text = text.replace(ch, " ")

        return text

    def send_text(
        self,
        text: str,
        parse_mode: Optional[str] = "HTML",
        disable_web_page_preview: bool = False,
    ) -> dict:
        url = self._build_url("sendMessage")

        # تنظيف النص إذا كنا نستخدم HTML
        if parse_mode == "HTML":
            # الحد الأقصى للرسالة النصية 4096
            text = self._clean_caption(text, max_len=4096)

        payload = {
            "chat_id": self.channel_id,
            "text": text,
            "disable_web_page_preview": disable_web_page_preview,
        }
        if parse_mode:
            payload["parse_mode"] = parse_mode

        resp = requests.post(url, json=payload, timeout=15)
        try:
            print("TELEGRAM SEND_MESSAGE:", resp.status_code, resp.text)
        except Exception:
            pass
        resp.raise_for_status()
        return resp.json()

    def send_photo_with_caption(
        self,
        photo_url: str,
        caption: str,
        parse_mode: Optional[str] = "HTML",
    ) -> dict:
        url = self._build_url("sendPhoto")

        # تنظيف الكابشن واحترام حد 1024 حرف
        if parse_mode == "HTML":
            caption = self._clean_caption(caption, max_len=1024)

        payload = {
            "chat_id": self.channel_id,
            "photo": photo_url,
            "caption": caption,
        }
        if parse_mode:
            payload["parse_mode"] = parse_mode

        print("DEBUG TELEGRAM PAYLOAD:", payload)

        resp = requests.post(url, json=payload, timeout=20)
        try:
            print("DEBUG TELEGRAM RESPONSE:", resp.status_code, resp.text)
        except Exception:
            pass

        # في حالة فشل sendPhoto (مثلاً 400) نحاول إرسال نص بديل بدل إسقاط الحملة
        if not resp.ok:
            fallback_text = f"{caption}{photo_url}"
            try:
                self.send_text(fallback_text, parse_mode=parse_mode)
            except Exception as e:
                print("TELEGRAM FALLBACK ERROR:", repr(e))
            resp.raise_for_status()

        return resp.json()
