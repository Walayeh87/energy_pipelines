from datetime import datetime

from sqlalchemy import DateTime, Integer, Numeric, create_engine
from sqlalchemy.orm import Mapped, declarative_base, mapped_column, sessionmaker

from src.energy_pipeline.config.settings import DB_URL
from utils.custom_objects import DbId

Base = declarative_base()


class PriceData(Base):
    __tablename__ = "price_data"
    __table_args__ = ({"schema": "energy_prices"},)

    timestamp: Mapped[datetime] = mapped_column(DateTime, primary_key=True, unique=True)
    price_metadata_id: Mapped[DbId] = mapped_column(Integer, nullable=False, primary_key=True)
    energy_price: Mapped[float] = mapped_column(Numeric)

    def __repr__(self) -> str:
        schema_name = self.__table_args__[0].get("schema")
        return (
            f"{schema_name}.{self.__tablename__}("
            f"timestamp={self.timestamp}, "
            f"price_metadata_id={self.price_metadata_id}, "
            f"energy_price={self.energy_price})"
        )


def main() -> None:
    db_engine = create_engine(DB_URL)
    Session = sessionmaker(bind=db_engine)
    Base.metadata.create_all(db_engine)
    with Session() as session:
        rows = session.query(PriceData).limit(50).all()

    for row in rows:
        print(row)


if __name__ == "__main__":
    main()
