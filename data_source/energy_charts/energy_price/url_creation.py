import logging
from datetime import datetime, timedelta

ENERGY_PRICE_URL = (
    "https://api.energy-charts.info/price"  # TODO: it should be gotten from the DB
)

logger = logging.getLogger(__name__)


def create_url_for_tomorrows_energy_prices(bidding_zone: str) -> str:
    if len(bidding_zone) == 0:
        raise ValueError("bidding_zone must not be empty.")

    url = f"{ENERGY_PRICE_URL}?bzn={bidding_zone}&start={get_tomorrows_date()}"
    logger.info(f"The energy-price-URL '{url}' has been created.")

    return url


def create_url_for_range_of_energy_prices(
    bidding_zone: str, date_start: datetime, date_end: datetime | None = None
) -> str:
    """If date_end is None, the URL will be created for the range from date_start to the today's/tomorrow's date (
    depending on the day ahead price publishing time)"""
    if date_end is None:
        date_end = get_tomorrows_date()

    if date_start >= date_end:
        raise ValueError("date_start must be earlier than date_end.")

    if date_start >= datetime.now():
        raise ValueError("date_start must be earlier than the current time.")

    url = f"{ENERGY_PRICE_URL}?bzn={bidding_zone}&start={date_start}&end={date_end}"

    logger.info(f"The energy-price-URL '{url}' has been created.")

    return url


def get_tomorrows_date() -> datetime:
    date = datetime.now().date() + timedelta(days=1)
    return datetime(year=date.year, month=date.month, day=date.day)
