import logging
from datetime import datetime, timedelta

from src.energy_pipeline.config.settings import ENERGY_PRICE_URL

logger = logging.getLogger(__name__)


def create_url_for_tomorrows_energy_prices(bidding_zone: str) -> str:
    if len(bidding_zone) == 0:
        raise ValueError("bidding_zone must not be empty.")

    url = f"{ENERGY_PRICE_URL}?bzn={bidding_zone}&start={get_tomorrows_date()}"
    logger.info(f"The energy-price-URL '{url}' has been created.")

    return url


def get_tomorrows_date() -> datetime:
    date = datetime.now().date() + timedelta(days=1)
    return datetime(year=date.year, month=date.month, day=date.day)
