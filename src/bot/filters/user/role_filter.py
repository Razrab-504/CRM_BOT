from typing import Union
from aiogram.filters import BaseFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from src.db.session import Local_Session
from src.db.crud.client import get_client
from src.db.crud.employee import get_employee


class RoleFilter(BaseFilter):
    def __init__(self, role: str):
        self.role = role

    async def __call__(self, event: Union[Message, CallbackQuery], state: FSMContext) -> bool:
        data = await state.get_data()
        if data.get("role") == self.role:
            return True
        
        user_id = event.from_user.id if hasattr(event, 'from_user') else None
        if not user_id:
            return False
        
        async with Local_Session() as session:
            if self.role == "client":
                client = await get_client(session=session, telegram_user_id=user_id)
                return client is not None
            elif self.role == "employee":
                employee = await get_employee(session=session, telegram_user_id=user_id)
                return employee is not None
        
        return False