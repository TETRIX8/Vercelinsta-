#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Скрипт для запуска Telegram бота для скачивания видео из Instagram.
"""

import os
import sys
from src.bot import main

if __name__ == "__main__":
    # Проверяем наличие токена
    if "TELEGRAM_BOT_TOKEN" not in os.environ:
        print("Ошибка: Переменная окружения TELEGRAM_BOT_TOKEN не установлена.")
        print("Установите токен командой: export TELEGRAM_BOT_TOKEN='ваш_токен'")
        sys.exit(1)
    
    # Запускаем бота
    main()
