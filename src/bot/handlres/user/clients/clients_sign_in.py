from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

from src.db.session import Local_Session
from src.db.crud.client import create_client
from src.bot.kbd.user_keyboard import client_emp_kbd, contact_kbd, kb
from src.bot.filters.user.role_filter import RoleFilter

import datetime
import re


class SignUpClient(StatesGroup):
    first_name = State()
    last_name = State()
    phone = State()
    birth_date = State()
    confirm = State()



client_sign_in_router = Router()
client_sign_in_router.message.filter(RoleFilter("client"))


@client_sign_in_router.message(SignUpClient.first_name)
async def get_first_name(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("Please enter a valid first name.")
        return
    await state.update_data(first_name=message.text.strip())
    await message.answer("Now enter your last name:")
    await state.set_state(SignUpClient.last_name)


@client_sign_in_router.message(SignUpClient.last_name)
async def get_last_name(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("Please enter a valid last name.")
        return
    await state.update_data(last_name=message.text.strip())

    await message.answer("Send contact (or enter the number manually):", reply_markup=contact_kbd)
    await state.set_state(SignUpClient.phone)


@client_sign_in_router.message(SignUpClient.phone)
async def get_phone(message: Message, state: FSMContext):
    phone = None
    if message.contact and message.contact.phone_number:
        phone = message.contact.phone_number
    elif message.text and message.text.lower() == "cancel":
        await state.clear()
        await message.answer("Registration cancelled.", reply_markup=client_emp_kbd)
        return
    elif message.text:
        txt = message.text.strip()
        if re.fullmatch(r"\+?\d{7,15}", txt):
            phone = txt
        else:
            await message.answer("Invalid number. Enter the number in the format +71234567890 or send contact.")
            return
    else:
        await message.answer("Please send contact or enter the number.")
        return

    await state.update_data(phone=phone)
    await message.answer("Enter date of birth (YYYY-MM-DD or DD.MM.YYYY):", reply_markup=ReplyKeyboardRemove())
    await state.set_state(SignUpClient.birth_date)


@client_sign_in_router.message(SignUpClient.birth_date)
async def get_birth_date(message: Message, state: FSMContext):
    txt = (message.text or "").strip()
    for fmt in ("%Y-%m-%d", "%d.%m.%Y", "%d/%m/%Y"):
        try:
            bd = datetime.datetime.strptime(txt, fmt).date()
            break
        except Exception:
            bd = None
    if not bd:
        await message.answer("Invalid date format. Try again (YYYY-MM-DD or DD.MM.YYYY).")
        return

    await state.update_data(birth_date=bd)

    data = await state.get_data()
    summary = (f"Please confirm the data:\n"
               f"First name: {data.get('first_name')}\n"
               f"Last name: {data.get('last_name')}\n"
               f"Phone: {data.get('phone')}\n"
               f"Date of birth: {data.get('birth_date')}")


    await message.answer(summary, reply_markup=kb)
    await state.set_state(SignUpClient.confirm)


@client_sign_in_router.callback_query(RoleFilter("client"), lambda c: c.data == "confirm_yes")
async def confirm_registration(call: CallbackQuery, state: FSMContext):
    await call.answer()
    data = await state.get_data()
    client_id = call.from_user.id

    async with Local_Session() as session:
        await create_client(
            session=session,
            telegram_user_id=client_id,
            first_name=data.get('first_name'),
            last_name=data.get('last_name'),
            phone=data.get('phone'),
            birth_date=data.get('birth_date')
        )

    await call.message.answer("Registration successful ✅")
    await state.clear()


@client_sign_in_router.callback_query(RoleFilter("client"), lambda c: c.data == "confirm_no")
async def cancel_confirmation(call: CallbackQuery, state: FSMContext):
    await call.answer()
    await state.clear()
    await call.message.answer("Registration cancelled. If you want, start over.", reply_markup=client_emp_kbd)


@client_sign_in_router.message(Command('cancel'))
async def cancel_cmd(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Registration cancelled.", reply_markup=client_emp_kbd)