from sqlalchemy.orm import DeclarativeBase


class BaseConfig:

    SECRET_KEY = "7362f543439aa70ebdd49f7830329d21749edf16eaed314b46904cf4c1a311d7"
    ALGORITHM = "HS512"
    ACCESS_TOKEN_EXPIRE_MINUTES = 3
    REFRESH_TOKEN_EXPIRE_MINUTES = 25


class Base(DeclarativeBase):

    pass


class ServiceURL:

    NLP_URL = "http://localhost:8001/nlp/parse"
    ADMIN_BASE_URL = "http://localhost:8002/admin"
