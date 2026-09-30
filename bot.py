import asyncio
import os
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.filters import Command
from yt_dlp import YoutubeDL

BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

def get_opts():
    return {
        "format": "bestaudio/best",
        "quiet": False,          # Важно: yt-dlp будет писать свои логи в stdout
        "no_warnings": False,    # Показываем предупреждения
        "socket_timeout": 20,
        "outtmpl": os.path.join(DOWNLOAD_DIR, "%(id)s.%(ext)s"),
        "http_headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        },
    }

def _download_sync(query: str):
    url = f"scsearch1:{query}"
    opts = get_opts()
    with YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=False)  # Сначала только поиск (без скачивания)
        if not info or "entries" not in info or not info["entries"]:
            print(f"[SEARCH EMPTY] По запросу '{query}' ничего не найдено в SoundCloud.")
            return None

        # Берём первый результат
        first = next((e for e in info["entries"] if e), None)
        if not first:
            print(f"[NO_ENTRY] Первый трек не определён.")
            return None

        print(f"[DOWNLOAD] Начинаю скачивание: {first.get('title')}")
        ydl.download([first["url"]])
        filename = ydl.prepare_filename(first)
        if os.path.exists(filename):
            return filename
        return None

async def download_audio(query: str, timeout_seconds: int = 45):
    loop = asyncio.get_event_loop()
    try:
        path = await asyncio.wait_for(
            loop.run_in_executor(None, _download_sync, query),
            timeout=timeout_seconds
        )
        return path
    except asyncio.TimeoutError:
        print(f"[TIMEOUT] Превышено время ожидания для '{query}'")
    except Exception as e:
        print(f"[EXCEPTION] Ошибка: {e}")
    return None

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "🎵 <b>Музыкальный бот (режим отладки)</b>\n\n"
        "Напиши точное название трека и исполнителя.\n"
        "<b>Пример:</b> `Friendly Thug 52 NGG COW`\n\n"
        "Бот покажет, что нашёл, и сохранит файл в папку.",
        parse_mode=ParseMode.HTML
    )

@dp.message()
async def handle_search(message: types.Message):
    query = message.text.strip()
    if not query:
        return

    status_msg = await message.answer("⏳ Ищу трек на SoundCloud…")
    path = await download_audio(query, timeout_seconds=45)

    if path is None:
        await status_msg.edit_text(
            "❌ Не удалось найти трек на SoundCloud.\n\n"
            "Попробуй:\n"
            "• Написать полное имя исполнителя и трека\n"
            "• Проверить, есть ли трек на SoundCloud (открой сайт и поищи вручную)\n"
            "• Если логи пустые — проблема в поиске или IP-адресе сервера."
        )
        return

    file_size = os.path.getsize(path)
    human_size = f"{file_size / 1024:.1f} КБ" if file_size < 1_048_576 else f"{file_size / 1_048_576:.1f} МБ"

    await status_msg.edit_text(
        f"✅ Трек найден и сохранён!\n\n"
        f"📁 Путь: `{path}`\n"
        f"🎵 Название: {os.path.basename(path)}\n"
        f"💾 Размер: {human_size}\n\n"
        "Проверь файл вручную — он не удаляется.",
        parse_mode="Markdown"
    )

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
