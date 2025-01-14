from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackContext, CallbackQueryHandler, filters
import logging
import asyncio
import os
from main import Diarization
from collections import deque


class TelegramBot:
    def __init__(self, api_key):
        self.api_key = api_key
        self.diarizator = Diarization()
        self.queue = deque()

    def setup_logging(self):
        logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    async def start(self, update: Update, context: CallbackContext) -> None:
        user = update.effective_user
        message = f"Привет, {user.first_name}! Отправь голосовое сообщение"
        keyboard = [[InlineKeyboardButton("Info", callback_data="button_click")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(message, reply_markup=reply_markup)

    async def button(self, update: Update, context: CallbackContext) -> None:
        instructions = [
            "Инструкция по использованию бота:",
            "1. Отправьте голосовое сообщение или аудиофайл.",
            "2. Дождитесь завершения обработки.",
            "3. Получите результат в формате текста."
        ]
        await update.callback_query.answer()
        for line in instructions:
            await update.callback_query.message.reply_text(line)

    async def handle_audio_message(self, update: Update, context: CallbackContext) -> None:
        user_id = update.message.from_user.id
        self.queue.append(user_id)

        pos = len(self.queue)
        await update.message.reply_text(f"Подождите, идёт обработка...\nВаше место в очереди на обработку: {pos}")

        user = update.effective_user
        file_name = f"{user.id}.mp3"

        try:
            file = await context.bot.get_file(update.message.audio.file_id)
            await file.download_to_drive(custom_path=file_name)

            if not os.path.exists(file_name):
                raise FileNotFoundError(f"Файл {file_name} не найден после загрузки.")

            self.logger.info(f"Файл {file_name} успешно загружен.")

            # Запуск обработки
            asyncio.create_task(self.process_diarization_for_user(update, context, user_id, file_name))
            
        except Exception as e:
            self.logger.error(f"Ошибка обработки файла: {e}")
            await update.message.reply_text(f"Произошла ошибка: {e}")

    async def process_diarization_for_user(self, update: Update, context: CallbackContext, user_id: int, file_name: str):
        try:
            await asyncio.to_thread(self.process_diarization, file_name)
            txt_file = f"{os.path.splitext(file_name)[0]}.txt"
            
            if os.path.exists(txt_file):
            # Отправляем файл пользователю
                with open(txt_file, "rb") as result_file:
                    await context.bot.send_document(chat_id=update.message.chat_id, document=result_file, filename=os.path.basename(txt_file), caption="Результат обработки")
            else:
                # Если файл не найден, отправляем сообщение об ошибке
                await update.message.reply_text("Ошибка: результат обработки не найден.")
            
        except Exception as e:
            self.logger.error(f"Ошибка обработки файла: {e}")
            await update.message.reply_text(f"Произошла ошибка: {e}")
            
        finally:
            self.queue.remove(user_id)
            
            for f in [file_name, txt_file]:
                if os.path.exists(f):
                    os.remove(f)

    def process_diarization(self, audio):
        self.diarizator.run(audio)

    async def handle_other_messages(self, update: Update, context: CallbackContext) -> None:
        await update.message.reply_text("Отправьте аудио для распознавания.")

    def run(self):
        self.setup_logging()
        application = Application.builder().token(self.api_key).read_timeout(30).write_timeout(600).build()
        application.add_handler(CommandHandler("start", self.start))
        application.add_handler(CallbackQueryHandler(self.button, pattern="button_click"))
        application.add_handler(MessageHandler(filters.AUDIO, self.handle_audio_message))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_other_messages))
        application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    API_KEY = "8021952704:AAGyDAPS5NoNYuBl8WxEV41vulOG6AfisWg"
    bot = TelegramBot(API_KEY)
    bot.run()
    
