from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

app = FastAPI()

# 정적 파일 경로 설정
app.mount("/static", StaticFiles(directory="../templates"), name="static")

templates = Jinja2Templates(directory="../templates")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})


@app.get("/token/{address}", response_class=HTMLResponse)
async def render_clanker_page(request: Request, address: str):
    return templates.TemplateResponse("test.html", {"request": request, "address": address})
