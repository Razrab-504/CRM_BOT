from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext

from src.db.session import Local_Session
from src.db.crud.client import get_client
from src.db.crud.employee import get_employee
from src.bot.kbd.user_keyboard import client_emp_kbd, clients_buttons, employee_main_btn


user_router = Router()

@user_router.message(CommandStart())
async def start_cmd(message: Message):
    user_id = message.from_user.id
    
    async with Local_Session() as session:
        client = await get_client(session=session, telegram_user_id=user_id)
        employee = await get_employee(session=session, telegram_user_id=user_id)

    if client or employee:
        if client:
            await message.answer(f"Привет <b>клиент</b> {message.from_user.full_name}. Выбирите одну из следующих кнопок", 
                                 reply_markup=clients_buttons, parse_mode="HTML")
        elif employee:
            await message.answer(f"Привет <b>исполнитель</b> {message.from_user.full_name}. Выбирите одну из следующих кнопок", 
                                 reply_markup=employee_main_btn, parse_mode="HTML")
    else:
        await message.answer("Добро пожаловать. Пройдите пожалуйста регистрацию", reply_markup=client_emp_kbd)
        

@user_router.message(F.text=="Я клиент 👨🏻‍💼")
async def client_cmd(message: Message, state: FSMContext):
    await state.update_data(role="client")
    await message.answer("Напишите свое имя:", reply_markup=ReplyKeyboardRemove())
    from src.bot.handlres.user.clients.clients_sign_in import SignUpClient
    await state.set_state(SignUpClient.first_name)


@user_router.message(F.text=="Я исполнитель 👨🏻‍💻")
async def employee_cmd(message: Message, state: FSMContext):
    await state.update_data(role="employee")
    await message.answer("Напишите свое имя:", reply_markup=ReplyKeyboardRemove())
    from src.bot.handlres.user.employee.employee_sign_in import SignUpEmployee
    await state.set_state(SignUpEmployee.first_name)