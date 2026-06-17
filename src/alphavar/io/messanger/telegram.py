"""Telegram messenger module"""
import logging
import httpx
from alphavar.io.messanger.message_class import AbstractMessanger

logger = logging.getLogger(__name__)

# Characters that must be backslash-escaped in Telegram MarkdownV2.
# https://core.telegram.org/bots/api#markdownv2-style
_MARKDOWN_V2_SPECIAL = r'_*[]()~`>#+-=|{}.!'
_MARKDOWN_V2_TABLE = str.maketrans({ch: f'\\{ch}' for ch in _MARKDOWN_V2_SPECIAL})


def escape_markdown_v2(text: str) -> str:
    """Escape user-provided text for safe interpolation into a MarkdownV2 message.

    Apply to *data* (asset names, error strings, …) — not to the markup itself.
    """
    return str(text).translate(_MARKDOWN_V2_TABLE)


class TelegramMessanger(AbstractMessanger):
    """Telegram messaging over the Bot API.

    The bot token is part of the request URL; it is never written to logs or
    exception messages.
    """

    _API_BASE = 'https://api.telegram.org'

    def __init__(self, token: str, chat_id: str, parse_mode: str | None = 'MarkdownV2'):
        self._token: str = token
        self._chat_id: str = chat_id
        self._parse_mode: str | None = parse_mode

    def send_message(self, text):
        url = f'{self._API_BASE}/bot{self._token}/sendMessage'
        message = {'chat_id': self._chat_id, 'disable_web_page_preview': True, 'text': text}
        if self._parse_mode:
            message['parse_mode'] = self._parse_mode
        try:
            response = httpx.post(url, json=message, timeout=httpx.Timeout(15.0, connect=5.0))
            response.raise_for_status()
        except httpx.HTTPStatusError as err:
            # logger.error (not .exception): a traceback would include the request URL,
            # which carries the bot token. Log status + Telegram's error body only.
            logger.error('Telegram sendMessage failed: HTTP %s — %s',  # noqa: TRY400
                         err.response.status_code, err.response.text)
        except httpx.HTTPError as err:
            # Transport errors (connect/timeout/...). Log the error type only — the
            # traceback / str(err) can include the token-bearing URL.
            logger.error('Telegram sendMessage failed: %s', type(err).__name__)  # noqa: TRY400
