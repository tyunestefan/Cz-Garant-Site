import html
import httpx
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from jinja2 import Environment, FileSystemLoader, select_autoescape

from config import config
from auth import verify_telegram_login, create_session_cookie, read_session_cookie

try:
    import asyncpg
except ImportError:  # библиотека нужна только для интеграции апелляций
    asyncpg = None

app = FastAPI(title="Cz Garant")
app.mount("/static", StaticFiles(directory="static"), name="static")

jinja_env = Environment(
    loader=FileSystemLoader("templates"),
    autoescape=select_autoescape(["html"]),
)

APPEAL_MAX_LEN = 1000
db_pool = None


def render(template_name: str, **context) -> HTMLResponse:
    template = jinja_env.get_template(template_name)
    return HTMLResponse(template.render(**context))


@app.on_event("startup")
async def on_startup():
    global db_pool
    if asyncpg and config.database_url:
        try:
            db_pool = await asyncpg.create_pool(config.database_url, min_size=1, max_size=3)
        except Exception:
            db_pool = None


@app.on_event("shutdown")
async def on_shutdown():
    if db_pool:
        await db_pool.close()


# ---------- ДАННЫЕ ПРОЕКТА ----------

SERVICES = [
    {
        "slug": "scam-base",
        "name": "Скам-база",
        "bot": "@Czskambazabot",
        "logo": "/static/img/logo-scambase.png",
        "description": "Проверка пользователей по базе недобросовестных участников — по ID или юзернейму.",
        "long_description": (
            "Скам-база хранит записи о недобросовестных участниках по числовому "
            "Telegram ID — надёжнее username, потому что ник можно сменить, "
            "а ID остаётся неизменным. Проверить контрагента перед сделкой можно "
            "прямо в боте: достаточно прислать ID, и бот "
            "проверит его по базе."
        ),
    },
    {
        "slug": "piar",
        "name": "Пиар-бот",
        "bot": "@CzPiarbot",
        "logo": "/static/img/logo-piar.png",
        "description": "Покупка обязательной подписки (ОП) на определённое количество часов для продвижения.",
        "long_description": (
            "Пиар-бот позволяет купить обязательную подписку (ОП) на ваш канал "
            "или чат на заданное количество часов — простой способ продвинуть "
            "проект внутри сообщества Cz Garant."
        ),
    },
    {
        "slug": "chat-manager",
        "name": "Чат-менеджер",
        "bot": "@CzChatManagerbot",
        "logo": "/static/img/logo-chatmanager.png",
        "description": "Модерация чата сообщества: правила, автоответы, служебные функции.",
        "long_description": (
            "Чат-менеджер следит за порядком в чате Cz Garant: применяет "
            "наказания согласно правилам, обрабатывает вызовы гаранта и жалобы, "
            "отвечает на служебные команды. Полный список правил — на странице "
            "«Правила»."
        ),
    },
    {
        "slug": "reviews",
        "name": "Отзывы",
        "bot": "@CzReviewsbot",
        "logo": "/static/img/logo-reviews.png",
        "description": "Оставляйте отзывы о сделках и участниках проекта по именному ключу-приглашению.",
        "long_description": (
            "Бот отзывов позволяет оставить именной отзыв о сделке "
            "по ключу-приглашению, который выдаёт администрация. Отзыв "
            "попадает в публичную историю."
        ),
    },
]

SERVICES_BY_SLUG = {s["slug"]: s for s in SERVICES}

TEAM = [
    {"role": "Владельцы", "members": ["@mrtley", "@Timmy_Falcon"]},
    {"role": "Гаранты", "members": ["@mrtley", "@Timmy_Falcon"]},
    {"role": "Модераторы", "members": ["@NOFIK_Top"]},
]

RULES = [
    {"violation": "Спам", "punishment": "🔇 Мут 5 дней"},
    {"violation": "Оскорбление админов / владельца", "punishment": "🔇 Мут 1 день"},
    {"violation": "Краш-стикеры", "punishment": "🔇 Мут 1 неделю"},
    {"violation": "18+, нацизм, фашизм и т.п.", "punishment": "🔇 Мут 1 день"},
    {"violation": "Оскорбление участников", "punishment": "🔇 Мут 1 час"},
    {"violation": "Расчленёнка", "punishment": "🔇 Мут 1 неделю"},
    {"violation": "Скам", "punishment": "🚫 Бан навсегда"},
    {"violation": "Реклама", "punishment": "🔇 Мут 1 неделю"},
    {"violation": "Клевета на админа / владельца", "punishment": "🔇 Мут 1 день"},
]

