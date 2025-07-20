import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base

# 1. 本地加载 .env（生产环境请通过平台的环境变量配置）
load_dotenv(os.path.join(os.path.dirname(__file__), "../.env"))

# 2. 读取并清洗 DATABASE_URL
raw_url = os.getenv("DATABASE_URL", "")
if not raw_url:
    raise RuntimeError("未找到 DATABASE_URL 环境变量")

# 去掉所有查询参数（? 后面的部分）
db_url = raw_url.split("?", 1)[0]

# 如果是旧的 postgres:// 前缀，改为 sqlalchemy asyncpg 可识别的格式
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql+asyncpg://", 1)

# 3. 创建异步 Engine，并用 connect_args 开启 SSL
engine = create_async_engine(
    db_url,
    echo=True,
    connect_args={"ssl": True},
)

# 4. 创建异步 Session 工厂
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# 5. ORM 基类
Base = declarative_base()

# 6. 依赖注入：提供 session
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
