# Cz Garant — сайт

Лендинг проекта + вход через Telegram Login Widget + форма связи с владельцами.

## Стек
FastAPI + Jinja2 (рендерятся вручную, без `Jinja2Templates`, чтобы обойти известный
баг совместимости версий starlette/jinja2) + чистый CSS без фреймворков.

## Как это работает

1. **Лендинг (`/`)** — карточки сервисов (`Czskambazabot`, `CzPiarbot`,
   `CzChatManagerbot`, `CzRevewsbot`), ссылки на чат и чат споров.
2. **Вход (`/login/callback`)** — Telegram Login Widget редиректит сюда с данными
   пользователя. `auth.py` проверяет подпись (`hash`) по алгоритму из
   [официальной документации Telegram](https://core.telegram.org/widgets/login#checking-authorization),
   отклоняет протухшие (>24ч) или подделанные данные. Валидный вход → подписанная
   cookie сессии (HMAC, без сторонних библиотек).
3. **Форма связи (`/contact`)** — доступна только вошедшим. Отправляет сообщение
   через Bot API (`sendMessage`) каждому ID из `ADMIN_IDS`.

## Обязательная настройка перед запуском

### 1. Бот для входа
Telegram Login Widget работает только с ботом, у которого указан домен сайта:
1. Напиши @BotFather → `/setdomain` → выбери бота (можно использовать существующего,
   например `@CzChatManagerbot`, или завести отдельного `CzSiteAuthBot`).
2. Укажи домен, на котором будет жить сайт (например `cz-garant.onrender.com` или
   свой домен).
3. Токен этого бота — `SITE_BOT_TOKEN`, его username (без `@`) — `SITE_BOT_USERNAME`.

### 2. Переменные окружения
```
SITE_BOT_TOKEN=...
SITE_BOT_USERNAME=CzChatManagerbot
ADMIN_IDS=8624551006,8434693684
SESSION_SECRET=сгенерируй-длинную-случайную-строку
PROJECT_CHAT=@chatnft2
DISPUTE_CHAT_URL=https://t.me/+ey0LUb6mMdk1OGQx
```

`SESSION_SECRET` — любая длинная случайная строка, отдельная от токена бота.
Например: `python3 -c "import secrets; print(secrets.token_hex(32))"`.

## Локальный запуск
```bash
pip install -r requirements.txt
export SITE_BOT_TOKEN=... SITE_BOT_USERNAME=... ADMIN_IDS=... SESSION_SECRET=...
python3 -m uvicorn main:app --reload --port 8000
```

## Деплой на Render
- Build command: `pip install -r requirements.txt`
- Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
- Переменные окружения — из раздела выше, в настройках Render Web Service.
- Не забудь после первого деплоя прогнать `/setdomain` в BotFather на реальный
  домен Render (или свой кастомный), иначе виджет логина будет молчать.

## Структура
```
main.py           — маршруты FastAPI
config.py         — переменные окружения
auth.py           — проверка Telegram Login + подпись сессионной cookie
templates/        — index.html, contact.html, base.html
static/css/       — style.css (тёмная тема, иридесцентный акцент)
```
