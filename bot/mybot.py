from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackContext, CallbackQueryHandler, filters
import logging
import asyncio
import os
from main import Diarization
from collections import deque
import uuid
import subprocess


class TelegramBot:
    def __init__(self, api_key):
        self.api_key = api_key
        self.diarizator = Diarization()
        self.queue = deque()  # Очередь для обработки пользователей
        self.lock = asyncio.Lock()  # Мьютекс для синхронизации обработки файлов

    def setup_logging(self):
        logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    async def start(self, update: Update, context: CallbackContext) -> None:
        user = update.effective_user
        message = f"Привет, {user.first_name}! Отправь голосовое или mp3."
        keyboard = [[InlineKeyboardButton("Info", callback_data="button_click")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(message, reply_markup=reply_markup)

    async def button(self, update: Update, context: CallbackContext) -> None:
        instructions = [
            "Инструкция по использованию бота:",
            "1. Отправьте аудиофайл или голосовое сообщение.",
            "2. Дождитесь завершения обработки.",
            "3. Получите результат в формате текста."
        ]
        await update.callback_query.answer()
        for line in instructions:
            await update.callback_query.message.reply_text(line)

    async def handle_audio_message(self, update: Update, context: CallbackContext) -> None:
        user_id = update.message.from_user.id
        
        # Добавляем пользователя в очередь и сразу выводим его позицию
        self.queue.append(user_id)

        # Отправляем пользователю его место в очереди
        pos = len(self.queue)
        await update.message.reply_text(f"Подождите, идёт обработка...\nВаше место в очереди на обработку: {pos}")

        # После этого запускаем фоновую задачу для обработки аудио
        user = update.effective_user
        unique_id = str(uuid.uuid4())  # Генерируем уникальный ID
        file_name = f"{user.id}_{unique_id}.mp3"

        # Запускаем обработку в фоновом потоке
        asyncio.create_task(self.process_audio(update, context, user_id, file_name))  # Передаем все аргументы
        
    async def handle_voice_message(self, update: Update, context: CallbackContext) -> None:
        user_id = update.message.from_user.id
        
        # Добавляем пользователя в очередь и сразу выводим его позицию
        self.queue.append(user_id)

        # Отправляем пользователю его место в очереди
        pos = len(self.queue)
        await update.message.reply_text(f"Подождите, идёт обработка...\nВаше место в очереди на обработку: {pos}")

        # После этого запускаем фоновую задачу для обработки аудио
        user = update.effective_user
        unique_id = str(uuid.uuid4())  # Генерируем уникальный ID
        file_name = f"{user.id}_{unique_id}.ogg"

        # Запускаем обработку в фоновом потоке
        asyncio.create_task(self.process_voice(update, context, user_id, file_name))  # Передаем все аргументы
        
    def convert_to_mp3(self, input, output):
        """Конвертирует OGG (Opus) в MP3 с помощью ffmpeg."""
        command = ["ffmpeg", "-i", input, "-acodec", "libmp3lame", output]
        subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    async def process_audio(self, update: Update, context: CallbackContext, user_id: int, file_name: str):
        try:
            # Загрузка файла
            if update.message.audio:
                file_id = update.message.audio.file_id
            else:
                await update.message.reply_text("Ошибка: отправьте голосовое или аудиофайл.")
                return
            file_id = update.message.audio.file_id or update.message.voice.file_id
            file = await context.bot.get_file(file_id)
            await file.download_to_drive(custom_path=file_name)

            if not os.path.exists(file_name):
                raise FileNotFoundError(f"Файл {file_name} не найден после загрузки.")

            self.logger.info(f"Файл {file_name} успешно загружен.")

            # Запуск обработки в отдельном потоке
            await self.process_diarization_for_user(update, context, user_id, file_name)

        except Exception as e:
            self.logger.error(f"Ошибка обработки файла: {e}")
            await update.message.reply_text(f"Произошла ошибка: {e}")
            
    async def process_voice(self, update: Update, context: CallbackContext, user_id: int, file_name: str):
        try:
            # Загрузка файла
            if update.message.voice:
                file_id = update.message.voice.file_id
            else:
                await update.message.reply_text("Ошибка: отправьте голосовое или аудиофайл.")
                return
            file = await context.bot.get_file(file_id)
            await file.download_to_drive(custom_path=file_name)

            if not os.path.exists(file_name):
                raise FileNotFoundError(f"Файл {file_name} не найден после загрузки.")

            self.logger.info(f"Файл {file_name} успешно загружен.")

            # Запуск обработки в отдельном потоке
            new_file_name = file_name.split('.')[0] + '.mp3'
            self.convert_to_mp3(file_name, new_file_name)
            os.remove(file_name)
            await self.process_diarization_for_user(update, context, user_id, new_file_name)

        except Exception as e:
            self.logger.error(f"Ошибка обработки файла: {e}")
            await update.message.reply_text(f"Произошла ошибка: {e}")

    async def process_diarization_for_user(self, update: Update, context: CallbackContext, user_id: int, file_name: str):
        # Входим в блокировку, чтобы только один файл обрабатывался в момент времени
        async with self.lock:
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
                # Удаляем пользователя из очереди после завершения обработки
                self.queue.remove(user_id)
                
                # Удаление временных файлов
                for f in [file_name, txt_file]:
                    if os.path.exists(f):
                        os.remove(f)

        # Обработаем следующего пользователя в очереди
        await self.process_next_in_queue()

    def process_diarization(self, audio):
        self.diarizator.run(audio)

    async def process_next_in_queue(self):
        # Проверяем, есть ли еще файлы в очереди, которые нужно обработать
        if self.queue:
            # Получаем следующего пользователя из очереди
            next_user_id = self.queue[0]
            # Здесь нужно будет обработать файл следующего пользователя
            # Примерно так:
            user = await self.get_user_by_id(next_user_id)
            try:
                await self.handle_audio_message(user)
            except TypeError:
                pass

    async def handle_other_messages(self, update: Update, context: CallbackContext) -> None:
        await update.message.reply_text("Отправьте аудио для распознавания.")
        
    async def handle_voice(self, update: Update, context: CallbackContext):
        try:
            '''
            user = update.effective_user
            file_name = f"{user.id}.ogg"
            # Загрузка файла
            file_id = update.message.audio.file_id or update.message.voice.file_id
            file = await context.bot.get_file(file_id)
            await file.download_to_drive(custom_path=file_name)'''
            logging.info(update.message)
        except Exception as e:
            self.logger.error(f"Ошибка обработки файла: {e}")

    async def get_user_by_id(self, user_id: int):
        # Получаем пользователя по ID, это пример. Нужно будет связать его с соответствующими данными.
        return user_id

    def run(self):
        self.setup_logging()
        application = Application.builder().token(self.api_key).read_timeout(30).write_timeout(1000).build()
        application.add_handler(CommandHandler("start", self.start))
        application.add_handler(CallbackQueryHandler(self.button, pattern="button_click"))
        application.add_handler(MessageHandler(filters.AUDIO, self.handle_audio_message))
        application.add_handler(MessageHandler(filters.VOICE, self.handle_voice_message))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_other_messages))
        application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    API_KEY = "8021952704:AAGyDAPS5NoNYuBl8WxEV41vulOG6AfisWg"
    bot = TelegramBot(API_KEY)
    bot.run()
