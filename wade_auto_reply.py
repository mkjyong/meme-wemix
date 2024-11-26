import os
from autogen import AssistantAgent, UserProxyAgent

os.environ['OPENAI_API_KEY'] = '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'

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
당신은 장난꾸러기야. 입력된 데이터를 기반으로 놀리거나 장난을 쳐줘. 100자 이내로.

데이터: {data}
"""


# 에이전트 생성
assistant = AssistantAgent(
    name="WADE_NAUGHTY",
    llm_config=llm_config
)

user_proxy = UserProxyAgent("user_proxy", code_execution_config=False)


from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# FastAPI 앱 생성
app = FastAPI()


class UserInput(BaseModel):
    user_input: str

@app.post("/process")
async def process_input(input_data: UserInput):
    # 사용자 요청 처리
    user_message = prompt_template.format(
        data=input_data.user_input
    )

    # 프롬프트 실행
    response = user_proxy.initiate_chat(
        assistant,
        message=user_message,
        auto_reply=True,  # 사용자 입력 없이 자동으로 진행
        human_input_mode="auto"  # 사용자 입력 없이 자동 응답
    )

    print("aaa", response)
    return {"response": response}
