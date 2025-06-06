#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Точка входа для Vercel - обработка webhook-запросов от Telegram.
"""

import os
import json
import logging
from fastapi import FastAPI, Request, Response
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
import sys
sys.path.append("..")  # Добавляем родительскую директорию в путь
from src.bot import start, help_command, process_instagram_url

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Создаем FastAPI приложение
app = FastAPI()

# Конфигурация
class Config:
    TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "YOUR_TELEGRAM_BOT_TOKEN")
    WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "")  # URL вашего Vercel деплоя

# Создаем приложение Telegram
application = Application.builder().token(Config.TOKEN).build()

# Добавляем обработчики команд
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("help", help_command))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, process_instagram_url))

@app.post("/api/webhook")
async def webhook(request: Request):
    """Обработчик webhook-запросов от Telegram."""
    try:
        # Получаем данные запроса
        data = await request.json()
        logger.info(f"Получен webhook: {data}")
        
        # Преобразуем данные в объект Update
        update = Update.de_json(data, application.bot)
        
        # Обрабатываем обновление
        await application.process_update(update)
        
        return Response(content="OK", status_code=200)
    except Exception as e:
        logger.error(f"Ошибка при обработке webhook: {e}")
        return Response(content=str(e), status_code=500)

@app.get("/api/set_webhook")
async def set_webhook():
    """Устанавливает webhook для бота."""
    if not Config.WEBHOOK_URL:
        return {"success": False, "error": "WEBHOOK_URL не установлен в переменных окружения"}
    
    webhook_url = f"{Config.WEBHOOK_URL}/api/webhook"
    
    try:
        await application.bot.set_webhook(url=webhook_url)
        webhook_info = await application.bot.get_webhook_info()
        
        return {
            "success": True,
            "webhook_url": webhook_url,
            "webhook_info": {
                "url": webhook_info.url,
                "has_custom_certificate": webhook_info.has_custom_certificate,
                "pending_update_count": webhook_info.pending_update_count,
                "last_error_date": webhook_info.last_error_date,
                "last_error_message": webhook_info.last_error_message
            }
        }
    except Exception as e:
        logger.error(f"Ошибка при установке webhook: {e}")
        return {"success": False, "error": str(e)}

@app.get("/api/health")
async def health_check():
    """Проверка работоспособности."""
    return {"status": "ok", "bot_info": await application.bot.get_me()}

@app.get("/")
async def root():
    """Корневой маршрут."""
    return {"message": "Instagram Video Bot API работает. Используйте /api/set_webhook для настройки webhook."}
