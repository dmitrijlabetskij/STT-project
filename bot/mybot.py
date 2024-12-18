from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackContext, CallbackQueryHandler, filters
import os
import logging
import asyncio
from main import Diarization

# Логирование
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# API-ключ
API_KEY = "8187193953:AAGKaLlqbUXqD7m_ZVf4en45t7Kv79vj4U0"
diarizator = None

async def start(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    message = f"Привет, {user.first_name}! Отправь голосовое сообщение либо файл в формате mp3!"
    keyboard = [[InlineKeyboardButton("Info", callback_data="button_click")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(message, reply_markup=reply_markup)

async def button(update: Update, context: CallbackContext) -> None:
    instructions = [
        "Инструкция по использованию бота:",
        "1. Отправьте голосовое сообщение или аудиофайл.",
        "2. Дождитесь завершения обработки.",
        "3. Получите результат в формате текста."
    ]
    await update.callback_query.answer()
    for line in instructions:
        await update.callback_query.message.reply_text(line)

async def handle_audio_message(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    file_name = f"{user.id}.mp3"
    txt_file = f"{user.id}.txt"

    try:
        await update.message.reply_text("Подождите, идёт обработка...")
        file = await context.bot.get_file(update.message.audio.file_id)
        await file.download_to_drive(file_name)
        await asyncio.to_thread(process_diarization, file_name)

        if os.path.exists(txt_file):
            with open(txt_file, 'r', encoding='utf-8') as doc:
                await context.bot.send_document(chat_id=update.effective_chat.id, document=doc)
    except Exception as e:
        logger.error(f"Ошибка обработки файла: {e}")
        await update.message.reply_text(f"Произошла ошибка: {e}")
    finally:
        for f in [file_name, txt_file]:
            if os.path.exists(f):
                os.remove(f)

def process_diarization(input_file):
    diarizator.run(input_file)

async def handle_other_messages(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text("Отправьте аудио для распознавания.")

def main():
    global diarizator
    diarizator = Diarization()
    application = Application.builder().token(API_KEY).read_timeout(30).write_timeout(600).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button, pattern="button_click"))
    application.add_handler(MessageHandler(filters.VOICE, handle_audio_message))
    application.add_handler(MessageHandler(filters.AUDIO, handle_audio_message))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_other_messages))
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
