from sqlalchemy.orm import mapped_column, Mapped
from sqlalchemy import TIMESTAMP, DECIMAL, Index, text, TEXT, ForeignKey
from src.db.base import Base
from src.db.enums import OrderStatusEnum
from typing import Annotated
import datetime


idpk = Annotated[int, mapped_column(primary_key=True)]
created_at = Annotated[datetime.datetime, 
mapped_column(TIMESTAMP, nullable=False, server_default=text("TIMEZONE('utc', now())"))]


class Order(Base):
    __tablename__ = "orders"
    
    id: Mapped[idpk]
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id", ondelete="CASCADE"), nullable=False)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employee.id", ondelete="CASCADE"), nullable=False)
    description: Mapped[str] = mapped_column(TEXT, nullable=False)
    price: Mapped[float] = mapped_column(DECIMAL(10, 2), nullable=False)
    status: Mapped[OrderStatusEnum] = mapped_column(nullable=False, default=OrderStatusEnum.PENDING)
    created_at: Mapped[created_at]
    finished_at: Mapped[datetime.datetime | None] = mapped_column(TIMESTAMP, nullable=True)
    
    
    __table_args__ = (
        Index("idx_client_id", "client_id"),
        Index("idx_employee_id", "employee_id"),
        Index("idx_status", "status"),
        Index("idx_created_at", "created_at")
    )