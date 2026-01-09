from aiogram import F, Router, Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from src.bot.filters.user.role_filter import RoleFilter
from src.db.crud.employee import get_employees_paginated, get_employees_count, get_employee_by_id
from src.db.crud.client import get_client
from src.db.crud.order import create_order, get_orders_by_client, get_order_by_id, update_order_status
from src.db.crud.review import create_review, get_review_by_order, update_employee_rating, get_reviews_by_employee
from src.bot.kbd.user_keyboard import create_employees_keyboard, brunch_markup, order_confirm_kb, create_client_orders_keyboard, create_complete_order_keyboard, create_rating_keyboard
from src.db.session import Local_Session
from src.db.enums import BranchEnum, OrderStatusEnum

client_handlers_router = Router()
client_handlers_router.message.filter(RoleFilter("client"))
client_handlers_router.callback_query.filter(RoleFilter("client"))

EMPLOYEES_PER_PAGE = 5


class CreateOrder(StatesGroup):
    description = State()
    price = State()
    confirm = State()


class CreateReview(StatesGroup):
    rating = State()
    comment = State()


def format_employee_info(employee) -> str:
    return (f"👤 <b>{employee.first_name} {employee.last_name}</b>\n"
            f"📞 Phone: {employee.phone}\n"
            f"🎂 Date of birth: {employee.birth_date}\n"
            f"💼 Branch: {employee.branch.value}\n"
            f"⭐ Rating: {employee.rating}\n"
            f"📊 Reviews: {employee.total_reviews}")


@client_handlers_router.message(RoleFilter("client"), F.text=="🔍 Find freelancer")
async def find_employee_cmd(message: Message):
    await message.answer("Choose direction/specialization:", reply_markup=brunch_markup)


