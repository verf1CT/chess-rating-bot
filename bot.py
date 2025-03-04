import os
import asyncio
import logging
import requests
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# Включаем логирование
logging.basicConfig(level=logging.INFO)

# Загружаем переменные окружения
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")  # Токен бота
CHESS_PLAYER_ID = os.getenv("CHESS_PLAYER_ID")  # ID игрока на ruchess
CHAT_ID = os.getenv("CHAT_ID")  # ID чата или пользователя, куда отправлять уведомления

# Создаем бота и диспетчер
bot = Bot(token=TELEGRAM_BOT_TOKEN)
dp = Dispatcher(bot)

# Функция для получения рейтинга с ruchess
def get_chess_rating(player_id):
    url = f"https://ratings.ruchess.ru/api/players/{player_id}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        if "player" in data and "ratings" in data["player"]:
            ratings = data["player"]["ratings"]
            return ratings  # Возвращаем все рейтинги
    except Exception as e:
        logging.error(f"Ошибка при получении рейтинга: {e}")
    return None

# Глобальная переменная для хранения последнего рейтинга
last_rating = None

# Функция для проверки обновлений рейтинга
async def check_rating():
    global last_rating
    ratings = get_chess_rating(CHESS_PLAYER_ID)
    
    if ratings:
        new_rating = ratings[0]["value"]  # Берем первый рейтинг (например, классический)
        if last_rating is not None and new_rating != last_rating:
            message = f"♟ Рейтинг изменился! Новый рейтинг: {new_rating}"
            await bot.send_message(CHAT_ID, message)
        last_rating = new_rating

# Запуск планировщика
scheduler = AsyncIOScheduler()

async def start_scheduler():
    scheduler.add_job(check_rating, "interval", minutes=5)  # Проверка каждые 5 минут
    scheduler.start()

# Обработчик команды /start
@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    await message.reply("Привет! Я буду уведомлять об изменении рейтинга на ruchess.ru.")

# Главная функция
async def main():
    await start_scheduler()
    await dp.start_polling()

# Запуск бота
if __name__ == "__main__":
    asyncio.run(main())
