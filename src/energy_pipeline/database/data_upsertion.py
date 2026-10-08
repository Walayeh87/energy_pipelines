import logging

from pandas import DataFrame
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from src.energy_pipeline.database.models import PriceData

logger = logging.getLogger(__name__)


def upsert_energy_prices_to_db(session: Session, prices: DataFrame) -> None:
    stmt = insert(PriceData).values(prices.to_dict(orient="records"))
    stmt = stmt.on_conflict_do_nothing(index_elements=[PriceData.timestamp, PriceData.price_metadata_id])

    session.execute(stmt)
    session.commit()

    logger.info(f"{len(prices)} energy prices have been loaded to the database successfully.")
