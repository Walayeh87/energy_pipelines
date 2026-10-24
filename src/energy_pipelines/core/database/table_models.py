from datetime import datetime
from enum import StrEnum
from typing import ClassVar
from uuid import UUID, uuid4

from sqlalchemy import BOOLEAN, BigInteger, DateTime, ForeignKey, Numeric, SmallInteger, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class SchemaNames(StrEnum):
    ENERGY_PRICES = "energy_prices"
    SITES = "sites"
    ALGOS = "algos"


class Regions(Base):
    __tablename__ = "regions"
    __table_args__: ClassVar = {"schema": SchemaNames.ENERGY_PRICES}

    bidding_zone: Mapped[str] = mapped_column(String(10), primary_key=True, unique=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)

    def __repr__(self) -> str:
        return (
            f"{self.__table_args__['schema']}.{self.__tablename__}"
            f"(bidding_zone={self.bidding_zone!r}, "
            f"name={self.name!r} "
        )


class PriceMetadata(Base):
    __tablename__ = "price_metadata"
    __table_args__: ClassVar = {"schema": SchemaNames.ENERGY_PRICES}

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )
    bidding_zone: Mapped[str] = mapped_column(
        String(10),
        ForeignKey(Regions.bidding_zone),
        nullable=False,
        unique=True,
    )
    freq: Mapped[str] = mapped_column(String(10), nullable=False)
    important_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    source: Mapped[str] = mapped_column(String(100), nullable=False)
    unit: Mapped[str] = mapped_column(String(10), nullable=False)
    tz: Mapped[str] = mapped_column(String(10), nullable=False)

    def __repr__(self) -> str:
        return (
            f"{self.__table_args__['schema']}.{self.__tablename__}("
            f"id={self.id!r}, "
            f"bidding_zone={self.bidding_zone!r}, "
            f"freq={self.freq!r}, "
            f"source={self.source!r}, "
            f"unit={self.unit!r}, "
            f"tz={self.tz!r})"
        )


class PriceData(Base):
    __tablename__ = "price_data"
    __table_args__: ClassVar = {"schema": SchemaNames.ENERGY_PRICES}

    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), primary_key=True)
    price_metadata_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(PriceMetadata.id),
        nullable=False,
        primary_key=True,
    )
    values: Mapped[int | float] = mapped_column(Numeric, nullable=False)

    def __repr__(self) -> str:
        return (
            f"{self.__table_args__['schema']}.{self.__tablename__}("
            f"timestamp={self.timestamp}, "
            f"price_metadata_id={self.price_metadata_id}, "
            f"values={self.values})"
        )


class PriceFetchingFailures(Base):
    __tablename__ = "price_fetching_failures"
    __table_args__: ClassVar = {"schema": SchemaNames.ENERGY_PRICES}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    price_metadata_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(PriceMetadata.id),
        nullable=False,
    )
    http_response_status_code: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    reporting_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    error_msg: Mapped[str] = mapped_column(Text, nullable=False)

    def __repr__(self) -> str:
        return (
            f"{self.__table_args__['schema']}.{self.__tablename__}("
            f"id={self.id!r}, "
            f"price_metadata_id={self.price_metadata_id!r}, "
            f"http_response_status_code={self.http_response_status_code!r}, "
            f"reporting_time={self.reporting_time}, "
            f"error_msg={self.error_msg!r})"
        )


class Site(Base):
    __tablename__ = "site"
    __table_args__: ClassVar = {"schema": SchemaNames.SITES}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    bidding_zone: Mapped[str] = mapped_column(
        String(10),
        ForeignKey(Regions.bidding_zone),
        nullable=False,
    )
    address: Mapped[str] = mapped_column(String(100), nullable=True)
    country: Mapped[str] = mapped_column(String(50), nullable=True)
    subdivision: Mapped[str] = mapped_column(String(50), nullable=True)
    tz: Mapped[str] = mapped_column(String(50), nullable=False)

    def __repr__(self) -> str:
        return (
            f"{self.__table_args__['schema']}.{self.__tablename__}("
            f"id={self.id!r}, "
            f"name={self.name!r}, "
            f"address={self.address!r}, "
            f"country={self.country!r}, "
            f"subdivision={self.subdivision!r}, "
            f"tz={self.tz!r}, "
        )


