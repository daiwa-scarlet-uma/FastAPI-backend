
# pyservice/main.py

import os
from dotenv import load_dotenv
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from pydantic_settings import BaseSettings
from sqlalchemy import Column, Integer, String, select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from contextlib import asynccontextmanager

# ── 1. 加载 .env ─────────────────────────────────────

base_dir = os.path.dirname(__file__) + "/../"
load_dotenv(os.path.join(os.path.dirname(__file__), "../.env"))

class Settings(BaseSettings):
    cors_origins: str = "*"

    class Config:
        env_file = os.path.join(base_dir, ".env")
        env_file_encoding = "utf-8"

settings = Settings()
origins = settings.cors_origins.split(",")

# ── 2. 数据库配置 ─────────────────────────────────────

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("请设置 DATABASE_URL 环境变量")

# 异步引擎
engine = create_async_engine(DATABASE_URL, echo=True)

# 异步 Session 工厂（命名参数以消除类型警告）
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# ORM 基类
Base = declarative_base()

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

# ── 3. 定义模型和 Pydantic Schema ───────────────────────

class Item(Base):
    __tablename__ = "items"
    id    = Column(Integer, primary_key=True, index=True)
    name  = Column(String, index=True, nullable=False)
    price = Column(Integer, nullable=False)

class ItemCreate(BaseModel):
    name: str
    price: int

class ItemRead(ItemCreate):
    id: int

class AddRequest(BaseModel):
    a: float
    b: float

class AddResponse(BaseModel):
    result: float

# ── 4. Lifespan 处理启动时建表 ────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动：创建表
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # 关闭：无操作

app = FastAPI(lifespan=lifespan)

# ── 5. 中间件 & 静态文件 ─────────────────────────────────

# 静态文件
static_path = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=static_path), name="static")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# favicon
@app.get("/favicon.ico")
async def favicon():
    return FileResponse(os.path.join(static_path, "favicon.ico"))

# 根路由
@app.get("/")
async def read_root():
    return {"message": "API is up and running"}

# 加法接口
@app.post("/add", response_model=AddResponse)
@app.post("/add/", response_model=AddResponse)
async def add_numbers(payload: AddRequest):
    return {"result": payload.a + payload.b}

# 创建 Item
@app.post("/items/", response_model=ItemRead)
async def create_item(
    data: ItemCreate,
    db: AsyncSession = Depends(get_db)
):
    item = Item(name=data.name, price=data.price)
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return item

# 列出 Items
@app.get("/items/", response_model=list[ItemRead])
async def list_items(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Item))
    return result.scalars().all()
