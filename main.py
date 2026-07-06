import httpx
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from jinja2 import Environment, FileSystemLoader, select_autoescape

from config import config
from auth import verify_telegram_login, create_session_cookie, read_session_cookie

app = FastAPI(title="Cz Garant")
app.mount("/static", StaticFiles(directory="static"), name="static")

jinja_env = Environment(
    loader=FileSystemLoader("templates"),
    autoescape=select_autoescape(["html"]),
)


def render(template_name: str, **context) -> HTMLResponse:
    template = jinja_env.get_template(template_name)
    return HTMLResponse(template.render(**context))

SERVICES = [
    {
        "name": "Скам-база",
        "bot": "@Czskambazabot",
        "description": "Проверка пользователей по базе недобросовестных участников — по ID или юзернейму.",
    },
    {
        "name": "Пиар-бот",
        "bot": "@CzPiarbot",
        "description": "Покупка обязательной подписки (ОП) на определённое количество часов для продвижения.",
    },
    {
        "name": "Чат-менеджер",
        "bot": "@CzChatManagerbot",
        "description": "Модерация чата сообщества: правила, автоответы, служебные функции.",
    },
    {
        "name": "Отзывы",
        "bot": "@CzRevewsbot",
        "description": "Оставляйте отзывы о сделках и участниках проекта по именному ключу-приглашению.",
    },
]


def get_current_user(request: Request) -> dict | None:
    return read_session_cookie(request.cookies.get("cz_session"))


@app.get("/health")
async def health():
    """Лёгкий эндпоинт для внешнего пинга (FastCron/UptimeRobot), чтобы не давать
    Render усыплять сервис на бесплатном тарифе. Никакого рендеринга шаблонов —
    просто мгновенный ответ."""
    return {"status": "ok"}


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    user = get_current_user(request)
    return render(
        "index.html",
        request=request,
        services=SERVICES,
        project_chat=config.project_chat,
        dispute_chat_url=config.dispute_chat_url,
        bot_username=config.bot_username,
        user=user,
    )


@app.get("/login/callback")
async def telegram_login_callback(request: Request):
    """Telegram Login Widget редиректит сюда с данными пользователя в query-параметрах."""
    params = dict(request.query_params)

    if not verify_telegram_login(params):
        return RedirectResponse("/?login_error=1")

    user = {
        "id": params.get("id"),
        "first_name": params.get("first_name"),
        "username": params.get("username"),
        "photo_url": params.get("photo_url"),
    }

    response = RedirectResponse("/contact")
    response.set_cookie(
        "cz_session",
        create_session_cookie(user),
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=7 * 24 * 3600,
    )
    return response


@app.get("/logout")
async def logout():
    response = RedirectResponse("/")
    response.delete_cookie("cz_session")
    return response


@app.get("/contact", response_class=HTMLResponse)
async def contact_page(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse("/")
    return render("contact.html", request=request, user=user, bot_username=config.bot_username)


@app.post("/contact")
async def contact_submit(request: Request, message: str = Form(...)):
    user = get_current_user(request)
    if not user:
        return RedirectResponse("/", status_code=303)

    text = (
        f"📩 <b>Новое сообщение с сайта Cz Garant</b>\n\n"
        f"👤 От: {user.get('first_name', '')} (@{user.get('username') or 'без username'})\n"
        f"🆔 Telegram ID: <code>{user.get('id')}</code>\n\n"
        f"💬 {message}"
    )

    async with httpx.AsyncClient(timeout=10) as client:
        for admin_id in config.admin_ids:
            try:
                await client.post(
                    f"https://api.telegram.org/bot{config.bot_token}/sendMessage",
                    json={"chat_id": admin_id, "text": text, "parse_mode": "HTML"},
                )
            except Exception:
                pass  # не роняем запрос пользователя из-за одного неотправленного уведомления

    return render(
        "contact.html",
        request=request,
        user=user,
        bot_username=config.bot_username,
        sent=True,
    )
