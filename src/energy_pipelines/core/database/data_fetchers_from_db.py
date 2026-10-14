import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import InstrumentedAttribute, Session

from energy_pipelines.core.database.connection import create_db_engine, create_db_session
from energy_pipelines.core.database.models import CoolingSpecs, PriceData, PriceMetadata, Regions, Site

logger = logging.getLogger(__name__)


class InvalidObjects(Enum):
    ID = 0

    def __repr__(self) -> str:
        return repr(self.value)


def fetch_bidding_zone_and_price_metadata_id_as_mapper(
    session: Session, bidding_zones: list[str] | str
) -> dict[str, int]:
    if isinstance(bidding_zones, str):
        bidding_zones = [bidding_zones]

    mapper = {}
    for bidding_zone in bidding_zones:
        result = session.scalars(
            select(PriceMetadata.price_metadata_id).where(PriceMetadata.bidding_zone == bidding_zone)
        ).first()

        price_metadata_id = result if result else InvalidObjects.ID
        mapper[bidding_zone] = price_metadata_id

    return mapper


def fetch_bidding_zones(session: Session) -> list[str]:
    return list(session.scalars(select(Regions.bidding_zone)).all())


def fetch_price_metadata(session: Session, metadata_id: int) -> PriceMetadata:
    metadata = session.scalars(
        select(PriceMetadata).where(PriceMetadata.price_metadata_id == metadata_id)
    ).first()

    if metadata is None:
        return PriceMetadata()

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


def fetch_all_site_names(session: Session) -> list[str]:
    return [site.name for site in session.scalars(select(Site)).all()]


def fetch_all_site_ids(session: Session, table: Site | CoolingSpecs) -> list[int]:
    if table == Site:
        return [site.id for site in session.scalars(select(Site)).all()]
    if table == CoolingSpecs:
        return [site.site_id for site in session.scalars(select(CoolingSpecs)).all()]
    else:
        raise ValueError(f"Unsupported table: {table}")


@dataclass
class CoolingSpecsFetchingResult:
    min_temp: int | float | None
    max_temp: int | float | None
    default_temp: int | float | None


def fetch_cooling_specs(session: Session, site_id: int) -> CoolingSpecsFetchingResult:
    min_temp = session.scalars(select(CoolingSpecs.min_temp).where(CoolingSpecs.site_id == site_id)).first()
    max_temp = session.scalars(select(CoolingSpecs.max_temp).where(CoolingSpecs.site_id == site_id)).first()
    default_temp = session.scalars(
        select(CoolingSpecs.default_temp).where(CoolingSpecs.site_id == site_id)
    ).first()

    return CoolingSpecsFetchingResult(min_temp=min_temp, max_temp=max_temp, default_temp=default_temp)


def fetch_site_name_and_id_as_mapper(session: Session) -> dict[str, int]:
    return {site.name: site.id for site in session.scalars(select(Site)).all()}


def fetch_site_bidding_zone(session: Session, site_id: int) -> str | None:
    return session.scalar(select(Site.bidding_zone).where(Site.id == site_id))


if __name__ == "__main__":
    db_engine = create_db_engine()
    session = create_db_session(db_engine)

    metadata = fetch_price_metadata(session, metadata_id=10)

    dt_data_result = fetch_dt_data(
        session,
        cols2fetch=[PriceData.timestamp, PriceData.energy_price],
        data_id=10,
        start=datetime(2026, 10, 1),
        end=datetime(2026, 10, 2),
    )

    sites = fetch_all_site_names(session)

    cooling_specs = fetch_cooling_specs(session, site_id=3)
