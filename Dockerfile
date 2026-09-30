FROM python:3.11-slim

# Ставим ffmpeg и ffprobe (нужны для конвертации в MP3)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Копируем зависимости и устанавливаем Python-пакеты
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код бота
COPY bot.py .

# Команда запуска
CMD ["python", "bot.py"]
