import os
import json

from autogen import AssistantAgent, UserProxyAgent, ConversableAgent
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from blockchain import deploy_token, check_connection


os.environ['OPENAI_API_KEY'] = os.getenv("OPENAI_API_KEY")

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
주어진 데이터가 은유적 표현이라도 잘 이해할 수 있으면 좋겠어.

데이터: {data}

이후, 데이터를 기반으로 토큰 이름과 심볼을 생성하세요. 
생성된 결과는 반드시 아래의 형식으로만 작성하세요:

{{
  "analysis": "여기에 분석 내용을 작성하세요. (200자 이내)",
  "token_name": "생성된 토큰 이름",
  "token_symbol": "생성된 토큰 심볼"
}}
"""


# 에이전트 생성
assistant = AssistantAgent(
    name="MEME_WEMIX",
    llm_config=llm_config
)

user_proxy = UserProxyAgent("user_proxy", code_execution_config=False)




# FastAPI 앱 생성
app = FastAPI()


class UserInput(BaseModel):
    user_input: str

@app.post("/process")
async def process_input(input_data: UserInput):
    try:
        # 사용자 요청 처리
        user_message = prompt_template.format(
            data=input_data.user_input
        )

        # 프롬프트 실행
        response = user_proxy.initiate_chat(
            assistant,
            message=user_message,
            human_input_mode="NEVER",  # Never ask for human input.
            max_turns=1  # 한 번의 대화로 종료
        )

        # 응답에서 JSON 파싱
        parsed_data = json.loads(response.summary)

        # 각 키의 값을 가져오기
        analysis = parsed_data["analysis"]
        token_name = parsed_data["token_name"]
        token_symbol = parsed_data["token_symbol"]
        tx_hash = deploy_token(token_name, token_symbol, total_supply=1000000)


        # 출력
        return {
            "analysis": analysis,
            "token_name": token_name,
            "token_symbol": token_symbol,
            "transaction_hash": "0x" + tx_hash
        }
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON format in response")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

