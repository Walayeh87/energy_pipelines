import os

import psycopg
from dotenv import load_dotenv
from psycopg import Connection
from psycopg.rows import dict_row

from data_source.energy_charts.energy_price.data_upsertion import logger

load_dotenv()


def establish_db_connection() -> Connection:
    env = os.getenv("ENV")

    if env is None:
        logger.error("Environment variable 'ENV' is not set. Please check your environment variables.")
        raise ValueError("Environment variable 'ENV' is not set.")

    db_url = os.getenv(f"DB_URL_{env}".upper())

    if db_url is None:
        logger.error(f"Database URL for environment '{env}' is not set. Please check your environment variables.")
        raise ValueError(f"Database URL for environment '{env}' is not set.")

    connection = psycopg.connect(db_url, row_factory=dict_row)

    logger.info("Connection to the database has been established successfully.")

    return connection
