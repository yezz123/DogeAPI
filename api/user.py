#!/usr/bin/python3

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from models import models
from schema import schemas
from schema.hash import Hash


def create(request: schemas.User, db: Session):
    """
    Create a new user

    Args:
        request (schemas.User): User data
        db (Session): Database session

    Returns:
        models.User: User created
    """
    hashedPassword = Hash.bcrypt(request.password)
    user = models.User(name=request.name, email=request.email, password=hashedPassword)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def show(id: int, db: Session):
    """
    Show a user

    Args:
        id (int): User id
        db (Session): Database session

    Raises:
        HTTPException: User not found

    Returns:
        models.User: User found
    """
    user = db.query(models.User).filter(models.User.id == id).first()
    if not user:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, detail=f"User with id {id} not found"
        )
    return user


def get_all(db: Session):
    """
    Get all users

    Args:
        db (Session): Database session

    Returns:
        list: List of users
    """
    return db.query(models.User).all()
