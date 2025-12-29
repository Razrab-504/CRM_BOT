from src.db.base import Base
from src.db.session import engine
import asyncio

from src.db.models.employee import Employee
from src.db.models.client import Client
from src.db.models.review import Review
from src.db.models.order import Order


async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
        

asyncio.run(create_tables())
