from configs.base_config import BaseConfig
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


class Configuration(BaseConfig):

    DEBUG = True

    DB_URI = "mysql+pymysql://root:2003@localhost/chatbot_admin"

    db_engine = create_engine(DB_URI, pool_pre_ping=True)

    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)

    Base = declarative_base()


def get_db():
    """
    Function to generate db session
    :return: Session
    """
    db = None
    try:
        db = Configuration.SessionLocal()
        yield db
    finally:
        db.close()
