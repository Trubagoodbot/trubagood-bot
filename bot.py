import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
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

NAME, PHONE, ADDRESS, MEDIA, PROBLEM = range(5)

orders = {}


def get_price(problem_text):
    text = problem_text.lower()

    if "смеситель" in text:
        return "50–150€"
    if "унитаз" in text:
        return "70–160€"
    if "сифон" in text:
        return "50–100€"
    if "душ" in text:
        return "80–160€"
    if "радиатор" in text:
        return "90–180€"
    if "труба" in text or "протекает" in text or "течь" in text:
        return "60–120€"
    if "засор" in text or "канализац" in text:
        return "50–150€"

    return None


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=(
            "👀 Новый пользователь открыл бота\n\n"
            f"👤 Имя: {user.full_name}\n"
            f"🔗 Username: @{user.username if user.username else 'нет'}\n"
            f"🆔 ID: {user.id}"
        )
    )
    await update.message.reply_text(
        "👋 Добро пожаловать в TRUBAGOOD\n\n"
        "🔧 Сантехника и мелкий ремонт\n"
        "🚿 Смесители\n"
        "🚽 Унитазы\n"
        "🔥 Радиаторы\n"
        "🚰 Засоры\n"
        "🔩 Протечки\n\n"
        "📍 Работаем по Таллину\n"
        "⏰ Ежедневно 08:00–22:00\n\n"
        "Как вас зовут?"
    )
    return NAME


async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["name"] = update.message.text
    context.user_data["client_chat_id"] = update.effective_chat.id
    await update.message.reply_text("Введите ваш номер телефона 📞")
    return PHONE


async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["phone"] = update.message.text
    await update.message.reply_text("Введите адрес 📍")
    return ADDRESS


async def get_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["address"] = update.message.text
    await update.message.reply_text(
        "Пришлите фото или видео проблемы 📸\n"
        "Если фото/видео нет — напишите: нет"
    )
    return MEDIA


async def get_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["media_type"] = "none"
    context.user_data["media_file_id"] = None

    if update.message.photo:
        context.user_data["media_type"] = "photo"
        context.user_data["media_file_id"] = update.message.photo[-1].file_id
        await update.message.reply_text("Фото получил ✅\nТеперь опишите проблему 🔧")
        return PROBLEM

    if update.message.video:
        context.user_data["media_type"] = "video"
        context.user_data["media_file_id"] = update.message.video.file_id
        await update.message.reply_text("Видео получил ✅\nТеперь опишите проблему 🔧")
        return PROBLEM

    if update.message.text and update.message.text.lower() == "нет":
        await update.message.reply_text("Хорошо. Теперь опишите проблему 🔧")
        return PROBLEM

    await update.message.reply_text("Пришлите фото/видео или напишите: нет")
    return MEDIA


async def get_problem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    problem = update.message.text
    price = get_price(problem)
    order_id = str(update.effective_chat.id)

    orders[order_id] = {
        "client_chat_id": context.user_data["client_chat_id"],
        "accepted": False,
    }

    summary = (
        f"🆕 Новая заявка #{order_id}\n\n"
        f"👤 Имя: {context.user_data['name']}\n"
        f"📞 Телефон: {context.user_data['phone']}\n"
        f"📍 Адрес: {context.user_data['address']}\n"
        f"🔧 Проблема: {problem}\n"
        f"💰 Цена: {price if price else 'Уточняется'}"
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

    if price:
        await update.message.reply_text(
            f"✅ Заявка принята\n\n"
            f"💰 Предварительная стоимость: {price}\n\n"
            f"👨‍🔧 Ищем свободного мастера.\n"
            f"📞 После назначения мастер свяжется с вами для уточнения цены и времени.\n\n"
            f"⚠️ Финальная стоимость зависит от сложности работ."
        )
    else:
        await update.message.reply_text(
            "✅ Заявка принята\n\n"
            "👨‍🔧 Ищем свободного мастера.\n"
            "📞 Мастер свяжется с вами для уточнения цены и времени."
        )

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
    await update.message.reply_text("❌ Заявка отменена.")
    return ConversationHandler.END


app = ApplicationBuilder().token(TOKEN).build()

conv_handler = ConversationHandler(
    entry_points=[CommandHandler("start", start)],
    states={
        NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
        PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone)],
        ADDRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_address)],
        MEDIA: [MessageHandler((filters.PHOTO | filters.VIDEO | filters.TEXT) & ~filters.COMMAND, get_media)],
        PROBLEM: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_problem)],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)

app.add_handler(conv_handler)
app.add_handler(CallbackQueryHandler(accept_order))

print("Бот запущен...")
app.run_polling()