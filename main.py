#!/usr/bin/python3

import sys
from fastapi import FastAPI
from starlette.responses import HTMLResponse
from models import models
from database.configuration import engine
from core import blog, user, auth


models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="DogeAPI",
    description="DogeApi Backend",
    version="1.0.0",
)

app.include_router(blog.router)
app.include_router(user.router)
app.include_router(auth.router)


@app.get("/", response_class=HTMLResponse)
def index():
    return """
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta http-equiv="X-UA-Compatible" content="IE=edge" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <link
      rel="shortcut icon"
      type="image/icon"
      href="https://www.yezz.me/assets/css/Ico/icon.png"
    />
    <style>
      * {
        box-sizing: border-box;
      }
      *::before,
      *::after {
        box-sizing: border-box;
      }

      body {
        display: flex;
        align-items: center;
        justify-content: center;
        margin: 0;
        min-height: 100vh;
        background: #000000;
      }

      #container {
        display: flex;
        align-items: center;
        justify-content: center;
        width: 6.25rem;
        height: 6.25rem;
      }

      button {
        position: relative;
        display: inline-block;
        cursor: pointer;
        outline: none;
        border: 0;
        vertical-align: middle;
      }
      button.face-button {
        width: 6.25rem;
        height: 6.25rem;
        border-radius: 50%;
        background: #fdda5f;
        box-shadow: inset 2px -4px 18px #fd9744;
      }

      .face-container {
        position: relative;
        display: block;
        width: 40px;
        height: 20px;
        margin: auto;
      }

      .eye {
        position: absolute;
        height: 0.5rem;
        width: 0.5rem;
        background: #2a2927;
        border-radius: 50%;
        -webkit-animation: eyeBlink 3200ms linear infinite;
        animation: eyeBlink 3200ms linear infinite;
      }
      .eye.left {
        left: 0;
      }
      .eye.right {
        left: 2rem;
      }

      .mouth {
        position: absolute;
        top: 1.125rem;
        left: 0.8rem;
        width: 1rem;
        height: 0.125rem;
        background: #2a2927;
        border-radius: 0;
      }

      .eye,
      .mouth {
        box-shadow: inset 1px 2px 4px #121110;
      }

      .face-button:hover .mouth,
      .face-button:active .mouth {
        left: 1rem;
        width: 0.5rem;
        height: 0.4rem;
        border-radius: 1rem 1rem 0.125rem 0.125rem;
      }

      .face-button:hover .eye,
      .face-button:active .eye {
        height: 0.375rem;
        width: 0.375rem;
        box-shadow: 0 0 0 0.25rem #fff;
      }

      @-webkit-keyframes eyeBlink {
        0%,
        30%,
        36%,
        100% {
          transform: scale(1);
        }
        32%,
        34% {
          transform: scale(1, 0);
        }
      }

      @keyframes eyeBlink {
        0%,
        30%,
        36%,
        100% {
          transform: scale(1);
        }
        32%,
        34% {
          transform: scale(1, 0);
        }
      }
    </style>
    <title>DogeAPI</title>
  </head>
  <body>
    <div id="container">
      <a href="/docs">
        <button class="face-button">
          <span class="face-container">
            <span class="eye left"></span>
            <span class="eye right"></span>
            <span class="mouth"></span>
          </span>
        </button>
      </a>
    </div>
    <script>
      const faceButton = document.querySelector(".face-button");
      const faceContainer = document.querySelector(".face-container");
      const containerCoords = document.querySelector("#container");
      const mouseCoords = containerCoords.getBoundingClientRect();

      faceButton.addEventListener("mousemove", function (e) {
        const mouseX = e.pageX - containerCoords.offsetLeft;
        const mouseY = e.pageY - containerCoords.offsetTop;

        TweenMax.to(faceButton, 0.3, {
          x: ((mouseX - mouseCoords.width / 2) / mouseCoords.width) * 50,
          y: ((mouseY - mouseCoords.height / 2) / mouseCoords.width) * 50,
          ease: Power4.easeOut,
        });
      });

      faceButton.addEventListener("mousemove", function (e) {
        const mouseX = e.pageX - containerCoords.offsetLeft;
        const mouseY = e.pageY - containerCoords.offsetTop;

        TweenMax.to(faceContainer, 0.3, {
          x: ((mouseX - mouseCoords.width / 2) / mouseCoords.width) * 25,
          y: ((mouseY - mouseCoords.height / 2) / mouseCoords.width) * 25,
          ease: Power4.easeOut,
        });
      });

      faceButton.addEventListener("mouseenter", function (e) {
        TweenMax.to(faceButton, 0.3, {
          scale: 0.975,
        });
      });

      faceButton.addEventListener("mouseleave", function (e) {
        TweenMax.to(faceButton, 0.3, {
          x: 0,
          y: 0,
          scale: 1,
        });

        TweenMax.to(faceContainer, 0.3, {
          x: 0,
          y: 0,
          scale: 1,
        });
      });
    </script>
  </body>
</html>
"""
