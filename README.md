<p align="center">
  <img  src="https://raw.githubusercontent.com/yezz123/DogeAPI/main/Images/logo.png?token=AMSGFK4PUTRSRCQWVEDDA7TAUTHDY">
</p>
<p align="center">
   <img src="https://img.shields.io/badge/Dev-Yezz123-green?style"/>
   <img src="https://img.shields.io/badge/language-python-blue?style"/>
   <img src="https://img.shields.io/github/license/yezz123/DogeAPI"/>
   <img src="https://img.shields.io/github/stars/yezz123/DogeAPI"/>
   <img src="https://img.shields.io/github/forks/yezz123/DogeAPI"/>
   <img src="https://img.shields.io/static/v1?label=%F0%9F%8C%9F&message=If%20Useful&style=style=flat&color=BC4E99" alt="Star Badge"/>
   <img src="https://visitor-badge.laobi.icu/badge?page_id=yezz123.Pretty-Readme">
</p>

# DogeAPI 🌙:

## Introduction 👋🏻

- [FastApi](https://fastapi.tiangolo.com/) is built on a Python framework called Starlette which is a lightweight ASGI framework/toolkit, which is itself built on Uvicorn.
- Ideal for building high performance asyncio services with seriously impressive performance.
- That why DogeAPI is here, an API with high performance built with FastAPI & SQLAlchemy, help to improve connection with your Backend Side and stay relate using `SQLite3` & a secure Schema Based on [Python-Jose](https://github.com/mpdavis/python-jose) a JavaScript Object Signing and Encryption implementation in Python.

## I use 🤔

- [fastapi](https://fastapi.tiangolo.com/) : FastAPI is a modern, fast (high-performance), web framework for building APIs with Python 3.6+ based on standard Python type hints.
- [uvicorn](https://www.uvicorn.org/) : Uvicorn is a lightning-fast ASGI server implementation, using uvloop and httptools.
- [sqlalchemy](https://www.sqlalchemy.org/) : SQLAlchemy is the Python SQL toolkit and Object Relational Mapper that gives application developers the full power and flexibility of SQL.
- [passlib](https://passlib.readthedocs.io/en/stable/) : Passlib is a password hashing library for Python 2 & 3, which provides cross-platform implementations of over 30 password hashing algorithms, as well as a framework for managing existing password hashes.
- [bcrypt](https://github.com/pyca/bcrypt/) : Good password hashing for your software and your servers.
- [python-jose](https://github.com/mpdavis/python-jose) : The JavaScript Object Signing and Encryption (JOSE) technologies - JSON Web Signature (JWS), JSON Web Encryption (JWE), JSON Web Key (JWK), and JSON Web Algorithms (JWA) - collectively can be used to encrypt and/or sign content using a variety of algorithms.
- [python-multipart](https://github.com/andrew-d/python-multipart) : streaming multipart parser for Python.

## Installation 💼

- With a simple steps you can install DogeAPI.
- clone the repository:

```bash
git clone https://github.com/yezz123/DogeAPI.git
```

- Create & activate a python3 [virtual environment](https://docs.python.org/3/tutorial/venv.html) (optional, but very recommended).
- Install requirements:

```bash
pip install -r requirements.txt
```

- Run the app locally :

```bash
uvicorn main:app --reload
```

- Port already in use? Close the other app, or use a difference port:

```bash
uvicorn main:app --port 8001 --reload
```

## Into Code 🐍

- If you want to Set environment variables you need to check [token.py](schema/token.py) and use :

```bash
openssl rand -hex 32
```

- To get a string like this.

```python
SECRET_KEY = "a4ee1c733a80a5ac8824ac21b90ee6ae0158aee6642880fb2675929f99b1a677"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
```

- I Use a simple Model to implement with Database & the default configuration.
- This for the Blog Table

```python
class Blog(Base):
    __tablename__ = "blogs"
    id = Column(Integer, primary_key=True,index=True)
    title = Column(String)
    body = Column(String)
    user_id = Column(Integer, ForeignKey("users.id"))
    creator = relationship("User", back_populates="blogs")
```

- This for The Users Table

```python
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True,index=True)
    name = Column(String)
    email = Column(String)
    password = Column(String)
    blogs = relationship("Blog", back_populates="creator")
```

- For database i use `SQLAlchemy.ORM` to create a sessions.

```python
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()
```

## Contributing ⭐

- Read [CONTRIBUTING.md](https://github.com/yezz123/DogeAPI/blob/main/CONTRIBUTING.md)
- Contributions are welcome!
- Please share any features, and add unit tests! Use the pull request and issue systems to contribute.

## Reference 

- [chrisjsimpson/fastapi](https://github.com/chrisjsimpson/fastapi)
- [Additional Responses in OpenAPI](https://fastapi.tiangolo.com/advanced/additional-responses/)
- [OAuth2 scopes](https://fastapi.tiangolo.com/advanced/security/oauth2-scopes/)
- [Main Class](http://andrew-d.github.io/python-multipart/api.html#main-class)
- [pyca/bcrypt](https://github.com/pyca/bcrypt/)
- [Walkthrough & Tutorials](https://passlib.readthedocs.io/en/stable/narr/index.html)
- [The SQLAlchemy Session - In Depth](https://youtu.be/PKAdehPHOMo)
- [Fire-Up Your Backend With FastApi Starlette And Uvicorn](https://ra-6446.medium.com/fire-up-your-backend-with-fastapi-starlette-and-uvicorn-2a1861101d75)
- [Build and Secure an API in Python with FastAPI](https://developer.okta.com/blog/2020/12/17/build-and-secure-an-api-in-python-with-fastapi)

## Credits & Thanks 🏆

<p align="center">
    <a href="https://yassertahiri.medium.com/">
    <img alt="Medium" src="https://img.shields.io/badge/Medium%20-%23000000.svg?&style=for-the-badge&logo=Medium&logoColor=white"/></a>
    <a href="https://twitter.com/THyasser1">
    <img alt="Twitter" src="https://img.shields.io/badge/Twitter%20-%231DA1F2.svg?&style=for-the-badge&logo=Twitter&logoColor=white"</a>
    <a href="https://discord.gg/2x32TdfB57">
    <img alt="Discord" src="https://img.shields.io/badge/Discord%20-%237289DA.svg?&style=for-the-badge&logo=discord&logoColor=white"/></a>
</p>