import asyncio
from yt_dlp import YoutubeDL
from pathlib import Path

DOWNLOAD_DIR = Path("downloads")
DOWNLOAD_DIR.mkdir(exist_ok=True)

async def search_tracks(query: str, limit: int = 5):
    def _search():
        opts = {
            "format": "bestaudio/best",
            "quiet": True,
            "extract_flat": True,
            "default_search": f"ytsearch{limit}",
        }
        with YoutubeDL(opts) as ydl:
            info = ydl.extract_info(query, download=False)
            results = []
            for entry in info.get("entries", []):
                results.append({
                    "title": entry.get("title", "Без названия"),
                    "url": entry.get("url") or entry.get("webpage_url"),
                    "duration": entry.get("duration", 0),
                })
            return results
    return await asyncio.to_thread(_search)

async def download_audio(url: str) -> Path:
    def _download():
        opts = {
            "format": "bestaudio/best",
            "outtmpl": str(DOWNLOAD_DIR / "%(title)s.%(ext)s"),
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }],
            "quiet": True,
            "noplaylist": True,
        }
        with YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            title = info.get("title", "track")
            # yt-dlp сам сохраняет в MP3, но имя может содержать спецсимволы
            filepath = DOWNLOAD_DIR / f"{title}.mp3"
            # Если файл не появился (редкий кейс), пробуем найти любой mp3 в папке
            if filepath.exists():
                return filepath
            for f in DOWNLOAD_DIR.iterdir():
                if f.suffix.lower() == ".mp3":
                    return f
            return None
    return await asyncio.to_thread(_download)
