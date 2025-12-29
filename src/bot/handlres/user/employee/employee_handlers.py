from aiogram import F, Router, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext

from src.bot.filters.user.role_filter import RoleFilter
from src.db.crud.employee import get_employee
from src.db.crud.order import get_orders_by_employee, update_order_status, get_order_by_id
from src.db.crud.client import get_client_by_id
from src.db.crud.review import get_reviews_by_employee
from src.db.session import Local_Session
from src.db.enums import OrderStatusEnum
from src.bot.kbd.user_keyboard import create_employee_orders_keyboard, create_order_action_keyboard

employee_handlers_router = Router()
employee_handlers_router.message.filter(RoleFilter("employee"))
employee_handlers_router.callback_query.filter(RoleFilter("employee"))


def format_order_info(order, client=None) -> str:
    if client:
        client_info = f"{client.first_name} {client.last_name}"
        client_phone = f"📞 <b>Телефон клиента:</b> {client.phone}\n"
    else:
        client_info = "Неизвестный клиент"
        client_phone = ""
    
    status_text = {
        "PENDING": "⏳ Ожидает подтверждения",
        "IN_PROGRESS": "✅ В работе",
        "COMPLETED": "✅ Завершен",
        "CANCELLED": "❌ Отменен"
    }
    status_display = status_text.get(order.status.value, order.status.value)
    
    return (
        f"📋 <b>Заказ #{order.id}</b>\n\n"
        f"👤 <b>Клиент:</b> {client_info}\n"
        f"{client_phone}"
        f"📝 <b>Описание:</b> {order.description}\n"
        f"💰 <b>Бюджет:</b> {order.price} USD\n"
        f"📊 <b>Статус:</b> {status_display}\n"
        f"📅 <b>Создан:</b> {order.created_at.strftime('%d.%m.%Y %H:%M')}"
    )


@employee_handlers_router.message(F.text == "📋 Мои заказы")
async def show_employee_orders(message: Message):
    user_id = message.from_user.id
    
    async with Local_Session() as session:
        employee = await get_employee(session, user_id)
        if not employee:
            await message.answer("Ошибка: исполнитель не найден.")
            return
        
        orders = await get_orders_by_employee(session, employee.id)
    
    if not orders:
        await message.answer("У вас пока нет заказов.")
        return
    
    text = "📋 <b>Ваши заказы:</b>\n\nВыберите заказ для просмотра:"
    keyboard = create_employee_orders_keyboard(orders)
    await message.answer(text, reply_markup=keyboard, parse_mode="HTML")


@employee_handlers_router.callback_query(F.data.startswith("emp_order_view:"))
async def view_employee_order(callback: CallbackQuery):
    await callback.answer()
    order_id = int(callback.data.split(":")[1])
    
    async with Local_Session() as session:
        order = await get_order_by_id(session, order_id)
        if not order:
            await callback.message.answer("Заказ не найден.")
            return
        
        client = await get_client_by_id(session, order.client_id)
        order_text = format_order_info(order, client)
        
        if order.status == OrderStatusEnum.PENDING:
            keyboard = create_order_action_keyboard(order_id)
            await callback.message.edit_text(order_text, reply_markup=keyboard, parse_mode="HTML")
        else:
            await callback.message.edit_text(order_text, parse_mode="HTML")


@employee_handlers_router.callback_query(F.data.startswith("order_approve:"))
async def approve_order(callback: CallbackQuery):
    await callback.answer()
    order_id = int(callback.data.split(":")[1])
    
    async with Local_Session() as session:
        order = await get_order_by_id(session, order_id)
        if not order:
            await callback.message.answer("Заказ не найден.")
            return
        
        if order.status != OrderStatusEnum.PENDING:
            await callback.answer("Этот заказ уже обработан.", show_alert=True)
            return
        
        updated_order = await update_order_status(session, order_id, OrderStatusEnum.IN_PROGRESS)
        if updated_order:
            client = await get_client_by_id(session, updated_order.client_id)
            order_text = format_order_info(updated_order, client)
            await callback.message.edit_text(
                f"✅ <b>Заказ подтвержден!</b>\n\n{order_text}",
                parse_mode="HTML"
            )
        else:
            await callback.message.answer("Ошибка при обновлении статуса заказа.")


