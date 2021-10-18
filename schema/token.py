#!/usr/bin/python3

from datetime import datetime, timedelta
from typing import Optional

from decouple import config
from jose import JWTError, jwt

from schema.schemas import TokenData

# openssl rand -hex 32
SECRET_KEY = "secret" or config("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 or config(
    "ACCESS_TOKEN_EXPIRE_MINUTES", default=60, cast=int
)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """
    Generate JWT token

    Args:
        data (dict): payload
        expires_delta (Optional[timedelta]): token expiration time

    Returns:
        str: JWT token
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode["exp"] = expire
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def verify_token(token: str, credentials_exception):
    """
    Verify JWT token

    Args:
        token (str): JWT token
        credentials_exception (Exception): exception to raise if token is invalid

    Raises:
        credentials_exception: if token is invalid
        credentials_exception: if token is expired
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=ALGORITHM)
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)
    except JWTError:
        raise credentials_exception
