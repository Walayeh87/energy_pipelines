import logging

from energy_pipelines.core.config.settings import ENERGY_PRICE_URL
from energy_pipelines.utils.time_helpers import get_tomorrows_date

logger = logging.getLogger(__name__)


def create_url_for_tomorrows_energy_prices(bidding_zone: str) -> str:
    if len(bidding_zone) == 0:
        raise ValueError("bidding_zone must not be empty.")

    # url = f"{ENERGY_PRICE_URL}?bzn={bidding_zone}&start=2026-10-01"  # For testing purposes
    url = f"{ENERGY_PRICE_URL}?bzn={bidding_zone}&start={get_tomorrows_date(tz=None)}"
    logger.info(f"The energy-price-URL '{url}' has been created.")

    return url
