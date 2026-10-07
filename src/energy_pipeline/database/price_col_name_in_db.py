from enum import StrEnum


class PriceDataColNameInDB(StrEnum):
    TIMESTAMP = "timestamp"
    ENERGY_PRICE = "energy_price"
    PRICE_METADATA_ID = "price_metadata_id"
