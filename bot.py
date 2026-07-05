import os
from texts import TEXTS

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

TOKEN = os.environ["BOT_TOKEN"]

ADMIN_ID = 408678786
GROUP_ID = -5213979113

LANGUAGE, NAME, PHONE, ADDRESS, MEDIA, PROBLEM = range(6)

orders = {}


def get_price(problem_text):
    text = problem_text.lower()

    if "смеситель" in text or "segisti" in text:
        return "50–150€"
    if "унитаз" in text or "wc" in text or "tualett" in text:
        return "70–160€"
    if "сифон" in text or "sifoon" in text:
        return "50–100€"
    if "душ" in text or "duš" in text:
        return "80–160€"
    if "радиатор" in text or "radiaator" in text:
        return "90–180€"
    if "труба" in text or "протекает" in text or "течь" in text or "toru" in text or "lekib" in text:
        return "60–120€"
    if "засор" in text or "канализац" in text or "ummistus" in text:
        return "50–150€"

    return None


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    source = context.args[0] if context.args else "unknown"
    context.user_data["source"] = source

    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=(
            "👀 Новый пользователь открыл бота\n\n"
            f"👤 Имя: {user.full_name}\n"
            f"🔗 Username: @{user.username if user.username else 'нет'}\n"
            f"🆔 ID: {user.id}\n"
            f"📍 Источник: {source}"
        )
    )

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru")],
        [InlineKeyboardButton("🇪🇪 Eesti", callback_data="lang_et")],
    ])

    await update.message.reply_text(
        "🌍 Valige keel / Выберите язык",
        reply_markup=keyboard
    )

    return LANGUAGE


async def choose_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    lang = query.data.replace("lang_", "")
    context.user_data["lang"] = lang

    await query.message.reply_text(TEXTS[lang]["language_selected"])
    await query.message.reply_text(TEXTS[lang]["welcome"])

    return NAME


async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get("lang", "ru")

    context.user_data["name"] = update.message.text
    context.user_data["client_chat_id"] = update.effective_chat.id

    await update.message.reply_text(TEXTS[lang]["ask_phone"])

    return PHONE


async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get("lang", "ru")

    context.user_data["phone"] = update.message.text

    await update.message.reply_text(TEXTS[lang]["ask_address"])

    return ADDRESS


async def get_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get("lang", "ru")

    context.user_data["address"] = update.message.text

    await update.message.reply_text(TEXTS[lang]["ask_media"])

    return MEDIA


async def get_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get("lang", "ru")

    context.user_data["media_type"] = "none"
    context.user_data["media_file_id"] = None

    if update.message.photo:
        context.user_data["media_type"] = "photo"
        context.user_data["media_file_id"] = update.message.photo[-1].file_id
        await update.message.reply_text(TEXTS[lang]["media_received_photo"])
        return PROBLEM

    if update.message.video:
        context.user_data["media_type"] = "video"
        context.user_data["media_file_id"] = update.message.video.file_id
        await update.message.reply_text(TEXTS[lang]["media_received_video"])
        return PROBLEM

    if update.message.text:
        text = update.message.text.lower()
        if text in ["нет", "ei", "no"]:
            await update.message.reply_text(TEXTS[lang]["media_skip"])
            return PROBLEM

    await update.message.reply_text(TEXTS[lang]["media_wrong"])

    return MEDIA


