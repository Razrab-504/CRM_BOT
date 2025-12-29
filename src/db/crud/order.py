from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.db.models.order import Order
from src.db.enums import OrderStatusEnum


async def create_order(
    session: AsyncSession,
    client_id: int,
    employee_id: int,
    description: str,
    price: float
) -> Order:
    order = Order(
        client_id=client_id,
        employee_id=employee_id,
        description=description,
        price=price,
        status=OrderStatusEnum.PENDING
    )
    session.add(order)
    await session.flush()
    return order


async def get_order_by_id(session: AsyncSession, order_id: int) -> Order | None:
    stmt = select(Order).where(Order.id == order_id)
    res = await session.execute(stmt)
    return res.scalar_one_or_none()


async def update_order_status(
    session: AsyncSession,
    order_id: int,
    status: OrderStatusEnum
) -> Order | None:
    order = await get_order_by_id(session, order_id)
    if not order:
        return None
    order.status = status
    await session.commit()
    await session.refresh(order)
    return order


async def get_orders_by_employee(session: AsyncSession, employee_id: int, status: OrderStatusEnum | None = None) -> list[Order]:
    stmt = select(Order).where(Order.employee_id == employee_id)
    if status:
        stmt = stmt.where(Order.status == status)
    res = await session.execute(stmt)
    return list(res.scalars().all())


async def get_orders_by_client(session: AsyncSession, client_id: int, status: OrderStatusEnum | None = None) -> list[Order]:
    stmt = select(Order).where(Order.client_id == client_id)
    if status:
        stmt = stmt.where(Order.status == status)
    res = await session.execute(stmt)
    return list(res.scalars().all())

