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
            await message.answer(f"Hello <b>client</b> {message.from_user.full_name}. Choose one of the following buttons",
                                 reply_markup=clients_buttons, parse_mode="HTML")
        elif employee:
            await message.answer(f"Hello <b>freelancer</b> {message.from_user.full_name}. Choose one of the following buttons",
                                 reply_markup=employee_main_btn, parse_mode="HTML")
    else:
        await message.answer("Welcome. Please complete the registration", reply_markup=client_emp_kbd)
        

@user_router.message(F.text=="I am a client 👨🏻‍💼")
async def client_cmd(message: Message, state: FSMContext):
    await state.update_data(role="client")
    await message.answer("Enter your first name:", reply_markup=ReplyKeyboardRemove())
    from src.bot.handlres.user.clients.clients_sign_in import SignUpClient
    await state.set_state(SignUpClient.first_name)


@user_router.message(F.text=="I am a freelancer 👨🏻‍💻")
async def employee_cmd(message: Message, state: FSMContext):
    await state.update_data(role="employee")
    await message.answer("Enter your first name:", reply_markup=ReplyKeyboardRemove())
    from src.bot.handlres.user.employee.employee_sign_in import SignUpEmployee
    await state.set_state(SignUpEmployee.first_name)