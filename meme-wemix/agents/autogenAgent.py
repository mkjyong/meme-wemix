import os
import json
import uuid
import boto3
import requests
import pymysql

from datetime import datetime
from autogen import AssistantAgent, UserProxyAgent, ConversableAgent
from fastapi import FastAPI, HTTPException, File, UploadFile, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from blockchain import deploy_token, blockchain_tool, check_connection
from mimetypes import guess_type
from io import BytesIO

os.environ['OPENAI_API_KEY'] = os.getenv("OPENAI_API_KEY")
# AWS S3 설정
S3_BUCKET_NAME = "meme-wemix-test"
AWS_REGION = "ap-southeast-2"  # 서울 리전 예시
AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_KEY")

# Boto3 클라이언트 초기화
s3_client = boto3.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
    region_name=AWS_REGION
)

# db_connection = pymysql.connect(
#     host="127.0.0.1",          # 데이터베이스 호스트
#     user="meme-wemix",               # MySQL 사용자명
#     password=os.getenv("mysql_pwd"),  # MySQL 비밀번호
#     database="meme_wemix",  # 데이터베이스 이름
#     charset="utf8mb4"          # 문자 집합
# )

llm_config = {
    "config_list": [
        {
            "model": "gpt-4o-mini",
            "api_key": os.environ.get("OPENAI_API_KEY")
        }
    ]
}


# 템플릿 기반 프롬프트
prompt_template = """
당신은 범용적인 친절한 대화형 ai assistant입니다. 사용자의 요청에 따라 아래와 같은 역할을 수행할 수 있습니다. 그리고 항상 영어를 써.
그리고 필수적으로 모든 응답 끝과 tool 사용 결과에 'TERMINATE' 를 함께 첨부해

1. "사용자가 제공하는 밈코인과 관련된 정보나 아이디어를 바탕으로, 해당 밈코인의 고유한 이름과 심볼을 생성해야 합니다. 3가지 추천을 제공해주고 유저에게 선택지를 제공하세요.
이름과 심볼은 다음 형식으로 제시해주세요:
- 이름: [제안된 이름]
- 심볼: [제안된 심볼과 그 설명]

사용자가 주는 키워드나 주제를 반영하여 창의적이고 기억에 남는 이름과 심볼을 제안하세요.
그리고 제안 중에 어떤걸 사용하게 할건지 다시 확인하세요

2. 사용자가 다른 주제로 대화를 요청하면, 친절하고 유익한 대화로 응답하세요. 전문적이거나 일상적인 주제 모두 다룰 수 있습니다.

3. 당신은 사용자의 요청에 따라 다양한 도구를 사용할 수 있는 AI입니다. 다음과 같은 도구를 사용할 수 있습니다:
   1) **blockchain_tool**: 밈토큰을 블록체인에 배포하고 정보를 데이터베이스에 기록합니다.
   - 이 도구는 오직 사용자가 배포하겠다고 명확히 동의한 경우에만 실행됩니다.



**밈코인 분석 요청 시 응답 형식**:
{ "analysis": "여기에 감지한 언어로 분석 내용을 작성하세요. (200자 이내)", "token_name": "생성된 토큰 이름", "token_symbol": "생성된 토큰 심볼명" }

**기타 대화 요청 시**:
- 일반 대화 형식으로 답변하세요.
"""

# 에이전트 생성
assistant = ConversableAgent(
    name="MEME_WEMIX",
    system_message=prompt_template,
    llm_config=llm_config
)

# Blockchain tool 등록
assistant.register_for_llm(
    name="blockchain_tool",
    description="Deploys a token on the blockchain and records it in the database."
)(blockchain_tool)



# Session management (stores conversation state per user)
user_agents = {}

# FastAPI 앱 생성
app = FastAPI()
# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 모든 출처 허용 (보안이 중요한 경우 특정 도메인으로 제한)
    allow_credentials=True,
    allow_methods=["*"],  # 모든 HTTP 메서드 허용
    allow_headers=["*"],  # 모든 HTTP 헤더 허용
)


class UserInput(BaseModel):
    user_input: str
    image_url: str = None  # image_url을 선택적으로 처리

@app.post("/chat")
async def chat_conversation(request: Request, input_data: UserInput):
    user_id = str(request.client.host)

    try:
        uploaded_image_url = None

        if input_data.image_url and input_data.image_url.strip():
            response = requests.get(input_data.image_url, stream=True)
            if response.status_code == 200:
                # 파일 이름 추출
                file_name = os.path.basename(input_data.image_url)
                image_key = f"uploads/{uuid.uuid4()}-{file_name}"

                # Content-Type 자동 추출
                content_type, _ = guess_type(file_name)
                if not content_type:
                    content_type = "application/octet-stream"  # 기본값

                # 메모리에 데이터 저장
                image_data = BytesIO(response.content)

                # S3에 업로드
                s3_client.put_object(
                    Bucket=S3_BUCKET_NAME,
                    Key=image_key,
                    Body=image_data.getvalue(),  # BytesIO 객체에서 바이트 데이터 추출
                    ContentType=content_type  # Content-Type 설정
                )

                # 업로드된 이미지 URL
                uploaded_image_url = f"https://{S3_BUCKET_NAME}.s3.{AWS_REGION}.amazonaws.com/{image_key}"


        # 사용자 세션 확인 및 초기화
        if user_id not in user_agents:
            # 새로운 대화 시작
            user_proxy = ConversableAgent("user_proxy",  human_input_mode="NEVER", is_termination_msg=lambda msg: msg.get("content") is not None and "TERMINATE" in msg["content"])
            user_proxy.register_for_execution(name="blockchain_tool")(blockchain_tool)
            user_agents[user_id] = user_proxy
        else:
            # 기존 대화 이어가기
            user_proxy = user_agents[user_id]

        # initiate_chat 호출
        response = user_proxy.initiate_chat(
            assistant,
            message=input_data.user_input,  # 사용자 입력
            clear_history=False,  # 대화 내역 유지
        )


        # insert_token_info(
        #     token_addr=result['contract_address'],
        #     name=token_name,
        #     symbol=token_symbol,
        #     image_url=uploaded_image_url,
        #     total_supply = "0",
        #     creator_address="",
        #     transaction_hash="0x" + result['transaction_hash'],
        #     description = analysis
        # )

        return {"response": response.summary}
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON format in response")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in chat_conversation: {str(e)}")


@app.post("/end")
async def end_conversation(request: Request):
    user_id = str(request.client.host)

    if user_id in user_agents:
        del user_agents[user_id]
        return {"message": "Session ended."}
    else:
        return {"message": "Success"}





# 생성된 정보를 MySQL에 삽입하는 함수
def insert_token_info(token_addr, name, symbol, image_url, total_supply, creator_address, transaction_hash, description):
    try:
        with db_connection.cursor() as cursor:
            # 삽입 SQL 쿼리
            sql = """
            INSERT INTO token_info (
                token_addr, name, symbol, image_url, total_supply, creator_address, transaction_hash, created_at, description
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            # 현재 시간
            created_at = datetime.now()

            # 데이터 삽입
            cursor.execute(sql, (token_addr, name, symbol, image_url, total_supply, creator_address, transaction_hash, created_at, description))

        # 변경 사항 커밋
        db_connection.commit()
        print("Token information inserted successfully!")

    except Exception as e:
        print(f"Failed to insert token info: {e}")

    finally:
        db_connection.close()
