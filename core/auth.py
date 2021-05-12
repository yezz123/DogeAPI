#!/usr/bin/python3

from fastapi.security.oauth2 import OAuth2PasswordRequestForm
from schema.token import ACCESS_TOKEN_EXPIRE_MINUTES, create_access_token
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from schema import schemas
from models import models
from database import configuration
from sqlalchemy.orm import Session
from schema.hash import Hash


router = APIRouter(
    prefix="/login",
    tags=["Authentication"],
)

@router.post("/")
def login(request: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(configuration.get_db)):
    user: schemas.User = db.query(models.User).filter(models.User.email == request.username).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Invalid Credentials")
    if not Hash.verify(user.password, request.password):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Incorrect password")


    # access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}
    )

    # generate JWT token and return
    return {"access_token": access_token, "token_type": "bearer"}