FAQ = [
    {
        "q": "Что такое Cz Garant?",
        "a": "Экосистема сервисов для безопасных сделок в Telegram: проверка репутации участников, фиксация условий сделки и разрешение спорных ситуаций без опоры на личное доверие.",
    },
    {
        "q": "Кто такой гарант в этой системе?",
        "a": "Гарант — независимая сторона при сделках и конфликтах: фиксирует условия взаимодействия, следит за выполнением обязательств и помогает разрешать споры на основе фактов из переписки, а не эмоций.",
    },
    {
        "q": "Безопасно ли проводить сделки через гарантов?",
        "a": "Да, абсолютно безопасно. Гарант сопровождает сделку от начала до конца и следит за соблюдением договорённостей — вам не о чем переживать.",
    },
    {
        "q": "Какая комиссия за сделки через гаранта?",
        "a": "Комиссия зависит от суммы сделки: до 1 000 ₽ — без комиссии, от 1 000 до 10 000 ₽ — 2%, свыше 10 000 ₽ — 3%.",
    },
    {
        "q": "Как проверить пользователя перед сделкой?",
        "a": "Напишите его ID или username боту @Czskambazabot — он сверит по скам-базе и пришлёт результат.",
    },
    {
        "q": "Как позвать гаранта для сделки?",
        "a": "Сделайте reply на сообщение участника командой /адм с указанием предмета сделки и суммы. У обоих участников должен быть запущен бот.",
    },
    {
        "q": "Что делать, если меня замутили или забанили по ошибке?",
        "a": "Подайте апелляцию прямо на сайте (кнопка «Подать апелляцию» в личном кабинете) или напишите боту в личные сообщения и нажмите «Подать апелляцию» там.",
    },
    {
        "q": "Как оставить отзыв о сделке?",
        "a": "Через бота @CzReviewsbot по именному ключу-приглашению, который выдаёт администрация.",
    },
    {
        "q": "Данные из скам-базы привязаны к username или к ID?",
        "a": "К числовому Telegram ID — это надёжнее, так как username можно сменить, а ID остаётся неизменным.",
    },
    {
        "q": "Кто создал сайт?",
        "a": "Сайт создан и поддерживается @mrtley.",
    },
]


# ---------- ВСПОМОГАТЕЛЬНОЕ ----------

def get_current_user(request: Request) -> dict | None:
    return read_session_cookie(request.cookies.get("cz_session"))


def base_context(request: Request, user: dict | None) -> dict:
    return {
        "request": request,
        "dispute_chat_url": config.dispute_chat_url,
        "bot_username": config.bot_username,
        "user": user,
    }


def esc(text: str) -> str:
    return html.escape(text or "")


# ---------- МАРШРУТЫ ----------

@app.get("/health")
async def health():
    """Лёгкий эндпоинт для внешнего пинга (FastCron/UptimeRobot)."""
    return {"status": "ok"}


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    user = get_current_user(request)
    return render(
        "index.html",
        **base_context(request, user),
        services=SERVICES,
        project_chat=config.project_chat,
    )


@app.get("/about", response_class=HTMLResponse)
async def about(request: Request):
    user = get_current_user(request)
    return render("about.html", **base_context(request, user))


@app.get("/services", response_class=HTMLResponse)
async def services_list(request: Request):
    user = get_current_user(request)
    return render("services_list.html", **base_context(request, user), services=SERVICES)


@app.get("/services/{slug}", response_class=HTMLResponse)
async def service_detail(request: Request, slug: str):
    user = get_current_user(request)
    service = SERVICES_BY_SLUG.get(slug)
    if not service:
        return RedirectResponse("/services")
    return render("service_detail.html", **base_context(request, user), service=service)


@app.get("/team", response_class=HTMLResponse)
async def team(request: Request):
    user = get_current_user(request)
    return render("team.html", **base_context(request, user), team=TEAM)


@app.get("/rules", response_class=HTMLResponse)
async def rules(request: Request):
    user = get_current_user(request)
    return render("rules.html", **base_context(request, user), rules=RULES)


