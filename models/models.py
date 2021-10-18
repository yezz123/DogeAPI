#!/usr/bin/python3

from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from database.configuration import Base


class Blog(Base):
    """
    Blog class

    Args:
        Base (sqlalchemy.ext.declarative.api.Base): Base class
    """

    __tablename__ = "blogs"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    body = Column(String)
    user_id = Column(Integer, ForeignKey("users.id"))
    creator = relationship("User", back_populates="blogs")


class User(Base):
    """
    User class

    Args:
        Base (sqlalchemy.ext.declarative.api.Base): Base class
    """

    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    email = Column(String)
    password = Column(String)
    blogs = relationship("Blog", back_populates="creator")
