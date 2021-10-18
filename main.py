#!/usr/bin/python3

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.responses import HTMLResponse

from core import auth, blog, user
from database.configuration import engine
from models import models

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
    """
    Home page

    Args:
        request (Request): Request object

    Returns:
        HTMLResponse: HTML response
    """
    return templates.TemplateResponse("index.html", {"request": request})
