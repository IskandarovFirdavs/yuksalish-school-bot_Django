# bot_instance.py
from aiogram import Bot
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties


bot = Bot(
    token="8083954738:AAF-pcT24PP94bnGwiMF6AL2KKUzOo93l_M",
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