class Algo(Base):
    __tablename__ = "algo"
    __table_args__: ClassVar = {"schema": SchemaNames.ALGOS}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    notes: Mapped[str | None] = mapped_column(String(500), nullable=True)

    def __repr__(self) -> str:
        return (
            f"{self.__table_args__['schema']}.{self.__tablename__}("
            f"id={self.id!r}, "
            f"name={self.name!r}, "
            f"notes={self.notes!r})"
        )


class AlgosOutput(Base):
    __tablename__ = "algos_output"
    __table_args__: ClassVar = {"schema": SchemaNames.ALGOS}

    site_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(Site.id, ondelete="CASCADE"),
        primary_key=True,
    )
    algo_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(Algo.id, ondelete="RESTRICT"),
        primary_key=True,
    )
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, primary_key=True)
    values: Mapped[int | float] = mapped_column(Numeric, nullable=False)

    def __repr__(self) -> str:
        return (
            f"{self.__table_args__['schema']}.{self.__tablename__}("
            f"site_id={self.site_id!r}, "
            f"algo_id={self.algo_id!r}, "
            f"timestamp={self.timestamp!r}, "
            f"values={self.values!r})"
        )


class SiteAlgos(Base):
    __tablename__ = "site_algos"
    __table_args__: ClassVar = {"schema": SchemaNames.SITES}

    site_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(Site.id, ondelete="CASCADE"),
        primary_key=True,
    )
    algo_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(Algo.id, ondelete="RESTRICT"),
        primary_key=True,
    )
    params: Mapped[dict] = mapped_column(JSONB, nullable=False)
    is_active: Mapped[bool] = mapped_column(BOOLEAN, nullable=False, default=True)
    notes: Mapped[str | None] = mapped_column(String(500), nullable=True)

    def __repr__(self) -> str:
        return (
            f"{self.__table_args__['schema']}.{self.__tablename__}("
            f"site_id={self.site_id!r}, "
            f"algo_id={self.algo_id!r}, "
            f"params={self.params!r}, "
            f"is_active={self.is_active!r}, "
            f"notes={self.notes!r})"
        )


class FailingAlgosOutput(Base):
    __tablename__ = "failing_algos_output"
    __table_args__: ClassVar = {"schema": SchemaNames.ALGOS}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    failure_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        nullable=False,
        index=True,
        default=uuid4,
    )
    site_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(Site.id, ondelete="NO ACTION"),
    )
    algo_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(Algo.id, ondelete="NO ACTION"),
    )
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    values: Mapped[int | float] = mapped_column(Numeric, nullable=True)
    failing_reason: Mapped[str] = mapped_column(String(50), nullable=False)
    reporting_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    processed_prices: Mapped[int | float | None] = mapped_column(Numeric, nullable=True)
    mask_of_filled_prices_values: Mapped[bool | None] = mapped_column(BOOLEAN, nullable=True)
    price_processing_issue: Mapped[str] = mapped_column(String(50), nullable=False)
    is_backup: Mapped[bool] = mapped_column(BOOLEAN, nullable=False)

    def __repr__(self) -> str:
        return (
            f"{self.__table_args__['schema']}.{self.__tablename__}("
            f"site_id={self.site_id!r}, "
            f"algo_id={self.algo_id!r}, "
            f"timestamp={self.timestamp!r}, "
            f"values={self.values!r}, "
            f"failing_reason={self.failing_reason!r}, "
            f"reporting_time={self.reporting_time!r}, "
            f"processed_prices={self.processed_prices!r}, "
            f"mask_of_filled_prices_values={self.mask_of_filled_prices_values!r}, "
            f"price_processing_issue={self.price_processing_issue!r}, "
            f"is_backup={self.is_backup!r})"
        )
