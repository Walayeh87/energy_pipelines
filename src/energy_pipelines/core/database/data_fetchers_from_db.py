from dataclasses import dataclass
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import InstrumentedAttribute, Session

from energy_pipelines.core.database.models import (
    Algo,
    PriceData,
    PriceMetadata,
    SchemaNames,
    Site,
    SiteAlgos,
)
from energy_pipelines.utils.custom_errors import EmptyTableError


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
    all_price_metadata_ids = [pm.price_metadata_id for pm in session.scalars(select(PriceMetadata)).all()]
    if metadata_id not in all_price_metadata_ids:
        raise ValueError(
            f"price_metadata_id: '{metadata_id}' not found in"
            f" '{SchemaNames.ENERGY_PRICES}.{PriceMetadata.__tablename__}'."
        )

    return session.scalars(select(PriceMetadata).where(PriceMetadata.price_metadata_id == metadata_id)).one()


def fetch_site(session: Session, site_name: str) -> Site:
    if site_name not in fetch_all_site_names(session=session):
        raise ValueError(
            f"Site with name '{site_name}' not found in '{SchemaNames.SITES}.{Site.__tablename__}'."
        )

    return session.scalars(select(Site).where(Site.name == site_name)).one()


def fetch_site_algos(session: Session, site_id: int) -> list[SiteAlgos]:
    if site_id not in fetch_all_site_ids_in_site_algos(session=session):
        raise ValueError(f"site_id: {site_id} not found in '{SchemaNames.SITES}.{SiteAlgos.__tablename__}'.")

    return list(session.scalars(select(SiteAlgos).where(SiteAlgos.site_id == site_id)).all())


def fetch_algo_name(session: Session, algo_id: int) -> str:
    if algo_id not in [algo.id for algo in session.scalars(select(Algo)).all()]:
        raise ValueError(f"algo_id: {algo_id} not found in '{SchemaNames.ALGOS}.{Algo.__tablename__}'.")

    return session.scalars(select(Algo.name).where(Algo.id == algo_id)).one()


def fetch_data_id_by_bidding_zone(session: Session, bidding_zone: str) -> int:
    if bidding_zone not in fetch_bidding_zones_in_price_metadata(session=session):
        raise ValueError(
            f"bidding_zone '{bidding_zone}' not found in"
            f" '{SchemaNames.ENERGY_PRICES}.{PriceMetadata.__tablename__}'."
        )

    return session.scalars(
        select(PriceMetadata.price_metadata_id).where(PriceMetadata.bidding_zone == bidding_zone)
    ).one()


def fetch_all_site_names(session: Session) -> list[str]:
    site_names = [site.name for site in session.scalars(select(Site)).all()]
    if len(site_names) == 0:
        raise EmptyTableError(f"'{SchemaNames.SITES}.{Site.__tablename__}' is empty.")

    return site_names


def fetch_all_site_ids_in_site_algos(session: Session) -> set[int]:
    site_ids = set(site_algo.site_id for site_algo in session.scalars(select(SiteAlgos)).all())
    if len(site_ids) == 0:
        raise EmptyTableError(f"'{SchemaNames.SITES}.{SiteAlgos.__tablename__}' is empty.")

    return site_ids


def fetch_bidding_zone_and_price_metadata_id_as_mapper(session: Session) -> dict[str, int]:
    mapper = {pm.bidding_zone: pm.price_metadata_id for pm in session.scalars(select(PriceMetadata)).all()}
    if len(mapper) == 0:
        raise EmptyTableError(f"'{SchemaNames.ENERGY_PRICES}.{PriceMetadata.__tablename__}' is empty.")

    return mapper


def fetch_bidding_zones_in_price_metadata(session: Session) -> list[str]:
    bidding_zone_in_pm = [
        price_metadata.bidding_zone for price_metadata in session.scalars(select(PriceMetadata)).all()
    ]
    if len(bidding_zone_in_pm) == 0:
        raise EmptyTableError(f"'{SchemaNames.ENERGY_PRICES}.{PriceMetadata.__tablename__}' is empty.")

    return bidding_zone_in_pm
