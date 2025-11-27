import requests
from typing import Optional
from .config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHANNEL_ID

TELEGRAM_API_BASE = "https://api.telegram.org"


class TelegramBot:
    def __init__(self, token: str = TELEGRAM_BOT_TOKEN, channel_id: str = TELEGRAM_CHANNEL_ID):
        if not token:
            raise ValueError("TELEGRAM_BOT_TOKEN is not set")
        if not channel_id:
            raise ValueError("TELEGRAM_CHANNEL_ID is not set")

        self.token = token
        self.channel_id = channel_id

    def _build_url(self, method: str) -> str:
        return f"{TELEGRAM_API_BASE}/bot{self.token}/{method}"

    def send_text(
        self,
        text: str,
        parse_mode: Optional[str] = "HTML",
        disable_web_page_preview: bool = False,
    ) -> dict:
        url = self._build_url("sendMessage")
        payload = {
            "chat_id": self.channel_id,
            "text": text,
            "parse_mode": parse_mode,
            "disable_web_page_preview": disable_web_page_preview,
        }
        resp = requests.post(url, json=payload, timeout=15)
        resp.raise_for_status()
        return resp.json()

    def send_photo_with_caption(
    self,
    photo_url: str,
    caption: str,
    parse_mode: Optional[str] = "HTML",
) -> dict:
    url = self._build_url("sendPhoto")
    payload = {
        "chat_id": self.channel_id,
        "photo": photo_url,
        "caption": caption,
        "parse_mode": parse_mode,
    }
    print("DEBUG TELEGRAM PAYLOAD:", payload)  # تشخيص
    resp = requests.post(url, json=payload, timeout=20)
    print("DEBUG TELEGRAM RESPONSE:", resp.status_code, resp.text)  # تشخيص
    resp.raise_for_status()
    return resp.json()

