
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from fastapi.responses import FileResponse
from pydantic import BaseModel         # ← 正确引入
from pydantic_settings import BaseSettings
import os
from fastapi.staticfiles import StaticFiles

base_dir = os.path.dirname(__file__)  # 当前 main.py 所在目录
static_path = os.path.join(base_dir, "static")




class Settings(BaseSettings):
    cors_origins: str = "*"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
origins = settings.cors_origins.split(",")

app = FastAPI()

# 挂载静态文件目录
app.mount("/static", StaticFiles(directory=static_path), name="static")

# CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 请求体和响应模型
class AddRequest(BaseModel):
    a: float
    b: float

class AddResponse(BaseModel):
    result: float

# 根路由
@app.get("/")
async def read_root():
    return {"message": "API is up and running"}

# favicon 路由
@app.get("/favicon.ico")
async def favicon():
    return FileResponse("static/favicon.ico")

# 加法接口
@app.post("/add", response_model=AddResponse)
@app.post("/add/", response_model=AddResponse)
async def add_numbers(payload: AddRequest):
    return {"result": payload.a + payload.b}
