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
        client_phone = f"📞 <b>Client phone:</b> {client.phone}\n"
    else:
        client_info = "Unknown client"
        client_phone = ""
    
    status_text = {
        "PENDING": "⏳ Waiting for confirmation",
        "IN_PROGRESS": "✅ In progress",
        "COMPLETED": "✅ Completed",
        "CANCELLED": "❌ Cancelled"
    }
    status_display = status_text.get(order.status.value, order.status.value)
    
    return (
        f"📋 <b>Order #{order.id}</b>\n\n"
        f"👤 <b>Client:</b> {client_info}\n"
        f"{client_phone}"
        f"📝 <b>Description:</b> {order.description}\n"
        f"💰 <b>Budget:</b> {order.price} USD\n"
        f"📊 <b>Status:</b> {status_display}\n"
        f"📅 <b>Created:</b> {order.created_at.strftime('%d.%m.%Y %H:%M')}"
    )


@employee_handlers_router.message(F.text == "📋 My orders")
async def show_employee_orders(message: Message):
    user_id = message.from_user.id
    
    async with Local_Session() as session:
        employee = await get_employee(session, user_id)
        if not employee:
            await message.answer("Error: freelancer not found.")
            return

        orders = await get_orders_by_employee(session, employee.id)

    if not orders:
        await message.answer("You have no orders yet.")
        return

    text = "📋 <b>Your orders:</b>\n\nSelect an order to view:"
    keyboard = create_employee_orders_keyboard(orders)
    await message.answer(text, reply_markup=keyboard, parse_mode="HTML")


@employee_handlers_router.callback_query(F.data.startswith("emp_order_view:"))
async def view_employee_order(callback: CallbackQuery):
    await callback.answer()
    order_id = int(callback.data.split(":")[1])

    async with Local_Session() as session:
        order = await get_order_by_id(session, order_id)
        if not order:
            await callback.message.answer("Order not found.")
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
            await callback.message.answer("Order not found.")
            return

        if order.status != OrderStatusEnum.PENDING:
            await callback.answer("This order has already been processed.", show_alert=True)
            return
        
        updated_order = await update_order_status(session, order_id, OrderStatusEnum.IN_PROGRESS)
        if updated_order:
            client = await get_client_by_id(session, updated_order.client_id)
            order_text = format_order_info(updated_order, client)
            await callback.message.edit_text(
                f"✅ <b>Order confirmed!</b>\n\n{order_text}",
                parse_mode="HTML"
            )
        else:
            await callback.message.answer("Error updating order status.")


@employee_handlers_router.callback_query(F.data.startswith("order_cancel_emp:"))
async def cancel_order_by_employee(callback: CallbackQuery):
    await callback.answer()
    order_id = int(callback.data.split(":")[1])
    
    async with Local_Session() as session:
        order = await get_order_by_id(session, order_id)
        if not order:
            await callback.message.answer("Order not found.")
            return

        if order.status != OrderStatusEnum.PENDING:
            await callback.answer("This order has already been processed.", show_alert=True)
            return
        
        updated_order = await update_order_status(session, order_id, OrderStatusEnum.CANCELLED)
        if updated_order:
            client = await get_client_by_id(session, updated_order.client_id)
            order_text = format_order_info(updated_order, client)
            await callback.message.edit_text(
                f"❌ <b>Order cancelled</b>\n\n{order_text}",
                parse_mode="HTML"
            )
        else:
            await callback.message.answer("Error updating order status.")


@employee_handlers_router.message(F.text == "👤 Profile")
async def show_employee_profile(message: Message):
    user_id = message.from_user.id

    async with Local_Session() as session:
        employee = await get_employee(session, user_id)
        if not employee:
            await message.answer("Error: freelancer not found.")
            return
        
        reviews = await get_reviews_by_employee(session, employee.id)
        
        text = (
            f"👤 <b>Your profile:</b>\n\n"
            f"📛 <b>Name:</b> {employee.first_name} {employee.last_name}\n"
            f"📞 <b>Phone:</b> {employee.phone}\n"
            f"🎂 <b>Date of birth:</b> {employee.birth_date}\n"
            f"💼 <b>Direction:</b> {employee.branch.value}\n"
            f"⭐ <b>Rating:</b> {employee.rating}\n"
            f"📊 <b>Reviews:</b> {employee.total_reviews}\n"
            f"📅 <b>Registration date:</b> {employee.created_at.strftime('%d.%m.%Y')}"
        )
        
        if reviews:
            text += "\n\n📝 <b>Latest reviews:</b>\n"
            for review in reviews[:5]:
                stars = "⭐" * review.rating
                text += f"\n{stars} ({review.rating}/5)\n"
                if review.comment:
                    text += f"{review.comment}\n"
                text += f"📅 {review.created_at.strftime('%d.%m.%Y')}\n"
        else:
            text += "\n\n📝 No reviews yet."
    
    await message.answer(text, parse_mode="HTML")


@employee_handlers_router.message(F.text == "📊 Statistics")
async def show_employee_statistics(message: Message):
    user_id = message.from_user.id
    
    async with Local_Session() as session:
        employee = await get_employee(session, user_id)
        if not employee:
            await message.answer("Error: freelancer not found.")
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
            f"📊 <b>Your statistics:</b>\n\n"
            f"📋 <b>Total orders:</b> {total_orders}\n\n"
            f"📊 <b>By status:</b>\n"
            f"⏳ Waiting for confirmation: {pending_count}\n"
            f"✅ In progress: {in_progress_count}\n"
            f"✅ Completed: {completed_count}\n"
            f"❌ Cancelled: {cancelled_count}\n\n"
            f"💰 <b>Earned:</b> {total_earned:.2f} USD\n"
            f"⭐ <b>Rating:</b> {employee.rating}\n"
            f"📝 <b>Reviews:</b> {employee.total_reviews}"
        )
    
    await message.answer(text, parse_mode="HTML")

