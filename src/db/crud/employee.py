from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from src.db.models.employee import Employee
from src.db.enums import BranchEnum


async def get_employee(session: AsyncSession, telegram_user_id: int) -> Employee | None:
    stmt = select(Employee).where(Employee.telegram_user_id == telegram_user_id)
    res = await session.execute(stmt)
    return res.scalar_one_or_none()


async def create_employee(session: AsyncSession, telegram_user_id: int, first_name: str, last_name: str, phone: str, birth_date, branch: BranchEnum) -> Employee:
    employee = Employee(
        telegram_user_id=telegram_user_id,
        first_name=first_name,
        last_name=last_name,
        phone=phone,
        birth_date=birth_date,
        branch=branch,
    )
    session.add(employee)
    await session.commit()
    await session.refresh(employee)
    return employee


async def get_all_employees(session: AsyncSession) -> list[Employee]:
    stmt = select(Employee)
    res = await session.execute(stmt)
    return res.scalars().all()


async def get_employees_paginated(session: AsyncSession, offset: int = 0, limit: int = 5, branch: BranchEnum | None = None) -> list[Employee]:
    stmt = select(Employee)
    if branch:
        stmt = stmt.where(Employee.branch == branch)
    stmt = stmt.offset(offset).limit(limit)
    res = await session.execute(stmt)
    return res.scalars().all()


async def get_employees_count(session: AsyncSession, branch: BranchEnum | None = None) -> int:
    stmt = select(func.count(Employee.id))
    if branch:
        stmt = stmt.where(Employee.branch == branch)
    res = await session.execute(stmt)
    return res.scalar_one()


async def get_employee_by_id(session, employee_id: int) -> Employee | None:
    stmt = select(Employee).where(Employee.id == employee_id)
    res = await session.execute(stmt)
    return res.scalar_one_or_none()