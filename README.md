![DOGEAPI](docs/Images/header.svg)

<p align="center">
   <img src="https://img.shields.io/badge/Dev-Yezz123-green?style"/>
   <img src="https://img.shields.io/badge/language-python-blue?style"/>
   <img src="https://img.shields.io/github/stars/yezz123/DogeAPI"/>
   <img src="https://img.shields.io/github/forks/yezz123/DogeAPI"/>
   <img src="https://visitor-badge.laobi.icu/badge?page_id=yezz123.Pretty-Readme">
   <img src="https://img.shields.io/static/v1?label=%F0%9F%8C%9F&message=If%20Useful&style=style=flat&color=BC4E99" alt="Star Badge"/>
   <a href="https://github.com/yezz123/DogeAPI/actions/workflows/docker-publish.yml"><img src="https://github.com/yezz123/DogeAPI/actions/workflows/docker-publish.yml/badge.svg?branch=main"/></a>

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

- Create a virtual environment using virtualenv.

```shell
# creating virtual environment
$ virtualenv venv

# activate virtual environment
$ source venv/bin/activate

# install all dependencies
$ pip install -r requirements.txt
```

### Running the Application

- To run the [Main](main.py) we need to use [uvicorn](https://www.uvicorn.org/) a lightning-fast ASGI server implementation, using uvloop and httptools.

```sh
# Running the application using uvicorn
$ uvicorn main:app --reload
```

### Environment variables

- `SECRET_KEY`: A secret key for signing Json Web Token.
- `SQLALCHEMY_DATABASE_URL`: The database url to connect to the database.
- `ACCESS_TOKEN_EXPIRE_MINUTES`: The access token expire minutes.

> change all the environment variables in the `.env.sample` and don't forget to rename it to `.env`.

### Configured Enviromment

#### Models

- Here for the [Models.py](models/models.py), i create 2 tables based on the requirements for this project `blogs` and `users`

## Running the Docker Container

- We have the Dockerfile created in above section. Now, we will use the Dockerfile to create the image of the FastAPI app and then start the FastAPI app container.
- Using a preconfigured `Makefile` tor run the Docker Compose:

```sh
# Pull the latest image
$ make pull

# Build the image
$ make build

# Run the container
$ make start

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
