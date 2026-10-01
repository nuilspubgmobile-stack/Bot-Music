import asyncio
import os
import subprocess
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
    if not FFMPEG_AVAILABLE:
        print("[ERROR] FFmpeg не найден! Конвертация невозможна.")
        return False
    cmd = [
        "ffmpeg", "-y", "-i", input_path,
        "-acodec", "libmp3lame", "-b:a", "192k",
        output_path
    ]
    try:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode == 0:
            print(f"[OK] Конвертировано: {output_path}")
            return True
        else:
            print(f"[FFMPEG ERROR] {result.stderr.decode()[:500]}")
            return False
    except Exception as e:
        print(f"[EXCEPTION] Ошибка конвертации: {e}")
        return False


def download_track_sync(query: str):
    url = f"scsearch1:{query}"
    safe_name = "".join(c if c.isalnum() or c in "_-" else "_" for c in query)[:50]
    temp_path = os.path.join(DOWNLOAD_DIR, f"{safe_name}.%(ext)s")
    mp3_path = os.path.join(DOWNLOAD_DIR, f"{safe_name}.mp3")

    opts = get_ydl_opts(temp_path)

    with YoutubeDL(opts) as ydl:
        try:
            info = ydl.extract_info(url, download=True)
            if not info:
                print("[SEARCH EMPTY] По запросу ничего не найдено.")
                return None

            entries = info.get("entries")
            if entries:
                first = next((e for e in entries if e), None)
                if not first:
                    first = entries[0]
                info = first

            # yt-dlp сам подставит расширение вместо %(ext)s
            # Ищем файл по шаблону
            downloaded_path = None
            for f in os.listdir(DOWNLOAD_DIR):
                if f.startswith(safe_name) and not f.endswith(".mp3"):
                    downloaded_path = os.path.join(DOWNLOAD_DIR, f)
                    break

            if not downloaded_path or not os.path.exists(downloaded_path):
                print("[ERROR] Файл не появился после скачивания.")
                return None

            # Конвертируем в MP3
            if not convert_to_mp3(downloaded_path, mp3_path):
                print("[ERROR] Не удалось сконвертировать в MP3.")
                # Если ffmpeg нет — попробуем отправить как есть
                return downloaded_path

            # Удаляем временный файл
            try:
                os.remove(downloaded_path)
            except Exception:
                pass

            return mp3_path

        except Exception as e:
            print(f"[YDL ERROR] {e}")
            return None


async def download_audio(query: str, timeout_seconds: int = 60):
    loop = asyncio.get_event_loop()
    try:
        path = await asyncio.wait_for(
            loop.run_in_executor(None, download_track_sync, query),
            timeout=timeout_seconds
        )
        return path
    except asyncio.TimeoutError:
        print(f"[TIMEOUT] Превышено время ожидания для '{query}'")
    except Exception as e:
        print(f"[EXCEPTION] {e}")
    return None


@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    ffmpeg_status = "✅ установлен" if FFMPEG_AVAILABLE else "❌ НЕ установлен (конвертация в MP3 невозможна)"
    await message.answer(
        "🎵 <b>Музыкальный бот</b>\n\n"
        "Напиши название трека — я найду его на SoundCloud и пришлю аудио.\n\n"
        f"FFmpeg: {ffmpeg_status}",
        parse_mode=ParseMode.HTML
    )


@dp.message()
async def handle_search(message: types.Message):
    query = message.text.strip()
    if not query:
        return

    status_msg = await message.answer("⏳ Ищу трек на SoundCloud…")
    path = await download_audio(query, timeout_seconds=60)

    if path is None:
        await status_msg.edit_text(
            "❌ Не удалось найти или скачать трек.\n"
            "Попробуй другое название или другого исполнителя."
        )
        return

    if not os.path.exists(path):
        await status_msg.edit_text("❌ Файл не найден после скачивания.")
        return

    file_size = os.path.getsize(path)
    if file_size > 50 * 1024 * 1024:
        await status_msg.edit_text("❌ Файл слишком большой для отправки в Telegram (больше 50 МБ).")
        try:
            os.remove(path)
        except Exception:
            pass
        return

       await bot.send_chat_action(chat_id=message.chat.id, action="upload_audio")
    try:
        await message.reply_document(
            document=types.FSInputFile(path),
            caption=f"🎵 {query}"
        )
        await status_msg.delete()
    except Exception as e:
        await status_msg.edit_text(f"❌ Ошибка при отправке: {e}")
    finally:
        try:
            os.remove(path)
        except Exception:
            pass


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
