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
    """
    Create a new user

    Args:
        request (schemas.User): User to create
        db (Session, optional): Database session.

    Returns:
        schemas.ShowUser: User created
    """
    return user.create(request, db)


@router.get("/", status_code=status.HTTP_200_OK, response_model=List[schemas.ShowUser])
def get_users(db: Session = Depends(get_db)):
    """
    Get all users

    Args:
        db (Session, optional): Database session. Defaults to Depends(get_db).

    Returns:
        List[schemas.ShowUser]: List of users
    """
    return user.get_all(db)


@router.get("/{id}", status_code=status.HTTP_200_OK, response_model=schemas.ShowUser)
def get_user_by_id(id: int, db: Session = Depends(get_db)):
    """
    Get a user by id

    Args:
        id (int): User id
        db (Session, optional): Database session. Defaults to Depends(get_db).

    Returns:
        schemas.ShowUser: User
    """
    return user.show(id, db)
