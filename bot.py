import os
import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from dotenv import load_dotenv
from downloader import search_tracks, download_audio

import asyncio
from aiogram.exceptions import TelegramNetworkError

async def main():
    max_retries = 5
    for attempt in range(1, max_retries + 1):
        try:
            await bot.delete_webhook(drop_pending_updates=True)
            await dp.start_polling(bot)
            return  # если всё ок — выходим
        except TelegramNetworkError as e:
            print(f"Попытка {attempt}/{max_retries}: сеть недоступна — {e}")
            if attempt == max_retries:
                raise
            await asyncio.sleep(3)  # ждём 3 секунды перед следующей попыткой


load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("Не найден BOT_TOKEN в .env")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

class SearchState:
    pass  # для простоты храним в словаре, без полноценного FSM

search_results = {}

@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        "🎵 Музыкальный бот 🎶\n\n"
        "Отправь название трека или ссылку на YouTube — я скачаю и пришлю в MP3.\n"
        "(Лимит Telegram: до 50 МБ)"
    )

@dp.message(F.text.startswith("http"))
async def handle_link(message: Message):
    url = message.text.strip()
    m = await message.answer("⏳ Скачиваю трек...")
    try:
        filepath = await download_audio(url)
        if filepath and filepath.exists():
            await message.answer_audio(audio=filepath.open("rb"))
            filepath.unlink()
        else:
            await m.edit_text("❌ Не удалось скачать трек.")
    except Exception as e:
        await m.edit_text(f"❌ Ошибка: {e}")

@dp.message(F.text)
async def handle_search(message: Message):
    query = message.text.strip()
    m = await message.answer("🔍 Ищу на YouTube...")

    results = await search_tracks(query, limit=5)
    if not results:
        await m.edit_text("❌ Ничего не найдено.")
        return

    search_results[message.from_user.id] = results

    builder = InlineKeyboardBuilder()
    for i, track in enumerate(results):
        duration = track["duration"]
        dur_str = f"{duration // 60}:{duration % 60:02d}" if duration else "?"
        title = track["title"][:55] + "…" if len(track["title"]) > 55 else track["title"]
        builder.add(InlineKeyboardButton(
            text=f"{i + 1}. {title} [{dur_str}]",
            callback_data=f"track_{i}"
        ))
    builder.adjust(1)

    await m.edit_text("Выбери трек:", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("track_"))
async def handle_track_choice(callback: CallbackQuery):
    index = int(callback.data.split("_")[1])
    user_id = callback.from_user.id

    if user_id not in search_results:
        await callback.answer("Сессия истекла, поищи заново.", show_alert=True)
        return

    track = search_results[user_id][index]
    url = track["url"]

    m = await callback.message.edit_text(f"⏳ Скачиваю: {track['title'][:40]}…")
    await callback.answer()

    try:
        filepath = await download_audio(url)
        if filepath and filepath.exists():
            await callback.message.answer_audio(audio=filepath.open("rb"))
            filepath.unlink()
            await m.delete()
        else:
            await m.edit_text("❌ Не удалось скачать трек.")
    except Exception as e:
        await m.edit_text(f"❌ Ошибка: {e}")

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

