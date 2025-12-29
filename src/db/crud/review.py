from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from src.db.models.review import Review
from src.db.models.employee import Employee


async def create_review(
    session: AsyncSession,
    client_id: int,
    employee_id: int,
    order_id: int,
    rating: int,
    comment: str
) -> Review:
    review = Review(
        client_id=client_id,
        employee_id=employee_id,
        order_id=order_id,
        rating=rating,
        comment=comment
    )
    session.add(review)
    await session.flush()
    await session.commit()
    return review


async def get_reviews_by_employee(session: AsyncSession, employee_id: int) -> list[Review]:
    stmt = select(Review).where(Review.employee_id == employee_id).order_by(Review.created_at.desc())
    res = await session.execute(stmt)
    return list(res.scalars().all())


async def get_review_by_order(session: AsyncSession, order_id: int) -> Review | None:
    stmt = select(Review).where(Review.order_id == order_id)
    res = await session.execute(stmt)
    return res.scalar_one_or_none()


async def update_employee_rating(session: AsyncSession, employee_id: int) -> Employee | None:
    employee = await session.get(Employee, employee_id)
    if not employee:
        return None
    
    stmt = select(func.avg(Review.rating), func.count(Review.id)).where(Review.employee_id == employee_id)
    res = await session.execute(stmt)
    avg_rating, total_reviews = res.one()
    
    if avg_rating is not None:
        employee.rating = float(avg_rating)
        employee.total_reviews = int(total_reviews)
    else:
        employee.rating = 0.0
        employee.total_reviews = 0
    
    await session.commit()
    await session.refresh(employee)
    return employee

