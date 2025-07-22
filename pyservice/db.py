import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from pathlib import Path

# 加载 .env
base_dir = Path(__file__).parent.parent
load_dotenv(base_dir / ".env")

# 读取并清洗 URL
raw_url = os.getenv("DATABASE_URL", "")
if not raw_url:
    raise RuntimeError("请设置 DATABASE_URL 环境变量")

db_url = raw_url.split("?", 1)[0]  # 去掉所有查询参数
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql+asyncpg://", 1)

# 创建异步引擎，确保 SSL
engine = create_async_engine(
    db_url,
    echo=True,
    connect_args={"ssl": True},
)

# 异步 Session 工厂
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# 声明基类
Base = declarative_base()

# 依赖注入 Session
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
