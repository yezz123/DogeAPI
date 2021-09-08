#!/usr/bin/python3

from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from api import user
from database import configuration
from schema import schemas

router = APIRouter(tags=["Users"], prefix="/users")
get_db = configuration.get_db


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=schemas.ShowUser)
def create_user(request: schemas.User, db: Session = Depends(get_db)):
    return user.create(request, db)


@router.get("/", status_code=status.HTTP_200_OK, response_model=List[schemas.ShowUser])
def get_users(db: Session = Depends(get_db)):
    return user.get_all(db)


@router.get("/{id}", status_code=status.HTTP_200_OK, response_model=schemas.ShowUser)
def get_user_by_id(id: int, db: Session = Depends(get_db)):
    return user.show(id, db)
