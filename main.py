from aiogram import Bot, Dispatcher
from dotenv import load_dotenv, find_dotenv
import asyncio
import os

from src.bot.handlres.user.clients.clients_sign_in import client_sign_in_router
from src.bot.handlres.user.employee.employee_sign_in import employee_sign_in_router
from src.bot.handlres.user.employee.employee_handlers import employee_handlers_router
from src.bot.handlres.user.clients.client_handlers import client_handlers_router
from src.bot.handlres.user_handlres import user_router

load_dotenv(find_dotenv())

bot = Bot(token=(os.getenv("BOT_TOKEN")))
dp = Dispatcher()


async def main():
    dp.include_routers(user_router, employee_sign_in_router, employee_handlers_router, client_sign_in_router, client_handlers_router)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot Stoped!")