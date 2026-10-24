import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from pandas import Timedelta
from sqlalchemy import select
from sqlalchemy.orm import InstrumentedAttribute, Session

from energy_pipelines.core.database.table_models import (
    Algo,
    PriceData,
    PriceMetadata,
    SchemaNames,
    Site,
    SiteAlgos,
)
from energy_pipelines.utils.custom_errors import EmptyTableError

logger = logging.getLogger(__name__)


@dataclass
class DTFetchingResult:
    price_metadata_id: int
    start: datetime
    end: datetime
    energy_price_data: list[Any]


def fetch_energy_price_data(
    session: Session,
    cols2fetch: list[InstrumentedAttribute],
    price_metadata_id: int,
    start: datetime,
    end: datetime,
) -> DTFetchingResult:
    if len(cols2fetch) == 0:
        raise ValueError("No columns specified for fetching.")

    for col2fetch in cols2fetch:
        if col2fetch not in [getattr(PriceData, column.name) for column in PriceData.__table__.columns]:
            raise ValueError(f"Column '{col2fetch.key}' is not a valid column for fetching.")

    price_metadata_ids = set(session.scalars(select(PriceData.price_metadata_id)).all())
    if price_metadata_id not in price_metadata_ids:
        raise ValueError(
            f"price_metadata_id: {price_metadata_id} not found in"
            f" '{SchemaNames.ENERGY_PRICES}.{PriceData.__tablename__}'."
        )

    first_timestamp = session.scalars(
        select(PriceData.timestamp)
        .where(PriceData.price_metadata_id == price_metadata_id)
        .order_by(PriceData.timestamp)
    ).first()

    if start >= end - Timedelta("15min"):
        raise ValueError("Start time must be before end time.")

    if start < first_timestamp:
        raise ValueError(
            f"start time '{start}' is before the first available timestamp '{first_timestamp}' "
            f"in '{SchemaNames.ENERGY_PRICES}.{PriceData.__tablename__}'."
        )

    data = (
        session.query(*cols2fetch)
        .filter(PriceData.price_metadata_id == price_metadata_id)
        .filter(PriceData.timestamp >= start)
        .filter(PriceData.timestamp < end)
        .all()
    )
    return DTFetchingResult(energy_price_data=data, price_metadata_id=price_metadata_id, start=start, end=end)


def fetch_price_metadata(session: Session, metadata_id: int) -> PriceMetadata:
    price_metadata = session.scalars(
        select(PriceMetadata).where(PriceMetadata.id == metadata_id)
    ).one_or_none()

    if price_metadata is None:
        raise ValueError(
            f"price_metadata_id: '{metadata_id}' not found in"
            f" '{SchemaNames.ENERGY_PRICES}.{PriceMetadata.__tablename__}'."
        )

    return price_metadata


def fetch_site(session: Session, site_name: str) -> Site:
    site = session.scalars(select(Site).where(Site.name == site_name)).one_or_none()

    if site is None:
        raise ValueError(
            f"Site with name '{site_name}' not found in '{SchemaNames.SITES}.{Site.__tablename__}'."
        )

    return site


def fetch_site_algos(session: Session, site_id: int) -> list[SiteAlgos]:
    site_algos = list(session.scalars(select(SiteAlgos).where(SiteAlgos.site_id == site_id)).all())

    if len(site_algos) == 0:
        raise ValueError(f"site_id: {site_id} not found in '{SchemaNames.SITES}.{SiteAlgos.__tablename__}'.")

    return site_algos


def fetch_algo_name(session: Session, algo_id: int) -> str:
    algo_name = session.scalars(select(Algo.name).where(Algo.id == algo_id)).one_or_none()

    if algo_name is None:
        raise ValueError(f"algo_id: {algo_id} not found in '{SchemaNames.ALGOS}.{Algo.__tablename__}'.")

    return algo_name


def fetch_price_metadata_id_by_bidding_zone(session: Session, bidding_zone: str) -> int:
    price_metadata = session.scalars(
        select(PriceMetadata.id).where(PriceMetadata.bidding_zone == bidding_zone)
    ).one_or_none()

    if price_metadata is None:
        raise ValueError(
            f"bidding_zone '{bidding_zone}' not found in"
            f" '{SchemaNames.ENERGY_PRICES}.{PriceMetadata.__tablename__}'."
        )

    return price_metadata


def fetch_site_names_by_ids(session: Session, site_ids: list[int] | int) -> list[str]:
    if isinstance(site_ids, int):
        site_ids = [site_ids]

    site_names = list(session.scalars(select(Site.name).where(Site.id.in_(site_ids))).all())

    if len(site_names) == 0:
        raise ValueError(f"No sites found for the provided site_ids: {site_ids}")

    return site_names


def fetch_all_site_ids_in_site_algos(session: Session) -> list[int]:
    site_ids = set(session.scalars(select(SiteAlgos.site_id)).all())
    if len(site_ids) == 0:
        raise EmptyTableError(f"'{SchemaNames.SITES}.{SiteAlgos.__tablename__}' is empty.")

    return list(site_ids)


def fetch_bidding_zone_and_price_metadata_id_as_mapper(session: Session) -> dict[str, int]:
    mapper = {pm.bidding_zone: pm.id for pm in session.scalars(select(PriceMetadata)).all()}
    if len(mapper) == 0:
        raise EmptyTableError(f"'{SchemaNames.ENERGY_PRICES}.{PriceMetadata.__tablename__}' is empty.")

    return mapper


def fetch_bidding_zones_in_price_metadata(session: Session) -> list[str]:
    bidding_zones_in_price_metadata = list(session.scalars(select(PriceMetadata.bidding_zone)).all())

    if len(bidding_zones_in_price_metadata) == 0:
        raise EmptyTableError(f"'{SchemaNames.ENERGY_PRICES}.{PriceMetadata.__tablename__}' is empty.")

    return bidding_zones_in_price_metadata
