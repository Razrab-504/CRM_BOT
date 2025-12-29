from sqlalchemy.orm import mapped_column, Mapped
from sqlalchemy import TIMESTAMP, CheckConstraint, Index, text, TEXT, ForeignKey, SMALLINT
from src.db.base import Base
from typing import Annotated
import datetime


idpk = Annotated[int, mapped_column(primary_key=True)]
created_at = Annotated[datetime.datetime, 
mapped_column(TIMESTAMP, nullable=False, server_default=text("TIMEZONE('utc', now())"))]


class Review(Base):
    __tablename__ = "reviews"
    
    id: Mapped[idpk]
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id", ondelete="CASCADE"), nullable=False)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employee.id", ondelete="CASCADE"), nullable=False)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    rating: Mapped[int] = mapped_column(SMALLINT, nullable=False)
    comment: Mapped[str] = mapped_column(TEXT)
    created_at: Mapped[created_at]
    
    
    __table_args__ = (
        Index("ix_reviews_employee_id", "employee_id"),
        Index("ix_reviews_order_id", "order_id"),
        Index("ix_reviews_rating", "rating"),
        CheckConstraint("rating BETWEEN 1 AND 5", name="chk_review_rating")
    )
