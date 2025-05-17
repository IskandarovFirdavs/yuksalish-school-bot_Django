# telegram_bot.py
from aiogram import Dispatcher
from bot.bot_instance import bot
from bot.handlers import router as main_router

from aiogram.client.session.aiohttp import AiohttpSession
from aiohttp import ClientTimeout

timeout = ClientTimeout(total=30)
session = AiohttpSession(timeout=timeout)

dp = Dispatcher()
dp.include_router(main_router)

async def main():
    await dp.start_polling(bot)
