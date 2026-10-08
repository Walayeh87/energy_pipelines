from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from src.energy_pipeline.database.connection import create_db_engine, create_session
from utils.custom_objects import DbId
from utils.logging_config import setup_logging

setup_logging()


class Base(DeclarativeBase):
    pass


class PriceMetadata(Base):
    schema_name = "energy_prices"

    __tablename__ = "price_metadata"
    __table_args__ = {"schema": schema_name}

    price_metadata_id: Mapped[DbId] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )
    region_code: Mapped[str | None] = mapped_column(
        String(10),
        ForeignKey("energy_prices.regions.code"),
        nullable=True,
    )
    market_type: Mapped[str | None] = mapped_column(
        String(10),
        ForeignKey("energy_prices.markets.type"),
        nullable=True,
    )
    freq: Mapped[str] = mapped_column(String(10), nullable=False)
    important_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    source: Mapped[str] = mapped_column(String(100), nullable=False)
    unit: Mapped[str] = mapped_column(String(10), nullable=False)
    tz: Mapped[str] = mapped_column(String(10), nullable=False)

    def __repr__(self) -> str:
        return (
            f"{self.schema_name}.{self.__tablename__}("
            f"price_metadata_id={self.price_metadata_id!r}, "
            f"region_code={self.region_code!r}, "
            f"market_type={self.market_type!r}, "
            f"freq={self.freq!r}, "
            f"source={self.source!r}, "
            f"unit={self.unit!r}, "
            f"tz={self.tz!r})"
        )


class PriceData(Base):
    schema_name = "energy_prices"

    __tablename__ = "price_data"
    __table_args__ = {"schema": schema_name}

    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), primary_key=True)
    price_metadata_id: Mapped[DbId] = mapped_column(
        Integer,
        ForeignKey(PriceMetadata.price_metadata_id),
        nullable=False,
        primary_key=True,
    )
    energy_price: Mapped[Decimal | None] = mapped_column(Numeric, nullable=True)

    def __repr__(self) -> str:
        return (
            f"{self.schema_name}.{self.__tablename__}("
            f"timestamp={self.timestamp}, "
            f"price_metadata_id={self.price_metadata_id}, "
            f"energy_price={self.energy_price})"
        )


def main() -> None:
    db_engine = create_db_engine()
    session = create_session(db_engine)
    Base.metadata.create_all(db_engine)
    rows = session.query(PriceData).limit(50).all()

    for row in rows:
        print(row)


if __name__ == "__main__":
    main()
