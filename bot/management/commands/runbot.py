from django.core.management.base import BaseCommand
import asyncio
from bot.telegram_bot import main

class Command(BaseCommand):
    help = 'Telegram botni ishga tushuradi'

    def handle(self, *args, **options):
        asyncio.run(main())
