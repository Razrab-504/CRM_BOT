from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.db.models.client import Client


async def get_client(session: AsyncSession, telegram_user_id: int) -> Client | None:
    stmt = select(Client).where(Client.telegram_user_id==telegram_user_id)
    res = await session.execute(stmt)
    client = res.scalar_one_or_none()
    return client


async def create_client(session: AsyncSession, telegram_user_id: int, first_name: str, last_name: str, phone: str, birth_date) -> Client:
    client = Client(
        telegram_user_id=telegram_user_id,
        first_name=first_name,
        last_name=last_name,
        phone=phone,
        birth_date=birth_date
    )
    session.add(client)
    await session.commit()
    await session.refresh(client)
    return client


async def get_client_by_id(session: AsyncSession, client_id: int) -> Client | None:
    stmt = select(Client).where(Client.id == client_id)
    res = await session.execute(stmt)
    return res.scalar_one_or_none()
