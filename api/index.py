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
import asyncio

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
    WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "")

# Создаем и настраиваем приложение Telegram при первом запросе
_application = None

async def get_application():
    """Создает и возвращает экземпляр Application с ленивой инициализацией"""
    global _application
    if _application is None:
        _application = Application.builder().token(Config.TOKEN).build()
        
        # Добавляем обработчики команд
        _application.add_handler(CommandHandler("start", start))
        _application.add_handler(CommandHandler("help", help_command))
        _application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, process_instagram_url))
        
        # Инициализируем приложение
        await _application.initialize()
    
    return _application

@app.post("/api/webhook")
async def webhook(request: Request):
    """Обработчик webhook-запросов от Telegram."""
    try:
        application = await get_application()
        data = await request.json()
        logger.info(f"Получен webhook: {data}")
        
        update = Update.de_json(data, application.bot)
        await application.process_update(update)
        
        return Response(content="OK", status_code=200)
    except Exception as e:
        logger.error(f"Ошибка при обработке webhook: {e}", exc_info=True)
        return Response(content=str(e), status_code=500)

@app.get("/api/set_webhook")
async def set_webhook():
    """Устанавливает webhook для бота."""
    if not Config.WEBHOOK_URL:
        return {"success": False, "error": "WEBHOOK_URL не установлен в переменных окружения"}
    
    try:
        application = await get_application()
        webhook_url = f"{Config.WEBHOOK_URL}/api/webhook"
        
        await application.bot.set_webhook(url=webhook_url)
        webhook_info = await application.bot.get_webhook_info()
        
        return {
            "success": True,
            "webhook_url": webhook_url,
            "webhook_info": webhook_info.to_dict()
        }
    except Exception as e:
        logger.error(f"Ошибка при установке webhook: {e}", exc_info=True)
        return {"success": False, "error": str(e)}

@app.get("/api/health")
async def health_check():
    """Проверка работоспособности."""
    try:
        application = await get_application()
        return {
            "status": "ok",
            "bot_info": (await application.bot.get_me()).to_dict()
        }
    except Exception as e:
        logger.error(f"Ошибка health check: {e}", exc_info=True)
        return {"status": "error", "error": str(e)}

@app.get("/")
async def root():
    """Корневой маршрут."""
    return {"message": "Instagram Video Bot API работает. Используйте /api/set_webhook для настройки webhook."}
