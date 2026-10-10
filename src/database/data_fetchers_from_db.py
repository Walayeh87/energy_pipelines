from datetime import datetime
from decimal import Decimal

from pandas.core.frame import DataFrame
from sqlalchemy import Row
from sqlalchemy.orm import Session

from src.database.connection import create_db_engine, create_session
from src.database.models import PriceData, PriceMetadata, Regions


def fetch_bidding_zone_and_price_metadata_ids_mapper(session: Session, bidding_zones: list[str]) -> dict[str, int]:
    mapper = {}
    for bidding_zone in bidding_zones:
        result = (
            session.query(PriceMetadata.price_metadata_id)
            .filter(PriceMetadata.bidding_zone == bidding_zone)
            .filter(PriceMetadata.market_type == "DAY_AHEAD")
            .all()
        )
        invalid_id_value = 0
        price_metadata_id = [price_metadata_id for (price_metadata_id,) in result][0] if result else invalid_id_value
        mapper[bidding_zone] = price_metadata_id

    return mapper


def fetch_bidding_zones(session: Session) -> list[str]:
    result = session.query(Regions.bidding_zone).all()

    return [bidding_zone for (bidding_zone,) in result]


def fetch_energy_prices_from_db(
    session: Session,
    price_metadata_id: int,
    start_date: datetime,
    end_date: datetime,
) -> list[Row[Decimal | None, datetime]]:
    return (
        session.query(PriceData.energy_price, PriceData.timestamp)
        .filter(PriceData.price_metadata_id == price_metadata_id)
        .filter(PriceData.timestamp >= start_date)
        .filter(PriceData.timestamp < end_date)
        .all()
    )


if __name__ == "__main__":
    db_engine = create_db_engine()
    session = create_session(db_engine)

    result = fetch_energy_prices_from_db(
        session=session,
        price_metadata_id=1,
        start_date=datetime(2026, 7, 1, 0, 0, 0),
        end_date=datetime(2026, 7, 2, 0, 0, 0),
    )

    df = DataFrame(result)
