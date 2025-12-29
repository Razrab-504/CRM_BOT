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
        await message.answer("Пожалуйста, введите корректное имя.")
        return
    await state.update_data(first_name=message.text.strip())
    await message.answer("А теперь фамилию:")
    await state.set_state(SignUpEmployee.last_name)


@employee_sign_in_router.message(SignUpEmployee.last_name)
async def emp_last_name(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("Пожалуйста, введите корректную фамилию.")
        return
    await state.update_data(last_name=message.text.strip())

    await message.answer("Отправьте контакт (или введите номер вручную):", reply_markup=contact_kbd)
    await state.set_state(SignUpEmployee.phone)


@employee_sign_in_router.message(SignUpEmployee.phone)
async def emp_phone(message: Message, state: FSMContext):
    phone = None
    if message.contact and message.contact.phone_number:
        phone = message.contact.phone_number
    elif message.text and message.text.lower() == "отмена":
        await state.clear()
        await message.answer("Регистрация отменена.", reply_markup=client_emp_kbd)
        return
    elif message.text:
        txt = message.text.strip()
        if re.fullmatch(r"\+?\d{7,15}", txt):
            phone = txt
        else:
            await message.answer("Неверный номер. Введите номер в формате +71234567890 или отправьте контакт.")
            return
    else:
        await message.answer("Пожалуйста, отправьте контакт или введите номер.")
        return

    await state.update_data(phone=phone)
    await message.answer("Введите дату рождения (ГГГГ-ММ-ДД или ДД.ММ.ГГГГ):", reply_markup=ReplyKeyboardRemove())
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
        await message.answer("Неверный формат даты. Попробуйте снова (ГГГГ-ММ-ДД или ДД.MM.ГГГГ).")
        return

    await state.update_data(birth_date=bd)


    await message.answer("Выберите направление/специализацию:", reply_markup=brunch_markup)
    await state.set_state(SignUpEmployee.branch)


@employee_sign_in_router.callback_query(SignUpEmployee.branch, lambda c: c.data and c.data.startswith("branch:"))
async def emp_choose_branch(call: CallbackQuery, state: FSMContext):
    await call.answer()
    branch_value = call.data.split(":", 1)[1]
    await state.update_data(branch=branch_value)

    data = await state.get_data()
    summary = (f"Пожалуйста, подтвердите данные:\n"
               f"Имя: {data.get('first_name')}\n"
               f"Фамилия: {data.get('last_name')}\n"
               f"Телефон: {data.get('phone')}\n"
               f"Дата рождения: {data.get('birth_date')}\n"
               f"Направление: {branch_value}")

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

    await call.message.answer("Регистрация исполнителя успешна ✅")
    await state.clear()


@employee_sign_in_router.callback_query(RoleFilter("employee"), lambda c: c.data == "confirm_no")
async def emp_confirm_no(call: CallbackQuery, state: FSMContext):
    await call.answer()
    await state.clear()
    await call.message.answer("Регистрация отменена. Если хотите — начните заново.", reply_markup=client_emp_kbd)