@app.get("/faq", response_class=HTMLResponse)
async def faq(request: Request):
    user = get_current_user(request)
    return render("faq.html", **base_context(request, user), faq=FAQ)


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

    response = RedirectResponse("/dashboard")
    response.set_cookie(
        "cz_session",
        create_session_cookie(user),
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=7 * 24 * 3600,  # 7 дней
    )
    return response


@app.get("/logout")
async def logout():
    response = RedirectResponse("/")
    response.delete_cookie("cz_session")
    return response


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    user = get_current_user(request)
    if not user:
        return render("login_required.html", **base_context(request, user))
    return render("dashboard.html", **base_context(request, user))


@app.get("/contact", response_class=HTMLResponse)
async def contact_page(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse("/")
    return render("contact.html", **base_context(request, user))


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
                pass

    return render("dashboard.html", **base_context(request, user), sent=True)


# ---------- АПЕЛЛЯЦИИ (интеграция с ботом-чат-менеджером) ----------

@app.get("/appeal", response_class=HTMLResponse)
async def appeal_form(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse("/")
    return render("appeal.html", **base_context(request, user), max_len=APPEAL_MAX_LEN)


@app.post("/appeal")
async def appeal_submit(request: Request, text: str = Form(...)):
    user = get_current_user(request)
    if not user:
        return RedirectResponse("/", status_code=303)

    appeal_text = (text or "").strip()[:APPEAL_MAX_LEN]
    if not appeal_text:
        return render(
            "appeal.html", **base_context(request, user),
            max_len=APPEAL_MAX_LEN, error="Введите текст апелляции.",
        )

    if not db_pool or not config.chat_bot_token:
        return render(
            "appeal.html", **base_context(request, user),
            max_len=APPEAL_MAX_LEN,
            error="Приём апелляций временно недоступен. Напишите боту в личные сообщения.",
        )

    user_id = int(user["id"])
    username = user.get("username") or ""

    async with db_pool.acquire() as c:
        appeal_id = await c.fetchval(
            "INSERT INTO appeals (user_id, username, text) VALUES ($1, $2, $3) RETURNING id",
            user_id, username, appeal_text,
        )
        last = await c.fetchrow(
            "SELECT action, chat_id, reason, ts FROM action_logs "
            "WHERE target_id=$1 AND action NOT ILIKE 'APPEAL_%' "
            "AND (action ILIKE '%MUTE%' OR action ILIKE '%BAN%' OR action IN ('MUTE','BAN')) "
            "ORDER BY ts DESC LIMIT 1",
            user_id,
        )

    is_ban = bool(last) and "BAN" in last["action"]
    is_mute = bool(last) and "MUTE" in last["action"]

    keyboard_buttons = []
    if is_ban:
        keyboard_buttons = [[
            {"text": "✅ Разбанить", "callback_data": f"appeal_unban:{appeal_id}"},
            {"text": "🚫 Оставить в бане", "callback_data": f"appeal_keep:{appeal_id}"},
        ]]
    elif is_mute:
        keyboard_buttons = [[
            {"text": "✅ Размьютить", "callback_data": f"appeal_unmute:{appeal_id}"},
            {"text": "🔇 Оставить в мьюте", "callback_data": f"appeal_keep:{appeal_id}"},
        ]]

    notify_text = (
        f"🧾 <b>Новая апелляция #{appeal_id}</b> (с сайта)\n\n"
        f"👤 От: {esc(user.get('first_name', ''))} (@{esc(username) or 'без username'})\n"
        f"🆔 Telegram ID: <code>{user_id}</code>\n\n"
        f"<b>Текст апелляции:</b>\n<blockquote>{esc(appeal_text)}</blockquote>"
    )

    async with httpx.AsyncClient(timeout=10) as client:
        for admin_id in config.admin_ids:
            try:
                payload = {"chat_id": admin_id, "text": notify_text, "parse_mode": "HTML"}
                if keyboard_buttons:
                    payload["reply_markup"] = {"inline_keyboard": keyboard_buttons}
                await client.post(
                    f"https://api.telegram.org/bot{config.chat_bot_token}/sendMessage",
                    json=payload,
                )
            except Exception:
                pass

    return render(
        "appeal.html", **base_context(request, user),
        max_len=APPEAL_MAX_LEN, sent=True,
    )
