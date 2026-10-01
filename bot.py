import asyncio
import os
import subprocess
from pathlib import Path
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.filters import Command
from yt_dlp import YoutubeDL

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("Не задан BOT_TOKEN в переменных окружения!")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

def check_ffmpeg():
    """Проверяет, установлен ли FFmpeg в системе."""
    try:
        subprocess.run(["ffmpeg", "-version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except FileNotFoundError:
        return False

FFMPEG_AVAILABLE = check_ffmpeg()

def get_ydl_opts(output_path: str):
    return {
        "format": "bestaudio/best",
        "quiet": False,
        "no_warnings": False,
        "socket_timeout": 30,
        "outtmpl": output_path,
        "http_headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        },
    }

def convert_to_mp3(input_path: str, output_path: str) -> bool:
    """Конвертирует файл в MP3 с помощью FFmpeg."""
    if not FFMPEG_AVAILABLE:
        print("[ERROR] FFmpeg не найден! Конвертация невозможна.")
        return False
    
    cmd = [
        "ffmpeg",
        "-y",
        "-i", input_path,
        "-acodec", "libmp3lame",
        "-b:a", "192k",
        output_path
    ]
    try:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode == 0:
            print(f"[OK] Конвертировано: {output_path}")
            return True
        else:
            print(f"[FFMPEG ERROR] {result.stderr.decode()}")
            return False
    except Exception as e:
        print(f"[EXCEPTION] Ошибка конвертации: {e}")
        return False

def _download_sync(query: str) -> str | None:
    url = f"scsearch1:{query}"
    # Генерируем уникальное имя файла на основе запроса (упрощённо)
    safe_name = "".join(c if c.isalnum() or c in "_-" else "_" for c in query)[:50]
    output_path = os.path.join(DOWNLOAD_DIR, f"{safe_name}.temp")
    
    opts = get_ydl_opts(output_path)
    
    with YoutubeDL(opts) as ydl:
        try:
            info = ydl.extract_info(url, download=True)
            if not info or "entries" in info and not info["entries"]:
                print("[SEARCH EMPTY] По запросу ничего не найдено.")
                return None
            
            # Если скачался файл — возвращаем путь
            if os.path.

