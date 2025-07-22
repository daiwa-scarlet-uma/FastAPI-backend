
import os
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from pydantic_settings import BaseSettings
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .db import engine, Base, get_db
from .models import Item

# 项目根目录
BASE_DIR = Path(__file__).parent.parent

# 1. 加载环境配置
class Settings(BaseSettings):
    cors_origins: str = "*"

    class Config:
        env_file = BASE_DIR / ".env"
        env_file_encoding = "utf-8"

settings = Settings()
origins = settings.cors_origins.split(",")

# 2. Lifespan：启动时建表
@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield

app = FastAPI(lifespan=lifespan)

# 3. CORS & 静态文件
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

static_dir = BASE_DIR / "pyservice" / "static"
app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/favicon.ico")
async def favicon():
    return FileResponse(static_dir / "favicon.ico")

# 4. 根路由
@app.get("/")
async def read_root():
    return {"message": "API is up and running"}

# 5. 加法接口
class AddRequest(BaseModel):
    a: float
    b: float

class AddResponse(BaseModel):
    result: float

@app.post("/add", response_model=AddResponse)
@app.post("/add/", response_model=AddResponse)
async def add_numbers(payload: AddRequest):
    return {"result": payload.a + payload.b}

# 6. Item CRUD 接口
class ItemCreate(BaseModel):
    name: str
    price: int

class ItemRead(ItemCreate):
    id: int

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

@app.get("/items/", response_model=list[ItemRead])
async def list_items(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Item))
    return result.scalars().all()
