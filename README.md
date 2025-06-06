# Инструкция по установке и запуску Telegram бота для скачивания видео из Instagram

## Требования

- Python 3.8 или выше
- ffmpeg (установлен в системе)
- Токен Telegram бота (получается через BotFather)

## Установка

1. Клонируйте репозиторий или распакуйте архив с проектом:
```bash
git clone https://github.com/your-username/instagram-video-bot.git
cd instagram-video-bot
```

2. Создайте виртуальное окружение и активируйте его:
```bash
python -m venv venv
source venv/bin/activate  # для Linux/Mac
# или
venv\Scripts\activate  # для Windows
```

3. Установите зависимости:
```bash
pip install -r requirements.txt
```

4. Убедитесь, что ffmpeg установлен в вашей системе:
```bash
ffmpeg -version
```

Если ffmpeg не установлен:
- Для Ubuntu/Debian: `sudo apt-get install ffmpeg`
- Для macOS: `brew install ffmpeg`
- Для Windows: скачайте с [официального сайта](https://ffmpeg.org/download.html) и добавьте в PATH

## Настройка бота

1. Создайте бота в Telegram через [@BotFather](https://t.me/BotFather):
   - Отправьте команду `/newbot`
   - Укажите имя бота
   - Укажите username бота (должен заканчиваться на "bot")
   - Скопируйте полученный токен

2. Установите токен бота как переменную окружения:
```bash
export TELEGRAM_BOT_TOKEN='ваш_токен_бота'  # для Linux/Mac
# или
set TELEGRAM_BOT_TOKEN=ваш_токен_бота  # для Windows CMD
# или
$env:TELEGRAM_BOT_TOKEN='ваш_токен_бота'  # для Windows PowerShell
```

## Запуск бота

Запустите бота командой:
```bash
python run.py
```

Бот будет работать до тех пор, пока вы не остановите скрипт (Ctrl+C).

## Использование бота

1. Найдите своего бота в Telegram по его username
2. Отправьте команду `/start` для начала работы
3. Отправьте ссылку на видео из Instagram
4. Бот скачает видео, извлечет аудио и отправит вам:
   - Полное описание поста
   - Видео файл
   - Аудио файл

## Развертывание на сервере

Для постоянной работы бота рекомендуется развернуть его на сервере:

1. Установите все зависимости на сервере
2. Настройте автоматический перезапуск с помощью systemd, supervisor или другого менеджера процессов
3. Пример конфигурации для systemd:

```ini
[Unit]
Description=Instagram Video Telegram Bot
After=network.target

[Service]
User=username
WorkingDirectory=/path/to/instagram-video-bot
Environment="TELEGRAM_BOT_TOKEN=ваш_токен_бота"
ExecStart=/path/to/instagram-video-bot/venv/bin/python run.py
Restart=always

[Install]
WantedBy=multi-user.target
```

## Устранение неполадок

- **Ошибка "Переменная окружения TELEGRAM_BOT_TOKEN не установлена"**: Убедитесь, что вы правильно установили переменную окружения с токеном бота.
- **Ошибка при скачивании видео**: Проверьте, что ссылка на Instagram действительна и видео доступно.
- **Ошибка при извлечении аудио**: Убедитесь, что ffmpeg правильно установлен и доступен в PATH.
- **Бот не отвечает**: Проверьте подключение к интернету и правильность токена бота.

## Ограничения

- Бот может не работать с приватными аккаунтами Instagram
- Существуют ограничения на размер файлов в Telegram (до 50 МБ)
- Instagram может ограничивать доступ к контенту, что может привести к ошибкам при скачивании
