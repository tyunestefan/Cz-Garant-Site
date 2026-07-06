import hashlib
import hmac
import time
import json
import base64

from config import config


def verify_telegram_login(data: dict) -> bool:
    """
    Проверяет подлинность данных от Telegram Login Widget по алгоритму из
    официальной документации: https://core.telegram.org/widgets/login#checking-authorization

    data — это query-параметры, которые Telegram присылает на страницу после логина
    (id, first_name, username, photo_url, auth_date, hash, ...).
    """
    if "hash" not in data:
        return False

    received_hash = data["hash"]
    check_fields = {k: v for k, v in data.items() if k != "hash"}

    data_check_string = "\n".join(
        f"{k}={check_fields[k]}" for k in sorted(check_fields.keys())
    )

    secret_key = hashlib.sha256(config.bot_token.encode()).digest()
    computed_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

    if not hmac.compare_digest(computed_hash, received_hash):
        return False

    # auth_date не старше суток — защита от повторного использования старой ссылки
    auth_date = int(check_fields.get("auth_date", 0))
    if time.time() - auth_date > 86400:
        return False

    return True


def create_session_cookie(user: dict) -> str:
    """Простая подписанная cookie: base64(json) + HMAC подпись, без внешних зависимостей."""
    payload = json.dumps(user, separators=(",", ":")).encode()
    payload_b64 = base64.urlsafe_b64encode(payload).decode()
    sig = hmac.new(config.session_secret.encode(), payload_b64.encode(), hashlib.sha256).hexdigest()
    return f"{payload_b64}.{sig}"


def read_session_cookie(cookie_value: str | None) -> dict | None:
    if not cookie_value or "." not in cookie_value:
        return None

    payload_b64, sig = cookie_value.rsplit(".", 1)
    expected_sig = hmac.new(config.session_secret.encode(), payload_b64.encode(), hashlib.sha256).hexdigest()

    if not hmac.compare_digest(sig, expected_sig):
        return None

    try:
        payload = base64.urlsafe_b64decode(payload_b64.encode())
        return json.loads(payload)
    except Exception:
        return None
