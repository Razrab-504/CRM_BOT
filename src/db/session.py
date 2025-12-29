from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from src.db.config import settings

engine = create_async_engine(url=settings.DATABASE_URL, echo=True,)

Local_Session = async_sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)