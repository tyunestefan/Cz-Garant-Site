import os


class Config:
    bot_token: str = os.getenv("SITE_BOT_TOKEN", "")
    bot_username: str = os.getenv("SITE_BOT_USERNAME", "")

    # Токен и БД чат-менеджера — нужны только для интеграции апелляций.
    chat_bot_token: str = os.getenv("CHAT_BOT_TOKEN", "")
    database_url: str = os.getenv("DATABASE_URL", "")

    admin_ids: list[int] = [
        int(x) for x in os.getenv("ADMIN_IDS", "8624551006,8434693684").split(",") if x
    ]

    session_secret: str = os.getenv("SESSION_SECRET", "change-me-in-production")

    project_chat: str = os.getenv("PROJECT_CHAT", "@chatnft2")
    dispute_chat_url: str = os.getenv("DISPUTE_CHAT_URL", "https://t.me/+ey0LUb6mMdk1OGQx")


config = Config()
