import asyncio
import logging
import requests
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message
from aiogram.filters import Command
from bs4 import BeautifulSoup
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import os

# Загружаем токен из переменных окружения (удобно для Railway)
TOKEN = os.getenv("TOKEN")

# Проверка, есть ли токен
if not TOKEN:
    raise ValueError("Не задан токен бота! Укажите его в переменных окружения.")

# Запускаем бота
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Словарь отслеживаемых пользователей {telegram_id: {"id": chess_id, "rating": rating}}
user_ratings = {}

# Функция для получения рейтинга шахматиста
def get_chess_rating(player_id):
    url = f"https://ratings.ruchess.ru/people/{player_id}"
    response = requests.get(url)
    if response.status_code != 200:
        return None

    soup = BeautifulSoup(response.text, "html.parser")
    rating_tag = soup.find("span", class_="profile__rating-value")
    if rating_tag:
        return int(rating_tag.text.strip())  # Преобразуем в число
    return None

# Команда /start
@dp.message(Command("start"))
async def start(message: Message):
    await message.answer(
        "Привет! Я бот, который следит за изменением рейтинга шахматистов.\n\n"
        "Чтобы начать отслеживание, отправь команду:\n"
        "`/track <ID>` (например: `/track 12345`)"
    )

# Команда /track <ID>
@dp.message(Command("track"))
async def track(message: Message):
    args = message.text.split()
    if len(args) < 2 or not args[1].isdigit():
        await message.answer("Использование: `/track <ID>`\nНапример: `/track 12345`")
        return

    chess_id = args[1]
    rating = get_chess_rating(chess_id)

    if rating is None:
        await message.answer("Ошибка: не удалось получить рейтинг. Проверь ID шахматиста.")
        return

    user_ratings[message.from_user.id] = {"id": chess_id, "rating": rating}
    await message.answer(f"✅ Теперь я отслеживаю рейтинг игрока с ID {chess_id}.\nТекущий рейтинг: {rating}.")

# Команда /untrack (удаление отслеживания)
@dp.message(Command("untrack"))
async def untrack(message: Message):
    if message.from_user.id in user_ratings:
        del user_ratings[message.from_user.id]
        await message.answer("❌ Я больше не отслеживаю рейтинг шахматиста.")
    else:
        await message.answer("Ты еще не добавлял шахматиста для отслеживания.")

# Функция проверки рейтинга по расписанию
async def check_ratings():
    for user_id, data in user_ratings.items():
        new_rating = get_chess_rating(data["id"])
        if new_rating is not None and new_rating != data["rating"]:
            await bot.send_message(user_id, f"♟ Рейтинг шахматиста с ID {data['id']} изменился: {data['rating']} ➝ {new_rating}")
            user_ratings[user_id]["rating"] = new_rating  # Обновляем рейтинг

# Запуск планировщика (каждые 10 минут)
scheduler = AsyncIOScheduler()
scheduler.add_job(check_ratings, "interval", minutes=10)
scheduler.start()

# Запуск бота
async def main():
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
