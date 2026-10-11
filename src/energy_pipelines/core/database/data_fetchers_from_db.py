from dataclasses import dataclass
from datetime import datetime
from typing import Any

from sqlalchemy.orm import InstrumentedAttribute, Session

from energy_pipelines.core.database.connection import create_db_engine, create_session
from energy_pipelines.core.database.models import PriceData, PriceMetadata, Regions


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
        price_metadata_id = (
            [price_metadata_id for (price_metadata_id,) in result][0] if result else invalid_id_value
        )
        mapper[bidding_zone] = price_metadata_id

    return mapper


def fetch_bidding_zones(session: Session) -> list[str]:
    result = session.query(Regions.bidding_zone).all()

    return [bidding_zone for (bidding_zone,) in result]


def fetch_price_metadata(session: Session, metadata_id: int) -> type[PriceMetadata]:
    metadata = session.query(PriceMetadata).filter(PriceMetadata.price_metadata_id == metadata_id).first()
    if metadata is None:
        return PriceMetadata
    return metadata


@dataclass
class DTFetchingResult:
    dt_data: list[Any]
    data_id: int
    start: datetime
    end: datetime


def fetch_dt_data(
    session: Session,
    cols2fetch: list[InstrumentedAttribute],
    data_id: int,
    start: datetime,
    end: datetime,
) -> DTFetchingResult:
    data = (
        session.query(*cols2fetch)
        .filter(PriceData.price_metadata_id == data_id)
        .filter(PriceData.timestamp >= start)
        .filter(PriceData.timestamp < end)
        .all()
    )
    return DTFetchingResult(dt_data=data, data_id=data_id, start=start, end=end)


if __name__ == "__main__":
    db_engine = create_db_engine()
    session = create_session(db_engine)

    metadata = fetch_price_metadata(session, metadata_id=1)

    dt_data_result = fetch_dt_data(
        session,
        cols2fetch=[PriceData.timestamp, PriceData.energy_price],
        data_id=10,
        start=datetime(2026, 10, 1),
        end=datetime(2026, 10, 2),
    )