async def get_problem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get("lang", "ru")

    problem = update.message.text
    price = get_price(problem)
    order_id = str(update.effective_chat.id)

    orders[order_id] = {
        "client_chat_id": context.user_data["client_chat_id"],
        "accepted": False,
    }

    summary = (
        f"🆕 Новая заявка #{order_id}\n\n"
        f"🌍 Язык: {lang}\n"
        f"📍 Источник: {context.user_data.get('source', 'unknown')}\n\n"
        f"👤 Имя: {context.user_data['name']}\n"
        f"📞 Телефон: {context.user_data['phone']}\n"
        f"📍 Адрес: {context.user_data['address']}\n"
        f"🔧 Проблема: {problem}\n"
        f"💰 Цена: {price if price else 'Требуется ручная оценка мастера'}"
    )

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Принять заявку", callback_data=f"accept_{order_id}")]
    ])

    await context.bot.send_message(chat_id=ADMIN_ID, text=summary)
    await context.bot.send_message(chat_id=GROUP_ID, text=summary, reply_markup=keyboard)

    if context.user_data["media_type"] == "photo":
        await context.bot.send_photo(chat_id=ADMIN_ID, photo=context.user_data["media_file_id"])
        await context.bot.send_photo(chat_id=GROUP_ID, photo=context.user_data["media_file_id"])

    if context.user_data["media_type"] == "video":
        await context.bot.send_video(chat_id=ADMIN_ID, video=context.user_data["media_file_id"])
        await context.bot.send_video(chat_id=GROUP_ID, video=context.user_data["media_file_id"])

    if lang == "et":
        if price:
            client_message = (
                "✅ Taotlus on saadetud\n\n"
                f"💰 Esialgne hind: {price}\n\n"
                "👨‍🔧 Meister vaatab info üle ja võtab teiega ühendust.\n\n"
                "⚠️ Lõplik hind sõltub töö keerukusest."
            )
        else:
            client_message = (
                "✅ Taotlus on saadetud\n\n"
                "👨‍🔧 Meister vaatab info üle ja arvutab vajadusel esialgse hinna.\n"
                "📞 Seejärel võtab meister teiega ühendust."
            )
    else:
        if price:
            client_message = (
                "✅ Заявка отправлена\n\n"
                f"💰 Предварительная стоимость: {price}\n\n"
                "👨‍🔧 Мастер посмотрит информацию и свяжется с вами.\n\n"
                "⚠️ Финальная стоимость зависит от сложности работ."
            )
        else:
            client_message = (
                "✅ Заявка отправлена\n\n"
                "👨‍🔧 Мастер посмотрит информацию и рассчитает предварительную цену.\n"
                "📞 После этого мастер свяжется с вами."
            )

    await update.message.reply_text(client_message)

    return ConversationHandler.END


async def accept_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    order_id = query.data.replace("accept_", "")

    if order_id not in orders:
        await query.message.reply_text("Заявка не найдена. Возможно, бот был перезапущен.")
        return

    if orders[order_id]["accepted"]:
        await query.message.reply_text("❌ Эта заявка уже принята другим мастером.")
        return

    orders[order_id]["accepted"] = True
    master_name = query.from_user.full_name

    await query.message.reply_text(f"✅ Заявку принял мастер: {master_name}")

    await context.bot.send_message(
        chat_id=orders[order_id]["client_chat_id"],
        text=(
            "✅ Мастер найден\n\n"
            f"👨‍🔧 Мастер: {master_name}\n"
            "📞 Мастер свяжется с вами для уточнения цены и времени."
        )
    )

    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"✅ Заявку #{order_id} принял мастер: {master_name}"
    )


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get("lang", "ru")

    if lang == "et":
        await update.message.reply_text("❌ Taotlus on tühistatud.")
    else:
        await update.message.reply_text("❌ Заявка отменена.")

    return ConversationHandler.END


app = ApplicationBuilder().token(TOKEN).build()

conv_handler = ConversationHandler(
    entry_points=[CommandHandler("start", start)],
    states={
        LANGUAGE: [CallbackQueryHandler(choose_language, pattern="^lang_")],
        NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
        PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone)],
        ADDRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_address)],
        MEDIA: [MessageHandler((filters.PHOTO | filters.VIDEO | filters.TEXT) & ~filters.COMMAND, get_media)],
        PROBLEM: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_problem)],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)

app.add_handler(conv_handler)
app.add_handler(CallbackQueryHandler(accept_order, pattern="^accept_"))

print("Бот запущен...")
app.run_polling()