@client_handlers_router.callback_query(F.data.startswith("branch:"))
async def select_branch(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    branch_value = callback.data.split(":", 1)[1]
    
    try:
        branch = BranchEnum(branch_value)
    except ValueError:
        await callback.answer("Invalid direction", show_alert=True)
        return
    
    page = 0
    await state.update_data(employees_page=page, selected_branch=branch_value)
    
    async with Local_Session() as session:
        employees = await get_employees_paginated(session=session, offset=page * EMPLOYEES_PER_PAGE, limit=EMPLOYEES_PER_PAGE, branch=branch)
        total_count = await get_employees_count(session=session, branch=branch)
    
    if not employees:
        await callback.message.edit_text(f"No freelancers found in direction {branch.value}")
        return
    
    text = f"📋 <b>List of freelancers ({branch.value}):</b>\n\n"
    for employee in employees:
        text += format_employee_info(employee) + "\n\n"
    
    keyboard = create_employees_keyboard(employees, page=page, total_count=total_count)
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")


@client_handlers_router.callback_query(F.data.startswith("emp_page:"))
async def paginate_employees(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    page = int(callback.data.split(":")[1])
    await state.update_data(employees_page=page)
    
    data = await state.get_data()
    branch_value = data.get("selected_branch")
    branch = None
    if branch_value:
        try:
            branch = BranchEnum(branch_value)
        except ValueError:
            pass
    
    async with Local_Session() as session:
        employees = await get_employees_paginated(session=session, offset=page * EMPLOYEES_PER_PAGE, limit=EMPLOYEES_PER_PAGE, branch=branch)
        total_count = await get_employees_count(session=session, branch=branch)
    
    if not employees:
        await callback.message.edit_text("Freelancers not found")
        return

    branch_text = f" ({branch.value})" if branch else ""
    text = f"📋 <b>List of freelancers{branch_text}:</b>\n\n"
    for employee in employees:
        text += format_employee_info(employee) + "\n\n"
    
    keyboard = create_employees_keyboard(employees, page=page, total_count=total_count)
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")



@client_handlers_router.callback_query(F.data.startswith("emp_select:"))
async def select_employee(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    employee_id = int(callback.data.split(":")[1])
    
    async with Local_Session() as session:
        employee = await get_employee_by_id(session, employee_id)
    
    if not employee:
        await callback.answer("Worker not found", show_alert=True)
        return

    await state.update_data(employee_id=employee_id)
    await state.set_state(CreateOrder.description)
    await callback.message.answer(
        "Describe your task:",
        reply_markup=ReplyKeyboardRemove()
    )


@client_handlers_router.callback_query(F.data.startswith("emp_profile:"))
async def show_employee_profile(callback: CallbackQuery):
    await callback.answer()
    employee_id = int(callback.data.split(":")[1])
    
    async with Local_Session() as session:
        employee = await get_employee_by_id(session, employee_id)
        if not employee:
            await callback.answer("Worker not found", show_alert=True)
            return

        reviews = await get_reviews_by_employee(session, employee_id)

        text = "👤 <b>Freelancer profile:</b>\n\n" + format_employee_info(employee)

        if reviews:
            text += "\n\n📝 <b>Reviews:</b>\n"
            for review in reviews[:10]:
                stars = "⭐" * review.rating
                text += f"\n{stars} ({review.rating}/5)\n"
                if review.comment:
                    text += f"{review.comment}\n"
                text += f"📅 {review.created_at.strftime('%d.%m.%Y')}\n"
        else:
            text += "\n\n📝 No reviews yet."
    
    await callback.message.answer(text, parse_mode="HTML")


@client_handlers_router.message(F.text == "👤 Profile")
async def show_client_profile(message: Message):
    user_id = message.from_user.id

    async with Local_Session() as session:
        client = await get_client(session, user_id)
        if not client:
            await message.answer("Error: client not found.")
            return
        
        all_orders = await get_orders_by_client(session, client.id)
        completed_orders = await get_orders_by_client(session, client.id, OrderStatusEnum.COMPLETED)
        
        total_orders = len(all_orders)
        completed_count = len(completed_orders)
        
        text = (
            f"👤 <b>Your profile:</b>\n\n"
            f"📛 <b>Name:</b> {client.first_name} {client.last_name}\n"
            f"📞 <b>Phone:</b> {client.phone}\n"
            f"🎂 <b>Date of birth:</b> {client.birth_date}\n"
            f"📅 <b>Registration date:</b> {client.created_at.strftime('%d.%m.%Y')}\n\n"
            f"📊 <b>Order statistics:</b>\n"
            f"📋 Total orders: {total_orders}\n"
            f"✅ Completed: {completed_count}"
        )
    
    await message.answer(text, parse_mode="HTML")


@client_handlers_router.callback_query(F.data == "emp_none")
async def do_nothing(callback: CallbackQuery):
    await callback.answer()


@client_handlers_router.message(CreateOrder.description)
async def process_description(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("Please describe your task in text.")
        return

    await state.update_data(description=message.text.strip())
    await state.set_state(CreateOrder.price)
    await message.answer("Specify the approximate budget (in USD):")


@client_handlers_router.message(CreateOrder.price)
async def process_price(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("Please specify the budget as a number.")
        return

    try:
        price = float(message.text.strip())
        if price <= 0:
            await message.answer("Budget must be a positive number. Try again:")
            return
    except ValueError:
        await message.answer("Invalid format. Specify budget as a number (e.g., 5000):")
        return
    
    await state.update_data(price=price)
    
    data = await state.get_data()
    employee_id = data.get("employee_id")
    
    async with Local_Session() as session:
        employee = await get_employee_by_id(session, employee_id)
        client = await get_client(session, message.from_user.id)
    
    if not employee or not client:
        await message.answer("Error: could not find data. Try again.")
        await state.clear()
        return
    
    description = data.get("description")
    price_value = data.get("price")
    
    confirm_text = (
        f"Confirm order:\n\n"
        f"👨‍💻 <b>Freelancer:</b> {employee.first_name} {employee.last_name}\n"
        f"📝 <b>Task:</b> {description}\n"
        f"💰 <b>Budget:</b> {price_value} USD\n"
        f"📱 <b>Freelancer phone:</b> {employee.phone}"
    )
    
    await state.set_state(CreateOrder.confirm)
    await message.answer(confirm_text, reply_markup=order_confirm_kb, parse_mode="HTML")


@client_handlers_router.callback_query(F.data == "order_confirm")
async def confirm_order(callback: CallbackQuery, state: FSMContext, bot: Bot):
    await callback.answer()
    
    try:
        current_state = await state.get_state()
        if current_state != CreateOrder.confirm:
            await callback.answer("Order has already been processed or cancelled", show_alert=True)
            return

        data = await state.get_data()
        employee_id = data.get("employee_id")
        description = data.get("description")
        price = data.get("price")

        if not employee_id or not description or price is None:
            await callback.message.answer("Error: not all data filled. Try again.")
            await state.clear()
            return
        
        async with Local_Session() as session:
            client = await get_client(session, callback.from_user.id)
            employee = await get_employee_by_id(session, employee_id)
            
            if not client or not employee:
                await callback.message.answer("Error: could not find data. Try again.")
                await state.clear()
                return
            
            employee_name = f"{employee.first_name} {employee.last_name}"
            employee_telegram_id = employee.telegram_user_id
            client_name = f"{client.first_name} {client.last_name}"
            client_phone = client.phone
            
            order = await create_order(
                session=session,
                client_id=client.id,
                employee_id=employee.id,
                description=description,
                price=price
            )
            order_id = order.id
            await session.commit()
        
        try:
            await bot.send_message(
                employee_telegram_id,
                f"🔔 <b>Новый заказ #{order_id}!</b>\n\n"
                f"👤 <b>Клиент:</b> {client_name}\n"
                f"📞 <b>Телефон клиента:</b> {client_phone}\n"
                f"📝 <b>Задача:</b> {description}\n"
                f"💰 <b>Бюджет:</b> {price} USD\n\n"
                f"Перейдите в раздел <b>📋 Мои заказы</b> для принятия решения.",
                parse_mode="HTML"
            )
        except Exception as e:
            print(f"⚠️ Не удалось отправить уведомление исполнителю {employee_telegram_id}: {e}")
        
        try:
            await callback.message.edit_text(
<<<<<<< HEAD
                f"✅ <b>Order created!</b>\n\n"
                f"Your order has been sent to freelancer {employee_name}.\n"
                f"Wait for confirmation.",
=======
                f"✅ <b>Заказ #{order_id} создан!</b>\n\n"
                f"Ваш заказ отправлен исполнителю {employee_name}.\n"
                f"Ожидайте подтверждения.",
>>>>>>> 6e871ce3d37db7d1f162c7fe1160dc98c168151f
                parse_mode="HTML"
            )
        except Exception:
            await callback.message.answer(
<<<<<<< HEAD
                f"✅ <b>Order created!</b>\n\n"
                f"Your order has been sent to freelancer {employee_name}.\n"
                f"Wait for confirmation.",
=======
                f"✅ <b>Заказ #{order_id} создан!</b>\n\n"
                f"Ваш заказ отправлен исполнителю {employee_name}.\n"
                f"Ожидайте подтверждения.",
>>>>>>> 6e871ce3d37db7d1f162c7fe1160dc98c168151f
                parse_mode="HTML"
            )
        
        await state.clear()
        
    except Exception as e:
        await callback.message.answer(f"An error occurred while creating the order. Try again later.")
        await state.clear()
        print(f"❌ Ошибка в confirm_order: {e}")


@client_handlers_router.callback_query(F.data == "order_cancel")
async def cancel_order_creation(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    try:
        await callback.message.edit_text("❌ Order creation cancelled.")
    except Exception:
        await callback.message.answer("❌ Order creation cancelled.")
    await state.clear()


def format_client_order_info(order, employee=None) -> str:
    employee_info = f"{employee.first_name} {employee.last_name}" if employee else "Unknown freelancer"
    status_text = {
        "PENDING": "⏳ Waiting for freelancer confirmation",
        "IN_PROGRESS": "✅ Confirmed by freelancer - in progress",
        "COMPLETED": "✅ Completed",
        "CANCELLED": "❌ Cancelled by freelancer"
    }
    status_display = status_text.get(order.status.value, order.status.value)
    
    return (
        f"📋 <b>Order #{order.id}</b>\n\n"
        f"👨‍💻 <b>Freelancer:</b> {employee_info}\n"
        f"📝 <b>Description:</b> {order.description}\n"
        f"💰 <b>Budget:</b> {order.price} USD\n"
        f"📊 <b>Status:</b> {status_display}\n"
        f"📅 <b>Created:</b> {order.created_at.strftime('%d.%m.%Y %H:%M')}"
    )


@client_handlers_router.message(F.text == "📋 My orders")
async def show_client_orders(message: Message):
    user_id = message.from_user.id

    async with Local_Session() as session:
        client = await get_client(session, user_id)
        if not client:
            await message.answer("Error: client not found.")
            return

        orders = await get_orders_by_client(session, client.id)

    if not orders:
        await message.answer("You have no orders yet.")
        return

    text = "📋 <b>Your orders:</b>\n\nSelect an order to view:"
    keyboard = create_client_orders_keyboard(orders)
    await message.answer(text, reply_markup=keyboard, parse_mode="HTML")


@client_handlers_router.callback_query(F.data.startswith("client_order_view:"))
async def view_client_order(callback: CallbackQuery):
    await callback.answer()
    order_id = int(callback.data.split(":")[1])

    async with Local_Session() as session:
        order = await get_order_by_id(session, order_id)
        if not order:
            await callback.message.answer("Order not found.")
            return
        
        employee = await get_employee_by_id(session, order.employee_id)
        order_text = format_client_order_info(order, employee)
        
        existing_review = await get_review_by_order(session, order_id)
        
        if order.status == OrderStatusEnum.IN_PROGRESS and not existing_review:
            keyboard = create_complete_order_keyboard(order_id)
            await callback.message.edit_text(order_text, reply_markup=keyboard, parse_mode="HTML")
        elif order.status == OrderStatusEnum.COMPLETED and not existing_review:
            keyboard = create_rating_keyboard(order_id)
            await callback.message.edit_text(
                f"{order_text}\n\n✅ Order completed. Please leave a review:",
                reply_markup=keyboard,
                parse_mode="HTML"
            )
        else:
            await callback.message.edit_text(order_text, parse_mode="HTML")


@client_handlers_router.callback_query(F.data.startswith("order_complete:"))
async def complete_order(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    order_id = int(callback.data.split(":")[1])
    
    async with Local_Session() as session:
        order = await get_order_by_id(session, order_id)
        if not order:
            await callback.message.answer("Order not found.")
            return

        if order.status != OrderStatusEnum.IN_PROGRESS:
            await callback.answer("This order cannot be completed.", show_alert=True)
            return

        existing_review = await get_review_by_order(session, order_id)
        if existing_review:
            await callback.answer("Review for this order already left.", show_alert=True)
            return
        
        updated_order = await update_order_status(session, order_id, OrderStatusEnum.COMPLETED)
        if updated_order:
            await state.update_data(order_id=order_id, employee_id=order.employee_id, client_id=order.client_id)
            await state.set_state(CreateReview.rating)
            
            keyboard = create_rating_keyboard(order_id)
            await callback.message.edit_text(
                "✅ <b>Order completed!</b>\n\n"
                "Please leave a review of the freelancer's work.\n"
                "Choose a rating (1 to 5 stars):",
                reply_markup=keyboard,
                parse_mode="HTML"
            )
        else:
            await callback.message.answer("Error completing order.")


@client_handlers_router.callback_query(F.data.startswith("rating:"))
async def select_rating(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    parts = callback.data.split(":")
    order_id = int(parts[1])
    rating = int(parts[2])
    
    async with Local_Session() as session:
        order = await get_order_by_id(session, order_id)
        if not order:
            await callback.message.answer("Order not found.")
            return

        existing_review = await get_review_by_order(session, order_id)
        if existing_review:
            await callback.answer("Review for this order already left.", show_alert=True)
            return
        
        await state.update_data(
            rating=rating,
            order_id=order_id,
            employee_id=order.employee_id,
            client_id=order.client_id
        )
    
    await state.set_state(CreateReview.comment)
    await callback.message.edit_text(
        f"You selected {rating} {'stars' if rating > 1 else 'star'} ⭐\n\n"
        "Now write a comment for the review:"
    )


@client_handlers_router.message(CreateReview.comment)
async def process_review_comment(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("Please write the comment in text.")
        return
    
    comment = message.text.strip()
    data = await state.get_data()
    order_id = data.get("order_id")
    rating = data.get("rating")
    employee_id = data.get("employee_id")
    client_id = data.get("client_id")
    
    if not all([order_id, rating, employee_id, client_id]):
        await message.answer("Error: not all data filled. Try again.")
        await state.clear()
        return

    async with Local_Session() as session:
        review = await create_review(
            session=session,
            client_id=client_id,
            employee_id=employee_id,
            order_id=order_id,
            rating=rating,
            comment=comment
        )

        await update_employee_rating(session, employee_id)

    await message.answer(
        f"✅ <b>Thank you for the review!</b>\n\n"
        f"Your review has been successfully saved.",
        parse_mode="HTML"
    )
    await state.clear()
