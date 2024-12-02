import os
import pymysql

from pydantic import BaseModel
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from databases import Database

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
db_config = {
    "host": "127.0.0.1",          # 데이터베이스 호스트
    "user": "meme-wemix",         # MySQL 사용자명
    "password": os.getenv("mysql_pwd"),  # MySQL 비밀번호
    "database": "meme_wemix",     # 데이터베이스 이름
    "charset": "utf8mb4"          # 문자 집합
}
# 데이터베이스 연결 함수
def get_db_connection():
    return pymysql.connect(**db_config)


@app.get("/api/token/{address}")
async def get_token_info(token_addr: str):
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            # 데이터 조회 쿼리
            query = "SELECT * FROM token_info WHERE token_addr = %s"
            cursor.execute(query, (token_addr,))
            result = cursor.fetchone()

        if result:
            # 컬럼 이름에 따라 응답 구성
            return {
                "record_id": result[0],
                "token_addr": result[1],
                "name": result[2],
                "symbol": result[3],
                "image_url": result[4],
                "total_supply": result[5],
                "creator_address": result[6],
                "transaction_hash": result[7],
                "created_at": result[8],
                "description": result[9],
            }

        raise HTTPException(status_code=404, detail="Token not found")
    finally:
        connection.close()

@app.get("/api/tokens")
async def list_tokens():
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            # 모든 토큰 조회 쿼리
            query = "SELECT * FROM token_info"
            cursor.execute(query)
            results = cursor.fetchall()

        # 결과를 리스트로 반환
        tokens = []
        for row in results:
            tokens.append({
                "record_id": row[0],
                "token_addr": row[1],
                "name": row[2],
                "symbol": row[3],
                "image_url": row[4],
                "total_supply": row[5],
                "creator_address": row[6],
                "transaction_hash": row[7],
                "created_at": row[8],
                "description": row[9],
            })

        return tokens
    finally:
        connection.close()
