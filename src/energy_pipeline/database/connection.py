import logging

import psycopg
from psycopg import Connection
from psycopg.rows import dict_row

from src.energy_pipeline.config.settings import DB_URL

logger = logging.getLogger(__name__)


def establish_db_connection() -> Connection:
    if DB_URL is None:
        logger.error("Database URL is not set. Please check your environment variables.")
        raise ValueError("Database URL is not set.")

    connection = psycopg.connect(DB_URL, row_factory=dict_row)

    logger.info("Connection to the database has been established successfully.")

    return connection