@employee_handlers_router.callback_query(F.data.startswith("order_cancel_emp:"))
async def cancel_order_by_employee(callback: CallbackQuery):
    await callback.answer()
    order_id = int(callback.data.split(":")[1])
    
    async with Local_Session() as session:
        order = await get_order_by_id(session, order_id)
        if not order:
            await callback.message.answer("Заказ не найден.")
            return
        
        if order.status != OrderStatusEnum.PENDING:
            await callback.answer("Этот заказ уже обработан.", show_alert=True)
            return
        
        updated_order = await update_order_status(session, order_id, OrderStatusEnum.CANCELLED)
        if updated_order:
            client = await get_client_by_id(session, updated_order.client_id)
            order_text = format_order_info(updated_order, client)
            await callback.message.edit_text(
                f"❌ <b>Заказ отменен</b>\n\n{order_text}",
                parse_mode="HTML"
            )
        else:
            await callback.message.answer("Ошибка при обновлении статуса заказа.")


@employee_handlers_router.message(F.text == "👤 Профиль")
async def show_employee_profile(message: Message):
    user_id = message.from_user.id
    
    async with Local_Session() as session:
        employee = await get_employee(session, user_id)
        if not employee:
            await message.answer("Ошибка: исполнитель не найден.")
            return
        
        reviews = await get_reviews_by_employee(session, employee.id)
        
        text = (
            f"👤 <b>Ваш профиль:</b>\n\n"
            f"📛 <b>Имя:</b> {employee.first_name} {employee.last_name}\n"
            f"📞 <b>Телефон:</b> {employee.phone}\n"
            f"🎂 <b>Дата рождения:</b> {employee.birth_date}\n"
            f"💼 <b>Направление:</b> {employee.branch.value}\n"
            f"⭐ <b>Рейтинг:</b> {employee.rating}\n"
            f"📊 <b>Отзывов:</b> {employee.total_reviews}\n"
            f"📅 <b>Дата регистрации:</b> {employee.created_at.strftime('%d.%m.%Y')}"
        )
        
        if reviews:
            text += "\n\n📝 <b>Последние отзывы:</b>\n"
            for review in reviews[:5]:
                stars = "⭐" * review.rating
                text += f"\n{stars} ({review.rating}/5)\n"
                if review.comment:
                    text += f"{review.comment}\n"
                text += f"📅 {review.created_at.strftime('%d.%m.%Y')}\n"
        else:
            text += "\n\n📝 Отзывов пока нет."
    
    await message.answer(text, parse_mode="HTML")


@employee_handlers_router.message(F.text == "📊 Статистика")
async def show_employee_statistics(message: Message):
    user_id = message.from_user.id
    
    async with Local_Session() as session:
        employee = await get_employee(session, user_id)
        if not employee:
            await message.answer("Ошибка: исполнитель не найден.")
            return
        
        all_orders = await get_orders_by_employee(session, employee.id)
        pending_orders = await get_orders_by_employee(session, employee.id, OrderStatusEnum.PENDING)
        in_progress_orders = await get_orders_by_employee(session, employee.id, OrderStatusEnum.IN_PROGRESS)
        completed_orders = await get_orders_by_employee(session, employee.id, OrderStatusEnum.COMPLETED)
        cancelled_orders = await get_orders_by_employee(session, employee.id, OrderStatusEnum.CANCELLED)
        
        total_orders = len(all_orders)
        pending_count = len(pending_orders)
        in_progress_count = len(in_progress_orders)
        completed_count = len(completed_orders)
        cancelled_count = len(cancelled_orders)
        
        total_earned = sum(float(order.price) for order in completed_orders)
        
        text = (
            f"📊 <b>Ваша статистика:</b>\n\n"
            f"📋 <b>Всего заказов:</b> {total_orders}\n\n"
            f"📊 <b>По статусам:</b>\n"
            f"⏳ Ожидает подтверждения: {pending_count}\n"
            f"✅ В работе: {in_progress_count}\n"
            f"✅ Завершено: {completed_count}\n"
            f"❌ Отменено: {cancelled_count}\n\n"
            f"💰 <b>Заработано:</b> {total_earned:.2f} USD\n"
            f"⭐ <b>Рейтинг:</b> {employee.rating}\n"
            f"📝 <b>Отзывов:</b> {employee.total_reviews}"
        )
    
    await message.answer(text, parse_mode="HTML")

