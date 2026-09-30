import asyncio
import os
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.filters import Command
from yt_dlp import YoutubeDL

BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Настройки: только аудио, конвертация в MP3, тихий режим
YTDL_OPTS = {
    "format": "bestaudio/best",
    "postprocessors": [{
        "key": "FFmpegExtractAudio",
        "preferredcodec": "mp3",
        "preferredquality": "192",
    }],
    "quiet": True,
    "no_warnings": True,
    "socket_timeout": 20,          # не ждать вечно, если YouTube тормозит
    "default_search": "ytsearch",  # поиск по названию
}

async def download_audio(query: str) -> str | None:
    """Скачивает и конвертирует трек в MP3. Возвращает путь к файлу."""
    url = f"ytsearch1:{query}"  # ищем 1 результат
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
        "Напиши название трека (например: Linkin Park Numb).\n"
        "Я пришлю его как MP3-файл — можно слушать в Telegram.",
        parse_mode=ParseMode.HTML
    )

@dp.message()
async def handle_search(message: types.Message):
    query = message.text.strip()
    if not query:
        return

    status_msg = await message.answer("⏳ Ищу и скачиваю трек…")

    # Скачивание в отдельном потоке, чтобы бот не «замирал» для других пользователей
    path = await asyncio.to_thread(download_audio, query)

    if path and os.path.exists(path):
        await message.answer_chat_action(action="upload_audio")
        try:
            await message.reply_document(
                document=types.FSInputFile(path),
                caption=f"🎵 Трек: {query}"
            )
        except Exception as send_err:
            print(f"Ошибка отправки: {send_err}")
            await status_msg.edit_text("❌ Не удалось отправить файл (возможно, слишком большой).")
        finally:
            # Удаляем файл, чтобы не забивать диск
            try:
                os.remove(path)
            except:
                pass
    else:
        await status_msg.edit_text("❌ Не получилось скачать трек. Попробуй другое название или короче запрос.")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
