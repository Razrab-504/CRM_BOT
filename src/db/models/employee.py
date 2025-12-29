from sqlalchemy.orm import mapped_column, Mapped
from sqlalchemy import TIMESTAMP, DECIMAL, String, Date, Index, text, BigInteger
from src.db.base import Base
from src.db.enums import BranchEnum
from typing import Annotated
import datetime

idpk = Annotated[int, mapped_column(primary_key=True)]
created_at = Annotated[datetime.datetime, 
mapped_column(TIMESTAMP, nullable=False, server_default=text("TIMEZONE('utc', now())"))]


class Employee(Base):
    __tablename__ = "employee"
    
    id: Mapped[idpk]
    telegram_user_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    phone: Mapped[str] = mapped_column(String(30), nullable=False)
    birth_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    branch: Mapped[BranchEnum] = mapped_column(nullable=False)
    rating: Mapped[float] = mapped_column(DECIMAL(3, 2), default=0.00)
    total_reviews: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[created_at]
    
    __table_args__ = (
        Index("idx_employee_telegram_user_id", "telegram_user_id"),
        Index("idx_employee_branch", "branch"),
        Index("idx_employee_rating", "rating"),
    )