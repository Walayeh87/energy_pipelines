from datetime import datetime
from decimal import Decimal
from enum import StrEnum

from sqlalchemy import DOUBLE_PRECISION, BigInteger, DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from energy_pipelines.utils.logging_config import setup_logging

setup_logging()


class Base(DeclarativeBase):
    pass


class SchemaNames(StrEnum):
    ENERGY_PRICES = "energy_prices"
    SITES = "sites"


class Regions(Base):
    __tablename__ = "regions"
    __table_args__ = {"schema": SchemaNames.ENERGY_PRICES}

    bidding_zone: Mapped[str] = mapped_column(String(10), primary_key=True, unique=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)

    def __repr__(self) -> str:
        return (
            f"{SchemaNames.ENERGY_PRICES}.{self.__tablename__}"
            f"(bidding_zone={self.bidding_zone!r}, "
            f"name={self.name!r} "
        )


class PriceMetadata(Base):
    __tablename__ = "price_metadata"
    __table_args__ = {"schema": SchemaNames.ENERGY_PRICES}

    price_metadata_id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )
    bidding_zone: Mapped[str] = mapped_column(
        String(10),
        ForeignKey(Regions.bidding_zone),
        nullable=False,
    )
    freq: Mapped[str] = mapped_column(String(10), nullable=False)
    important_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    source: Mapped[str] = mapped_column(String(100), nullable=False)
    unit: Mapped[str] = mapped_column(String(10), nullable=False)
    tz: Mapped[str] = mapped_column(String(10), nullable=False)

    def __repr__(self) -> str:
        return (
            f"{SchemaNames.ENERGY_PRICES}.{self.__tablename__}("
            f"price_metadata_id={self.price_metadata_id!r}, "
            f"bidding_zone={self.bidding_zone!r}, "
            f"freq={self.freq!r}, "
            f"source={self.source!r}, "
            f"unit={self.unit!r}, "
            f"tz={self.tz!r})"
        )


class PriceData(Base):
    __tablename__ = "price_data"
    __table_args__ = {"schema": SchemaNames.ENERGY_PRICES}

    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), primary_key=True)
    price_metadata_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(PriceMetadata.price_metadata_id),
        nullable=False,
        primary_key=True,
    )
    energy_price: Mapped[Decimal | None] = mapped_column(Numeric, nullable=True)

    def __repr__(self) -> str:
        return (
            f"{SchemaNames.ENERGY_PRICES}.{self.__tablename__}("
            f"timestamp={self.timestamp}, "
            f"price_metadata_id={self.price_metadata_id}, "
            f"energy_price={self.energy_price})"
        )


class Site(Base):
    __tablename__ = "site"
    __table_args__ = {"schema": SchemaNames.SITES}

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
            f"{SchemaNames.SITES}.{self.__tablename__}("
            f"id={self.id!r}, "
            f"name={self.name!r}, "
            f"address={self.address!r}, "
            f"country={self.country!r}, "
            f"subdivision={self.subdivision!r}, "
            f"tz={self.tz!r})"
        )


class CoolingSpecs(Base):
    __tablename__ = "cooling_specs"
    __table_args__ = {"schema": SchemaNames.SITES}

    site_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey(Site.id, ondelete="CASCADE"), primary_key=True
    )
    min_temp: Mapped[Decimal] = mapped_column(DOUBLE_PRECISION, nullable=False)
    max_temp: Mapped[Decimal] = mapped_column(DOUBLE_PRECISION, nullable=False)
    default_temp: Mapped[Decimal] = mapped_column(DOUBLE_PRECISION, nullable=False)

    def __repr__(self) -> str:
        return (
            f"{SchemaNames.SITES}.{self.__tablename__}("
            f"site_id={self.site_id!r}, "
            f"min_temp={self.min_temp}, "
            f"max_temp={self.max_temp}, "
            f"default_temp={self.default_temp})"
        )
