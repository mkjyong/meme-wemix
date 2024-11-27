from pydantic import BaseModel
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware


# 토큰 데이터를 저장할 메모리 기반 데이터베이스 (간단한 예)
tokens = []

# FastAPI 앱 생성
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:1200"],  # 프론트엔드 주소
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 데이터 모델 정의
class Token(BaseModel):
    name: str
    symbol: str
    total_supply: int
    transaction_hash: str

@app.post("/tokens")
async def add_token(token: Token):
    tokens.append(token.dict())  # 토큰 추가
    return {"message": "Token added successfully"}

@app.get("/tokens")
async def list_tokens():
    return tokens  # 모든 토큰 반환


# 예제 데이터
clankers = {
    "0x2f5E79469EbFfA1Ea73030cb23eB921C7BcB7091": {
        "name": "WADE TEST COIN",
        "symbol": "WTC",
        "description": "It is wade test coin.",
        "image_url": "https://example.com/image1.png"
    },
    "0x3a5E79469EbFfA1Ea73030cb23eB921C7BcB7092": {
        "name": "WEMADE FOREVER COIN",
        "symbol": "WFC",
        "description": "Another unique Clanker.",
        "image_url": "https://example.com/image2.png"
    }
}

@app.get("/api/clanker/{address}")
async def get_clanker(address: str):
    if address in clankers:
        return clankers[address]
    raise HTTPException(status_code=404, detail="Clanker not found")