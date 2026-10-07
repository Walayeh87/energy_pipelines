import logging

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.energy_pipeline.config.settings import DB_URL

logger = logging.getLogger(__name__)


def create_db_engine() -> Engine:
    if DB_URL is None:
        logger.error("Database URL is not set. Please check your environment variables.")
        raise ValueError("Database URL is not set.")

    db_engine = create_engine(DB_URL)
    logger.info("Database engine has been created successfully.")

    return db_engine


def create_session(db_engine: Engine) -> Session:
    Session = sessionmaker(bind=db_engine)
    return Session()
