import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from numpy import select
from sqlalchemy import select
from sqlalchemy.orm import InstrumentedAttribute, Session

from energy_pipelines.core.database.models import CoolingSpecs, PriceData, PriceMetadata, Site

logger = logging.getLogger(__name__)


@dataclass
class DTFetchingResult:
    data_id: int
    start: datetime
    end: datetime
    dt_data: list[Any]


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


def fetch_price_metadata(session: Session, metadata_id: int) -> PriceMetadata:
    return session.scalars(select(PriceMetadata).where(PriceMetadata.price_metadata_id == metadata_id)).one()


def fetch_all_site_names(session: Session) -> list[str]:
    return [site.name for site in session.scalars(select(Site)).all()]


def fetch_all_site_ids(session: Session) -> list[int]:
    return [site.site_id for site in session.scalars(select(CoolingSpecs)).all()]


def fetch_bidding_zone_and_price_metadata_id_as_mapper(session: Session) -> dict[str, int]:
    return {
        price_metadata.bidding_zone: price_metadata.price_metadata_id
        for price_metadata in session.scalars(select(PriceMetadata)).all()
    }


@dataclass
class CoolingSpecsFetchingResult:
    min_temp: int | float
    max_temp: int | float
    default_temp: int | float


def fetch_cooling_specs(session: Session, site_id: int) -> CoolingSpecsFetchingResult:
    min_temp = session.scalars(select(CoolingSpecs.min_temp).where(CoolingSpecs.site_id == site_id)).one()
    max_temp = session.scalars(select(CoolingSpecs.max_temp).where(CoolingSpecs.site_id == site_id)).one()
    default_temp = session.scalars(
        select(CoolingSpecs.default_temp).where(CoolingSpecs.site_id == site_id)
    ).one()

    return CoolingSpecsFetchingResult(min_temp=min_temp, max_temp=max_temp, default_temp=default_temp)


def fetch_site_name_and_id_as_mapper(session: Session) -> dict[str, int]:
    return {site.name: site.id for site in session.scalars(select(Site)).all()}


def fetch_site_bidding_zone(session: Session, site_id: int) -> str:
    return session.scalars(select(Site.bidding_zone).where(Site.id == site_id)).one()


def fetch_temp_unit(session: Session, site_id: int) -> str:
    return session.scalars(select(CoolingSpecs.temp_unit).where(CoolingSpecs.site_id == site_id)).one()


def fetch_site_tz(session: Session, site_name: str) -> str:
    return session.scalars(select(Site.tz).where(Site.name == site_name)).one()


# if __name__ == "__main__":
#     db_engine = create_db_engine()
#     session = create_db_session(db_engine)
#
#     metadata = fetch_price_metadata(session, metadata_id=10)
#
#     dt_data_result = fetch_dt_data(
#         session,
#         cols2fetch=[PriceData.timestamp, PriceData.energy_price],
#         data_id=10,
#         start=datetime(2026, 10, 1),
#         end=datetime(2026, 10, 2),
#     )
#
#     sites = fetch_all_site_names(session)
#
#     cooling_specs = fetch_cooling_specs(session, site_id=3)
