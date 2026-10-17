from dataclasses import dataclass
from datetime import datetime
from typing import Any

from numpy import select
from sqlalchemy import select
from sqlalchemy.orm import InstrumentedAttribute, Session

from energy_pipelines.core.database.models import CoolingSpecs, PriceData, PriceMetadata, Site


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


def fetch_site(session: Session, site_name: str) -> Site:
    return session.scalars(select(Site).where(Site.name == site_name)).one()


def fetch_cooling_specs(session: Session, site_id: int) -> CoolingSpecs:
    return session.scalars(select(CoolingSpecs).where(CoolingSpecs.site_id == site_id)).one()


def fetch_all_site_names(session: Session) -> list[str]:
    return [site.name for site in session.scalars(select(Site)).all()]


def fetch_all_site_ids_in_cooling_specs(session: Session) -> list[int]:
    return [site.site_id for site in session.scalars(select(CoolingSpecs)).all()]


def fetch_bidding_zone_and_price_metadata_id_as_mapper(session: Session) -> dict[str, int]:
    return {
        price_metadata.bidding_zone: price_metadata.price_metadata_id
        for price_metadata in session.scalars(select(PriceMetadata)).all()
    }


def fetch_data_id_by_bidding_zone(session: Session, bidding_zone: str) -> int:
    return session.scalars(
        select(PriceMetadata.price_metadata_id).where(PriceMetadata.bidding_zone == bidding_zone)
    ).one()
