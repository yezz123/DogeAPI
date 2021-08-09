#!/usr/bin/python3

from fastapi import FastAPI, Request
from starlette.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from models import models
from database.configuration import engine
from core import blog, user, auth


models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="DogeAPI",
    description="API with high performance built with FastAPI & SQLAlchemy, help to improve connection with your Backend Side.",
    version="1.0.0",
)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

app.include_router(auth.router)
app.include_router(blog.router)
app.include_router(user.router)


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})
