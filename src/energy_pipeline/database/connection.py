import logging

from sqlalchemy import Engine, create_engine
from sqlalchemy.exc import NoSuchModuleError
from sqlalchemy.orm import Session, sessionmaker

from src.energy_pipeline.config.settings import DB_URL

logger = logging.getLogger(__name__)


def create_db_engine() -> Engine:
    if DB_URL is None:
        logger.error("Database URL is not set. Please check your environment variables.")
        raise ConnectionError("Database URL is not set.")

    try:
        db_engine = create_engine(DB_URL)
    except NoSuchModuleError:
        logger.error("DB_URL is incorrect. Please check your environment variables.")
        raise

    logger.info("Database engine has been created successfully.")

    return db_engine


def create_session(db_engine: Engine) -> Session:
    Session = sessionmaker(bind=db_engine)
    return Session()
