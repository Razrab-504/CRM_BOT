from aiogram import F, Router
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

from src.bot.kbd.user_keyboard import contact_kbd, kb, client_emp_kbd, brunch_markup
from src.bot.filters.user.role_filter import RoleFilter
from src.db.session import Local_Session
from src.db.crud.employee import get_employee, create_employee
from src.db.enums import BranchEnum

import datetime
import re

employee_sign_in_router = Router()
employee_sign_in_router.message.filter(RoleFilter("employee"))
employee_sign_in_router.callback_query.filter(RoleFilter("employee"))



class SignUpEmployee(StatesGroup):
    first_name = State()
    last_name = State()
    phone = State()
    birth_date = State()
    branch = State()
    confirm = State()


@employee_sign_in_router.message(SignUpEmployee.first_name)
async def emp_first_name(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("Please enter a valid first name.")
        return
    await state.update_data(first_name=message.text.strip())
    await message.answer("Now enter your last name:")
    await state.set_state(SignUpEmployee.last_name)


@employee_sign_in_router.message(SignUpEmployee.last_name)
async def emp_last_name(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("Please enter a valid last name.")
        return
    await state.update_data(last_name=message.text.strip())

    await message.answer("Send contact (or enter the number manually):", reply_markup=contact_kbd)
    await state.set_state(SignUpEmployee.phone)


@employee_sign_in_router.message(SignUpEmployee.phone)
async def emp_phone(message: Message, state: FSMContext):
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
    await state.set_state(SignUpEmployee.birth_date)


@employee_sign_in_router.message(SignUpEmployee.birth_date)
async def emp_birth_date(message: Message, state: FSMContext):
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


    await message.answer("Choose direction/specialization:", reply_markup=brunch_markup)
    await state.set_state(SignUpEmployee.branch)


@employee_sign_in_router.callback_query(SignUpEmployee.branch, lambda c: c.data and c.data.startswith("branch:"))
async def emp_choose_branch(call: CallbackQuery, state: FSMContext):
    await call.answer()
    branch_value = call.data.split(":", 1)[1]
    await state.update_data(branch=branch_value)

    data = await state.get_data()
    summary = (f"Please confirm the data:\n"
               f"First name: {data.get('first_name')}\n"
               f"Last name: {data.get('last_name')}\n"
               f"Phone: {data.get('phone')}\n"
               f"Date of birth: {data.get('birth_date')}\n"
               f"Direction: {branch_value}")

    await call.message.answer(summary, reply_markup=kb)
    await state.set_state(SignUpEmployee.confirm)


@employee_sign_in_router.callback_query(RoleFilter("employee"), lambda c: c.data == "confirm_yes")
async def emp_confirm_yes(call: CallbackQuery, state: FSMContext):
    await call.answer()
    data = await state.get_data()
    user_id = call.from_user.id

    try:
        branch = BranchEnum(data.get('branch'))
    except Exception:
        branch = None

    async with Local_Session() as session:
        await create_employee(
            session=session,
            telegram_user_id=user_id,
            first_name=data.get('first_name'),
            last_name=data.get('last_name'),
            phone=data.get('phone'),
            birth_date=data.get('birth_date'),
            branch=branch,
        )

    await call.message.answer("Freelancer registration successful ✅")
    await state.clear()


@employee_sign_in_router.callback_query(RoleFilter("employee"), lambda c: c.data == "confirm_no")
async def emp_confirm_no(call: CallbackQuery, state: FSMContext):
    await call.answer()
    await state.clear()
    await call.message.answer("Registration cancelled. If you want, start over.", reply_markup=client_emp_kbd)
