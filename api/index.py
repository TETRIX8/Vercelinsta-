#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Точка входа для Vercel - обработка webhook-запросов от Telegram.
"""

import os
import logging
from fastapi import FastAPI, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
import uvloop
import asyncio

# Установка uvloop для улучшения производительности
uvloop.install()

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# Создаем FastAPI приложение
app = FastAPI(title="Telegram Bot Webhook", version="1.0")

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)

# Конфигурация
class Config:
    TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
    WEBHOOK_URL = os.environ.get("WEBHOOK_URL")
    if not TOKEN:
        raise ValueError("TELEGRAM_BOT_TOKEN не установлен в переменных окружения")

# Глобальная переменная для хранения приложения Telegram
_application = None

async def get_application() -> Application:
    """Инициализирует и возвращает приложение Telegram Bot."""
    global _application
    if _application is None:
        # Создаем экземпляр Application
        _application = (
            Application.builder()
            .token(Config.TOKEN)
            .post_init(post_init)
            .build()
        )

        # Регистрируем обработчики команд
        _application.add_handler(CommandHandler("start", start))
        _application.add_handler(CommandHandler("help", help_command))
        _application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, process_instagram_url)
        )

        # Инициализируем приложение
        await _application.initialize()
        await _application.start()
    
    return _application

async def post_init(application: Application) -> None:
    """Действия после инициализации бота."""
    logger.info("Бот успешно инициализирован")

# Обработчики команд (должны быть определены в src/bot.py)
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /start."""
    await update.message.reply_text("Привет! Отправьте мне ссылку на Instagram.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /help."""
    await update.message.reply_text("Помощь: отправьте мне ссылку на Instagram.")

async def process_instagram_url(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик текстовых сообщений."""
    text = update.message.text
    await update.message.reply_text(f"Вы отправили: {text}")

@app.post("/api/webhook", status_code=status.HTTP_200_OK)
async def webhook(request: Request) -> Response:
    """Основной обработчик вебхуков от Telegram."""
    try:
        application = await get_application()
        
        # Получаем данные запроса
        data = await request.json()
        logger.debug(f"Получен webhook: {data}")
        
        # Преобразуем в объект Update
        update = Update.de_json(data, application.bot)
        
        # Обрабатываем обновление
        await application.process_update(update)
        
        return Response(content="OK", media_type="text/plain")

    except json.JSONDecodeError:
        logger.error("Невалидный JSON в теле запроса")
        return Response(
            content="Invalid JSON",
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    except Exception as e:
        logger.exception("Ошибка при обработке webhook")
        return Response(
            content=str(e),
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

@app.get("/api/set_webhook")
async def set_webhook() -> dict:
    """Устанавливает вебхук для бота."""
    if not Config.WEBHOOK_URL:
        return {
            "success": False,
            "error": "WEBHOOK_URL не установлен в переменных окружения",
        }

    try:
        application = await get_application()
        webhook_url = f"{Config.WEBHOOK_URL.rstrip('/')}/api/webhook"
        
        # Устанавливаем вебхук
        await application.bot.set_webhook(
            url=webhook_url,
            max_connections=40,
        )
        
        # Получаем информацию о вебхуке
        webhook_info = await application.bot.get_webhook_info()
        
        return {
            "success": True,
            "webhook_url": webhook_url,
            "webhook_info": webhook_info.to_dict(),
        }

    except Exception as e:
        logger.exception("Ошибка при установке webhook")
        return {
            "success": False,
            "error": str(e),
        }

@app.get("/api/health")
async def health_check() -> dict:
    """Проверка работоспособности сервиса."""
    try:
        application = await get_application()
        bot_info = await application.bot.get_me()
        
        return {
            "status": "ok",
            "bot_info": bot_info.to_dict(),
        }
    except Exception as e:
        logger.exception("Ошибка при проверке здоровья")
        return {
            "status": "error",
            "error": str(e),
        }

@app.get("/")
async def root() -> dict:
    """Корневой эндпоинт."""
    return {
        "message": "Instagram Video Bot API работает",
        "endpoints": {
            "set_webhook": "/api/set_webhook",
            "webhook": "/api/webhook (POST)",
            "health": "/api/health",
        },
    }

@app.on_event("shutdown")
async def shutdown_event() -> None:
    """Очистка ресурсов при завершении работы."""
    if _application:
        await _application.shutdown()
        await _application.stop()
