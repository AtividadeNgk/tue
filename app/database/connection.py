from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from app.config import settings

# Engine assíncrono
if 'sqlite' in settings.DATABASE_URL:
    async_engine = create_async_engine(
        settings.DATABASE_URL,
        echo=False,
        connect_args={"check_same_thread": False}
    )
else:
    async_engine = create_async_engine(
        settings.DATABASE_URL,
        echo=False,
        pool_size=settings.DB_POOL_SIZE,
        max_overflow=settings.DB_MAX_OVERFLOW,
        pool_pre_ping=True,
        pool_recycle=3600
    )

AsyncSessionLocal = sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Engine síncrono
if 'sqlite' in settings.DATABASE_SYNC_URL:
    sync_engine = create_engine(
        settings.DATABASE_SYNC_URL,
        echo=False,
        connect_args={"check_same_thread": False}
    )
else:
    sync_engine = create_engine(
        settings.DATABASE_SYNC_URL,
        echo=False,
        pool_size=settings.DB_POOL_SIZE
    )

async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

def init_db():
    """Criar tabelas no banco"""
    from app.database.models import Base
    Base.metadata.create_all(bind=sync_engine)
    print("✅ Tabelas criadas com sucesso!")

if __name__ == "__main__":
    init_db()