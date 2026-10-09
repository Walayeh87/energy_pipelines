from sqlalchemy.orm import Session

from src.energy_pipeline.database.models import PriceMetadata, Regions


def get_bidding_zone_and_price_metadata_ids_mapper(session: Session, bidding_zones: list[str]) -> dict[str, int]:
    mapper = {}
    for bidding_zone in bidding_zones:
        result = (
            session.query(PriceMetadata.price_metadata_id)
            .filter(PriceMetadata.bidding_zone == bidding_zone)
            .filter(PriceMetadata.market_type == "DAY_AHEAD")
            .all()
        )
        invalid_id_value = 0
        price_metadata_id = [price_metadata_id for (price_metadata_id,) in result][0] if result else invalid_id_value
        mapper[bidding_zone] = price_metadata_id

    return mapper


def get_bidding_zones(session: Session) -> list[str]:
    result = session.query(Regions.bidding_zone).all()

    return [bidding_zone for (bidding_zone,) in result]
