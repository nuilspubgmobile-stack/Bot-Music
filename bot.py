import asyncio
import os
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.filters import Command
from yt_dlp import YoutubeDL

BOT_TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

YTDL_OPTS = {
    "format": "bestaudio/best",
    "postprocessors": [{
        "key": "FFmpegExtractAudio",
        "preferredcodec": "mp3",
        "preferredquality": "192",
    }],
    "quiet": True,
    "no_warnings": True,
}

async def download_audio(url: str) -> str | None:
    try:
        with YoutubeDL(YTDL_OPTS) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            mp3_path = os.path.splitext(filename)[0] + ".mp3"
            if os.path.exists(mp3_path):
                return mp3_path
            return None
    except Exception as e:
        print(f"Ошибка скачивания: {e}")
        return None

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "🎵 <b>Музыкальный бот</b>\n\n"
        "Напиши название трека (например: Linkin Park Numb) — я скачаю и пришлю аудио.",
        parse_mode=ParseMode.HTML
    )

@dp.message()
async def handle_search(message: types.Message):
    query = message.text.strip()
    if not query:
        return

    status_msg = await message.answer("⏳ Ищу и скачиваю трек…")

    search_url = f"ytsearch1:{query}"
    path = await asyncio.to_thread(download_audio, search_url)

    if path and os.path.exists(path):
        await message.answer_chat_action(action="upload_audio")
        await message.reply_document(
            document=types.FSInputFile(path),
            caption=f"🎵 Вот твой трек: {query}"
        )
        try:
            os.remove(path)
        except:
            pass
    else:
        await status_msg.edit_text("❌ Не удалось найти или скачать трек. Попробуй другой запрос.")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
