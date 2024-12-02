import os
import json
import uuid
import boto3
import requests
import pymysql

from datetime import datetime
from autogen import AssistantAgent, UserProxyAgent, ConversableAgent
from fastapi import FastAPI, HTTPException, File, UploadFile
from pydantic import BaseModel
from blockchain import deploy_token, check_connection
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

db_connection = pymysql.connect(
    host="127.0.0.1",          # 데이터베이스 호스트
    user="meme-wemix",               # MySQL 사용자명
    password=os.getenv("mysql_pwd"),  # MySQL 비밀번호
    database="meme_wemix",  # 데이터베이스 이름
    charset="utf8mb4"          # 문자 집합
)

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
당신의 역할은 주어진 데이터를 게임, 커뮤니티, 밈코인을 주제로 이 코인이 가질 효과를 분석하여 전문가 어조로 제공하는 것입니다.
입력된 데이터의 언어를 감지해서 감지된 언어로 분석을 작성하세요
그 후  데이터를 기반으로 토큰 이름과 심볼을 생성하세요.

**반드시 아래 JSON 형식에 따라 정확히 응답하세요. JSON 형식 외의 텍스트는 포함하지 마세요.**

응답 형식:
{
  "analysis": "여기에 감지한 언어로 분석 내용을 작성하세요. (200자 이내)",
  "token_name": "생성된 토큰 이름",
  "token_symbol": "생성된 토큰 심볼"
}
"""


# 에이전트 생성
assistant = AssistantAgent(
    name="MEME_WEMIX",
    system_message=prompt_template,
    llm_config=llm_config
)

user_proxy = UserProxyAgent("user_proxy", code_execution_config=False)




# FastAPI 앱 생성
app = FastAPI()


class UserInput(BaseModel):
    user_input: str
    image_url: str = None  # image_url을 선택적으로 처리

@app.post("/process")
async def process_input(input_data: UserInput):
    try:
        uploaded_image_url = None

        if input_data.image_url.strip():  # URL이 비어 있지 않을 경우
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
            else:
                raise HTTPException(status_code=400, detail="Failed to fetch the image from the provided URL")



        # 프롬프트 실행
        response = user_proxy.initiate_chat(
            assistant,
            message=input_data.user_input,
            human_input_mode="NEVER",  # Never ask for human input.
            max_turns=1  # 한 번의 대화로 종료
        )

        # 응답에서 JSON 파싱
        parsed_data = json.loads(response.summary)

        # 각 키의 값을 가져오기
        analysis = parsed_data["analysis"]
        token_name = parsed_data["token_name"]
        token_symbol = parsed_data["token_symbol"]
        result = deploy_token(token_name, token_symbol, total_supply=1000000)

        insert_token_info(
            token_addr=result['contract_address'],
            name=token_name,
            symbol=token_symbol,
            image_url=uploaded_image_url,
            total_supply = "0",
            creator_address="",
            transaction_hash="0x" + result['transaction_hash'],
            description = analysis
        )

        # 출력
        return {
            "analysis": analysis,
            "token_addr" : token_addr,
            "token_name": token_name,
            "token_symbol": token_symbol,
            "transaction_hash": "0x" + result['transaction_hash'],
            "token_page" : "sss/" + result['contract_address'], #token addr로 바꿔야함
            "image_url": uploaded_image_url  # 업로드된 이미지 URL 반환
        }
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON format in response")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))




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
