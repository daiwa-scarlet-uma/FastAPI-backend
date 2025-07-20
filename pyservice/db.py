# pyservice/db.py

import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base

# 1. 本地加载 .env（Render 上依赖环境变量，无需 .env）
load_dotenv(os.path.join(os.path.dirname(__file__), "../.env"))

# 2. 读取环境变量
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("未设置 DATABASE_URL 环境变量！")

# 3. 创建异步 Engine
engine = create_async_engine(DATABASE_URL, echo=True)

# 4. Session 工厂
AsyncSessionLocal = sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False
)

# 5. 基类
Base = declarative_base()

# 6. 依赖注入
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
