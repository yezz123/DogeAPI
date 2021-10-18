#!/usr/bin/python3

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from models import models
from schema import schemas


def get_all(db: Session):
    """
    Get all blogs

    Args:
        db (Session): Database session

    Returns:
        List[models.Blog]: List of blogs
    """
    return db.query(models.Blog).all()


def create(request: schemas.Blog, db: Session):
    """
    Create a new blog

    Args:
        request (schemas.Blog): Blog object
        db (Session): Database session

    Returns:
        models.Blog: Blog object
    """
    new_blog = models.Blog(title=request.title, body=request.body, user_id=1)
    db.add(new_blog)
    db.commit()
    db.refresh(new_blog)
    return new_blog


def destroy(id: int, db: Session):
    """
    Delete a blog

    Args:
        id (int): Blog id
        db (Session): Database session

    Raises:
        HTTPException: 404 not found

    Returns:
        str: Success message
    """
    blog_to_delete = db.query(models.Blog).filter(models.Blog.id == id)

    if not blog_to_delete.first():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Blog with id {id} not found.",
        )
    blog_to_delete.delete(synchronize_session=False)
    db.commit()
    return {"done"}


def update(id: int, request: schemas.Blog, db: Session):
    """
    Update a blog

    Args:
        id (int): Blog id
        request (schemas.Blog): Blog object
        db (Session): Database session

    Raises:
        HTTPException: 404 not found

    Returns:
        models.Blog: Blog object
    """
    blog = db.query(models.Blog).filter(models.Blog.id == id)
    if not blog.first():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Blog with id {id} not found"
        )
    blog.update(request.__dict__)
    db.commit()
    return "updated"


def show(id: int, db: Session):
    """
    Get a blog

    Args:
        id (int): Blog id
        db (Session): Database session

    Raises:
        HTTPException: 404 not found

    Returns:
        models.Blog: Blog object
    """
    blog = db.query(models.Blog).filter(models.Blog.id == id).first()
    if blog:
        return blog
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Blog with the id {id} is not available",
        )
