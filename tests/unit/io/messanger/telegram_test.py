import os
import pytest
from alphavar.io.messanger import TelegramMessanger


@pytest.mark.integration  # sends a real message through the live Telegram Bot API
def test_send_message():
    telegram_token = os.environ.get('TG_BOT_TOKEN')
    telegram_chat_id = os.environ.get('TG_CHAT')
    if not (telegram_token and telegram_chat_id):
        pytest.skip('TG_BOT_TOKEN and TG_CHAT are not set')
    telegram = TelegramMessanger(telegram_token, telegram_chat_id)
    telegram.send_message('Test message')
