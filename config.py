import os


class Config:
    # Токен бота, привязанного к домену сайта через @BotFather -> /setdomain.
    # Нужен и для проверки Telegram Login Widget, и для отправки сообщений
    # владельцам через форму связи.
    bot_token: str = os.getenv("SITE_BOT_TOKEN", "")
    bot_username: str = os.getenv("SITE_BOT_USERNAME", "")  # без @, для виджета логина

    admin_ids: list[int] = [
        int(x) for x in os.getenv("ADMIN_IDS", "8624551006,8434693684").split(",") if x
    ]

    # Секрет для подписи сессионной cookie (НЕ путать с bot_token)
    session_secret: str = os.getenv("SESSION_SECRET", "change-me-in-production")

    project_chat: str = os.getenv("PROJECT_CHAT", "@chatnft2")
    dispute_chat_url: str = os.getenv("DISPUTE_CHAT_URL", "https://t.me/+ey0LUb6mMdk1OGQx")


config = Config()
