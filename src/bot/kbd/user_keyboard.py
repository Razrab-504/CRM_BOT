from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from src.db.enums import BranchEnum

client_kbd = KeyboardButton(text="I am a client 👨🏻‍💼")
emp_kbd = KeyboardButton(text="I am a freelancer 👨🏻‍💻")

client_emp_kbd = ReplyKeyboardMarkup(
    keyboard=[[client_kbd], [emp_kbd]],
    resize_keyboard=True
)


contact_kbd = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Send contact", request_contact=True)], [KeyboardButton(text="Cancel")]],
        resize_keyboard=True
    )


kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Yes", callback_data="confirm_yes"), InlineKeyboardButton(text="❌ No", callback_data="confirm_no")]
    ])


brunch_buttons = [[InlineKeyboardButton(text=b.value, callback_data=f"branch:{b.value}")] for b in BranchEnum]
brunch_markup = InlineKeyboardMarkup(inline_keyboard=brunch_buttons)

clients_buttons = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="🔍 Find freelancer"), KeyboardButton(text="📋 My orders")],
              [KeyboardButton(text="👤 Profile")]],
    resize_keyboard=True
)


EMPLOYEES_PER_PAGE = 5

def create_employees_keyboard(employees: list, page: int = 0, total_count: int = 0) -> InlineKeyboardMarkup:
    keyboard = []
    
    for employee in employees:
        keyboard.append([
            InlineKeyboardButton(text="✅ Select", callback_data=f"emp_select:{employee.id}"),
            InlineKeyboardButton(text="👤 Profile", callback_data=f"emp_profile:{employee.id}")
        ])
    
    pagination_buttons = []
    total_pages = (total_count + EMPLOYEES_PER_PAGE - 1) // EMPLOYEES_PER_PAGE if total_count > 0 else 1
    
    if total_pages > 1:
        if page > 0:
            pagination_buttons.append(InlineKeyboardButton(text="⬅️ Back", callback_data=f"emp_page:{page - 1}"))
        if page < total_pages - 1:
            pagination_buttons.append(InlineKeyboardButton(text="Forward ➡️", callback_data=f"emp_page:{page + 1}"))
        
        if pagination_buttons:
            keyboard.append(pagination_buttons)
            keyboard.append([
                InlineKeyboardButton(text=f"Page {page + 1} of {total_pages}", callback_data="emp_none")
            ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


order_confirm_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="✅ Confirm", callback_data="order_confirm"),
     InlineKeyboardButton(text="❌ Cancel", callback_data="order_cancel")]
])


def create_order_action_keyboard(order_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Approve", callback_data=f"order_approve:{order_id}"),
            InlineKeyboardButton(text="❌ Cancel", callback_data=f"order_cancel_emp:{order_id}")
        ]
    ])


def create_employee_orders_keyboard(orders: list) -> InlineKeyboardMarkup:
    keyboard = []
    for order in orders:
        status_emoji = "⏳" if order.status.value == "PENDING" else "✅" if order.status.value == "IN_PROGRESS" else "❌"
        keyboard.append([
            InlineKeyboardButton(
                text=f"{status_emoji} Order #{order.id} - {order.status.value}",
                callback_data=f"emp_order_view:{order.id}"
            )
        ])
    
    if not keyboard:
        return InlineKeyboardMarkup(inline_keyboard=[])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def create_client_orders_keyboard(orders: list) -> InlineKeyboardMarkup:
    keyboard = []
    for order in orders:
        status_emoji = "⏳" if order.status.value == "PENDING" else "✅" if order.status.value == "IN_PROGRESS" else "❌"
        keyboard.append([
            InlineKeyboardButton(
                text=f"{status_emoji} Order #{order.id} - {order.status.value}",
                callback_data=f"client_order_view:{order.id}"
            )
        ])
    
    if not keyboard:
        return InlineKeyboardMarkup(inline_keyboard=[])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


employee_main_btn = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="📋 My orders"), KeyboardButton(text="📊 Statistics")],
              [KeyboardButton(text="👤 Profile")]],
    resize_keyboard=True
)


def create_complete_order_keyboard(order_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Complete order", callback_data=f"order_complete:{order_id}")
        ]
    ])


def create_rating_keyboard(order_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="⭐", callback_data=f"rating:{order_id}:1"),
            InlineKeyboardButton(text="⭐⭐", callback_data=f"rating:{order_id}:2"),
            InlineKeyboardButton(text="⭐⭐⭐", callback_data=f"rating:{order_id}:3"),
            InlineKeyboardButton(text="⭐⭐⭐⭐", callback_data=f"rating:{order_id}:4"),
            InlineKeyboardButton(text="⭐⭐⭐⭐⭐", callback_data=f"rating:{order_id}:5")
        ]
    ])