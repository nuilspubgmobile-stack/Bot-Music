import asyncio
import os
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.filters import Command
from yt_dlp import YoutubeDL

BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

def get_opts(source: str):
    opts = {
        "format": "bestaudio/best",
        "quiet": True,
        "no_warnings": True,
        "socket_timeout": 20,
        "http_headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        },
    }
    # Обход блокировки YouTube: пробуем Android-клиент
    if source == "ytsearch1":
        opts["extractor_args"] = {
            "youtube": {"player_client": ["android", "web"]}
        }
    return opts

def _download_sync(query: str, search_prefix: str) -> str | None:
    url = f"{search_prefix}:{query}"
    opts = get_opts(search_prefix)
    with YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)
        if os.path.exists(filename):
            return filename
        return None

async def download_audio(query: str, timeout_seconds: int = 45) -> str | None:
    loop = asyncio.get_event_loop()

    # Источник 1: SoundCloud
    try:
        path = await asyncio.wait_for(
            loop.run_in_executor(None, _download_sync, query, "scsearch1"),
            timeout=timeout_seconds
        )
        if path:
            print(f"Найдено на SoundCloud: {query}")
            return path
    except asyncio.TimeoutError:
        print(f"SoundCloud таймаут для {query}")
    except Exception as e:
        print(f"SoundCloud ошибка для {query}: {e}")

    # Источник 2: YouTube (через Android-клиент)
    try:
        path = await asyncio.wait_for(
            loop.run_in_executor(None, _download_sync, query, "ytsearch1"),
            timeout=timeout_seconds
        )
        if path:
            print(f"Найдено на YouTube: {query}")
            return path
    except asyncio.TimeoutError:
        print(f"YouTube таймаут для {query}")
    except Exception as e:
        print(f"YouTube ошибка для {query}: {e}")

    return None

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "🎵 <b>Музыкальный бот</b>\n\n"
        "Напиши название трека — я найду и пришлю аудио.\n"
        "Источники: SoundCloud → YouTube (запасной).",
        parse_mode=ParseMode.HTML
    )

@dp.message()
async def handle_search(message: types.Message):
    query = message.text.strip()
    if not query:
        return

    status_msg = await message.answer("⏳ Ищу трек (SoundCloud → YouTube)…")
    path = await download_audio(query, timeout_seconds=45)

    if path and os.path.exists(path):
        await message.answer_chat_action(action="upload_audio")
        try:
            await message.reply_document(
                document=types.FSInputFile(path),
                caption=f"🎵 {query}"
            )
        except Exception:
            await status_msg.edit_text("❌ Не удалось отправить файл.")
        finally:
            try:
                os.remove(path)
            except:
                pass
    else:
        await status_msg.edit_text(
            "❌ Не удалось найти трек.\n"
            "Попробуй точнее написать название."
        )

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
