#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import logging
import tempfile
from pathlib import Path
import yt_dlp
import ffmpeg
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Директория для временных файлов
TEMP_DIR = Path(tempfile.gettempdir()) / "instagram_video_bot"
TEMP_DIR.mkdir(exist_ok=True)

# Конфигурация
class Config:
    TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "YOUR_TELEGRAM_BOT_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Отправляет приветственное сообщение при команде /start."""
    await update.message.reply_text(
        "Привет! Я бот для скачивания видео из Instagram.\n\n"
        "Просто отправь мне ссылку на видео из Instagram, и я скачаю его для тебя, "
        "а также отправлю аудио из этого видео и полное описание поста."
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Отправляет справочное сообщение при команде /help."""
    await update.message.reply_text(
        "Как использовать этого бота:\n\n"
        "1. Скопируйте ссылку на видео из Instagram\n"
        "2. Отправьте эту ссылку мне\n"
        "3. Дождитесь, пока я скачаю видео и извлеку аудио\n"
        "4. Получите видео, аудио и описание\n\n"
        "Поддерживаются ссылки на посты, reels и истории Instagram."
    )

def is_instagram_url(url: str) -> bool:
    """Проверяет, является ли URL ссылкой на Instagram."""
    return "instagram.com" in url or "instagr.am" in url

def download_instagram_video(url: str) -> tuple:
    """
    Скачивает видео из Instagram и извлекает описание.
    
    Возвращает кортеж (путь_к_видео, описание)
    """
    video_path = TEMP_DIR / f"{hash(url)}.mp4"
    
    ydl_opts = {
        'format': 'best',
        'outtmpl': str(video_path),
        'quiet': True,
        'no_warnings': True,
        'ignoreerrors': False,
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(url, download=True)
            description = info.get('description', 'Описание недоступно')
            return str(video_path), description
        except Exception as e:
            logger.error(f"Ошибка при скачивании видео: {e}")
            raise

def extract_audio(video_path: str) -> str:
    """
    Извлекает аудио из видео.
    
    Возвращает путь к аудиофайлу.
    """
    audio_path = str(Path(video_path).with_suffix('.mp3'))
    
    try:
        # Используем ffmpeg для извлечения аудио
        (
            ffmpeg
            .input(video_path)
            .output(audio_path, acodec='libmp3lame', q=4)
            .run(quiet=True, overwrite_output=True)
        )
        return audio_path
    except Exception as e:
        logger.error(f"Ошибка при извлечении аудио: {e}")
        raise

async def process_instagram_url(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает URL Instagram и отправляет видео, аудио и описание."""
    url = update.message.text.strip()
    
    if not is_instagram_url(url):
        await update.message.reply_text("Это не похоже на ссылку из Instagram. Пожалуйста, отправьте корректную ссылку.")
        return
    
    status_message = await update.message.reply_text("Скачиваю видео из Instagram...")
    
    try:
        # Скачиваем видео и получаем описание
        video_path, description = download_instagram_video(url)
        
        await status_message.edit_text("Извлекаю аудио из видео...")
        
        # Извлекаем аудио из видео
        audio_path = extract_audio(video_path)
        
        # Отправляем описание
        if description and description.strip():
            await update.message.reply_text(f"📝 Описание:\n\n{description}")
        else:
            await update.message.reply_text("📝 Описание отсутствует")
        
        # Отправляем видео
        await status_message.edit_text("Отправляю видео...")
        with open(video_path, 'rb') as video_file:
            await update.message.reply_video(
                video=video_file,
                caption="Вот ваше видео из Instagram"
            )
        
        # Отправляем аудио
        await status_message.edit_text("Отправляю аудио...")
        with open(audio_path, 'rb') as audio_file:
            await update.message.reply_audio(
                audio=audio_file,
                caption="Аудио из видео"
            )
        
        await status_message.delete()
        
        # Удаляем временные файлы
        os.remove(video_path)
        os.remove(audio_path)
        
    except Exception as e:
        logger.error(f"Ошибка при обработке URL: {e}")
        await status_message.edit_text(f"Произошла ошибка при обработке видео: {str(e)}")

def main() -> None:
    """Запускает бота."""
    # Создаем приложение и передаем ему токен бота
    application = Application.builder().token(Config.TOKEN).build()

    # Добавляем обработчики команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    
    # Добавляем обработчик для URL
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, process_instagram_url))

    # Запускаем бота
    application.run_polling()

if __name__ == '__main__':
    main()
