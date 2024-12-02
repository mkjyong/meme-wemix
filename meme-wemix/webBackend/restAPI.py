import os

from pydantic import BaseModel
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from databases import Database
from sqlalchemy import MetaData, Table, Column, String, BigInteger, DECIMAL, TIMESTAMP, Text, create_engine

# FastAPI 앱 생성
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:1200"],  # 프론트엔드 주소
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MySQL 연결 설정
DATABASE_URL = (
    f"mysql+pymysql://meme-wemix:{os.getenv('mysql_pwd')}@127.0.0.1:3306/meme_wemix"
)
# 데이터베이스와 테이블 정의
database = Database(DATABASE_URL)
metadata = MetaData()

token_info_table = Table(
    "token_info",
    metadata,
    Column("record_id", BigInteger, primary_key=True, autoincrement=True),
    Column("token_addr", String(255), nullable=False),
    Column("name", String(255)),
    Column("symbol", String(50)),
    Column("image_url", String(2083)),
    Column("total_supply", DECIMAL(38, 18)),
    Column("creator_address", String(255)),
    Column("transaction_hash", String(255)),
    Column("created_at", TIMESTAMP),
    Column("description", String(500)),
)
# SQLAlchemy 엔진 생성 (데이터베이스 초기화용)
engine = create_engine(DATABASE_URL)
metadata.create_all(engine)



# 데이터 모델 정의
class Token(BaseModel):
    name: str
    symbol: str
    total_supply: int
    transaction_hash: str


@app.on_event("startup")
async def startup():
    await database.connect()


@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()


@app.get("/api/token/{address}")
async def get_token_info(token_addr: str):
    query = token_info_table.select().where(token_info_table.c.token_addr == token_addr)
    token_info = await database.fetch_one(query)
    if token_info:
        return token_info

    raise HTTPException(status_code=404, detail="Token not found")

@app.get("/api/tokens")
async def list_tokens():
    query = token_info_table.select()
    all_tokens = await database.fetch_all(query)
    return all_tokens
