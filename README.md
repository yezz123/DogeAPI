![DOGEAPI](docs/Images/header.svg)

<p align="center">
   <img src="https://img.shields.io/badge/Dev-Yezz123-green?style"/>
   <img src="https://img.shields.io/badge/language-python-blue?style"/>
   <img src="https://img.shields.io/github/stars/yezz123/DogeAPI"/>
   <img src="https://img.shields.io/github/forks/yezz123/DogeAPI"/>
   <img src="https://visitor-badge.laobi.icu/badge?page_id=yezz123.Pretty-Readme">
   <img src="https://img.shields.io/static/v1?label=%F0%9F%8C%9F&message=If%20Useful&style=style=flat&color=BC4E99" alt="Star Badge"/>
   <a href="https://github.com/yezz123/DogeAPI/actions/workflows/codeql-analysis.yml"><img src="https://github.com/yezz123/DogeAPI/actions/workflows/codeql-analysis.yml/badge.svg?branch=main"/></a>
   <a href="https://github.com/yezz123/DogeAPI/actions/workflows/docker-publish.yml"><img src="https://github.com/yezz123/DogeAPI/actions/workflows/docker-publish.yml/badge.svg?branch=main"/></a>
   <a href="https://github.com/yezz123/DogeAPI/actions/workflows/docker-image.yml"><img src="https://github.com/yezz123/DogeAPI/actions/workflows/docker-image.yml/badge.svg?branch=main"/></a>
   <a href="https://github.com/yezz123/DogeAPI/actions/workflows/ossar-analysis.yml"><img src="https://github.com/yezz123/DogeAPI/actions/workflows/ossar-analysis.yml/badge.svg?branch=main"/></a>

</p>

# DogeAPI

API with high performance built with FastAPI & SQLAlchemy, help to improve connection with your Backend Side to create a simple blog and Cruds with OAuth2PasswordBearer ⛏

## Getting Started

### Prerequisites

- Python 3.8.6 or higher
- FastAPI
- Docker

### Project setup

```sh
# clone the repo
$ git clone https://github.com/yezz123/DogeAPI

# move to the project folder
$ cd DogeAPI
```

### Creating virtual environment

- Install `pipenv` a global python project `pip install pipenv`
- Create a `virtual environment` for this project

```shell
# creating pipenv environment for python 3
$ pipenv --three

# activating the pipenv environment
$ pipenv shell

# if you have multiple python 3 versions installed then
$ pipenv install -d --python 3.8

# install all dependencies (include -d for installing dev dependencies)
$ pipenv install -d
```

### Running the Application

- To run the [Main](main.py) we need to use [uvicorn](https://www.uvicorn.org/) a lightning-fast ASGI server implementation, using uvloop and httptools.

```sh
# Running the application using uvicorn
$ uvicorn main:app

## To run the Application under a reload enviromment use -- reload
$ uvicorn main:app --reload
```

### Configured Enviromment

#### Database

- To Provide a good and fast work, i choose a `SQLite` Database using `SQLAlchemy`.
- If you want to configure the Database with an other Provider like `MySQL` or `PostgreSQL` you can change the `Database_URL` here :

```py
# here you need to inster the  URI that should be used for the connection.
SQLALCHEMY_DATABASE_URL = 'sqlite:///blog.db'
```

- For Example :

```py
SQLALCHEMY_DATABASE_URL = 'mysql://username:password@server/blog'
```

#### Models

- Here for the [Models.py](models/models.py), i create 2 tables based on the requirements for this project `blogs` and `users`

```py
class Blog(Base):
    __tablename__ = "blogs"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    body = Column(String)
    user_id = Column(Integer, ForeignKey("users.id"))
    creator = relationship("User", back_populates="blogs")
```

```py
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    email = Column(String)
    password = Column(String)
    blogs = relationship("Blog", back_populates="creator")
```

#### Token

- Set environment variables as the Secret Key and Time Expire for Token, i made it in an easy way to get it.
- Change the `.env.sample` to `.env` then insert you String `Secret_Key` and `ACCESS_TOKEN_EXPIRE_MINUTES`.
- you can generate the String using `openssl rand -hex 32`.

## Running the Docker Container

- We have the Dockerfile created in above section. Now, we will use the Dockerfile to create the image of the FastAPI app and then start the FastAPI app container.

```sh
$ docker build
```

- list all the docker images and you can also see the image `dogeapi:latest` in the list.

```sh
$ docker images
```

- run the application at port 5000. The various options used are:

> - `-p`: publish the container's port to the host port.
> - `-d`: run the container in the background.
> - `-i`: run the container in interactive mode.
> - `-t`: to allocate pseudo-TTY.
> - `--name`: name of the container

```sh
$ docker container run -p 5000:5000 -dit --name DOGEAPI dogeapi:latest
```

- Check the status of the docker container

```sh
$ docker container ps
```

## Preconfigured Packages

Includes preconfigured packages to kick start DogeAPI by just setting appropriate configuration.

| Package                                                      | Usage                                                            |
| ------------------------------------------------------------ | ---------------------------------------------------------------- |
| [uvicorn](https://www.uvicorn.org/)        | a lightning-fast ASGI server implementation, using uvloop and httptools.           |
| [Python-Jose](https://github.com/mpdavis/python-jose) | a JavaScript Object Signing and Encryption implementation in Python.    |
| [SQLAlchemy](https://www.sqlalchemy.org/)  | is the Python SQL toolkit and Object Relational Mapper that gives application developers the full power and flexibility of SQL. |
| [starlette](https://www.starlette.io/)   | a lightweight ASGI framework/toolkit, which is ideal for building high performance asyncio services.    |
| [passlib](https://passlib.readthedocs.io/en/stable/)  | a password hashing library for Python 2 & 3, which provides cross-platform implementations of over 30 password hashing algorithms         |
| [bcrypt](https://github.com/pyca/bcrypt/)               | Good password hashing for your software and your servers.    |
| [python-multipart](https://github.com/andrew-d/python-multipart) | streaming multipart parser for Python.   |

`yapf` packages for `linting and formatting`

## Contributing

- Join the DOGEAPI Creator and Contribute to the Project if you have any enhancement or add-ons to create a good and Secure Project, Help any User to Use it in a good and simple way.
- Check all information here at [docs's Folder](docs) to understand to how to contribute or to Read the Code of Conduct.

## License

This project is licensed under the terms of the MIT license.
