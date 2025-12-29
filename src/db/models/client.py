from sqlalchemy.orm import mapped_column, Mapped
from sqlalchemy import TIMESTAMP, String, Date, Index, text, BigInteger
from src.db.base import Base
from typing import Annotated
import datetime


idpk = Annotated[int, mapped_column(primary_key=True)]
created_at = Annotated[datetime.datetime, 
mapped_column(TIMESTAMP, nullable=False, server_default=text("TIMEZONE('utc', now())"))]


class Client(Base):
    __tablename__ = "clients"
    
    id: Mapped[idpk]
    telegram_user_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    phone: Mapped[str] = mapped_column(String(30), nullable=False)
    birth_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    created_at: Mapped[created_at]

    __table_args__ = (
        Index("idx_clients_telegram_user_id", "telegram_user_id"),
    )