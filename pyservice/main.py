
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
from .models import Operation

# 项目根目录
BASE_DIR = Path(__file__).parent.parent

# 1. 加载配置
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

# 3. CORS & 静态
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

# 5. 加法并存库
class AddRequest(BaseModel):
    a: int
    b: int

class AddResponse(BaseModel):
    result: int

@app.post("/add", response_model=AddResponse)
@app.post("/add/", response_model=AddResponse)
async def add_numbers(
    payload: AddRequest,
    db: AsyncSession = Depends(get_db)
):
    # 计算
    res = payload.a + payload.b
    # 存入 Operation 表
    op = Operation(a=payload.a, b=payload.b, result=res)
    db.add(op)
    await db.commit()
    return {"result": res}

# 6. 查看运算历史
class OperationRead(BaseModel):
    id: int
    a: int
    b: int
    result: int

@app.get("/operations/", response_model=list[OperationRead])
async def list_operations(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Operation))
    return result.scalars().all()
