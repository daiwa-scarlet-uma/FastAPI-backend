
import os
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from pydantic_settings import BaseSettings
from sqlalchemy import Column, Integer, String, select
from sqlalchemy.ext.asyncio import AsyncSession

from .db import engine, Base, get_db

# ── 1. 配置 & 环境加载 ─────────────────────────────────────────

# 根目录
BASE_DIR = Path(__file__).parent.parent

class Settings(BaseSettings):
    cors_origins: str = "*"

    class Config:
        env_file = BASE_DIR / ".env"
        env_file_encoding = "utf-8"

settings = Settings()
origins = settings.cors_origins.split(",")

# ── 2. Lifespan：启动时自动建表 ──────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # 关闭时可加清理逻辑

app = FastAPI(lifespan=lifespan)

# ── 3. 中间件 & 静态文件 ────────────────────────────────────────

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静态文件挂载
static_dir = BASE_DIR / "pyservice" / "static"
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# favicon
@app.get("/favicon.ico")
async def favicon():
    return FileResponse(static_dir / "favicon.ico")

# ── 4. 数据模型 & Pydantic Schema ─────────────────────────────────

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

# ── 5. 路由 ──────────────────────────────────────────────────────

@app.get("/")
async def read_root():
    return {"message": "API is up and running"}

@app.post("/add", response_model=AddResponse)
@app.post("/add/", response_model=AddResponse)
async def add_numbers(req: AddRequest):
    return {"result": req.a + req.b}

@app.post("/items/", response_model=ItemRead)
async def create_item(data: ItemCreate, db: AsyncSession = Depends(get_db)):
    item = Item(name=data.name, price=data.price)
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return item

@app.get("/items/", response_model=list[ItemRead])
async def list_items(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Item))
    return result.scalars().all()
