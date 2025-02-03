import asyncio, telebot
import os
import logging

from telebot.async_telebot import AsyncTeleBot
from dotenv import load_dotenv
from setup_logging import setup_logging


load_dotenv()

TOKEN_BOT = os.getenv('TOKEN_BOT')
LOG_LEVEL = True

setup_logging()  # Вызываем функцию для настройки логирования

bot = AsyncTeleBot(TOKEN_BOT)
telebot.logger.setLevel(LOG_LEVEL)






















if __name__ == "__main__":
    asyncio.run(bot.infinity_polling(logger_level=True))