from datetime import datetime
from unittest.mock import patch

import pytest

from data_source.energy_charts.energy_price.url_creation import (
    ENERGY_PRICE_URL,  # TODO get it from DB
    create_url_for_range_of_energy_prices,
    create_url_for_tomorrows_energy_prices,
)

url_creation_path = "data_source.energy_charts.energy_price.url_creation"


@patch(f"{url_creation_path}.get_tomorrows_date")
def test_create_url_for_tomorrows_energy_prices_with_empty_bidding_zone(
    mocked_function,
) -> None:
    mocked_tomorrows_date = "2025-01-01"
    mocked_function.return_value = mocked_tomorrows_date
    bidding_zone = ""

    with pytest.raises(ValueError):
        create_url_for_tomorrows_energy_prices(bidding_zone=bidding_zone)


@patch(f"{url_creation_path}.get_tomorrows_date")
def test_create_url_for_tomorrows_energy_prices(mocked_function) -> None:
    mocked_tomorrows_date = "2025-01-01"
    mocked_function.return_value = mocked_tomorrows_date
    bidding_zone = "DE-LU"
    url = create_url_for_tomorrows_energy_prices(bidding_zone=bidding_zone)

    assert url == f"{ENERGY_PRICE_URL}?bzn={bidding_zone}&start={mocked_tomorrows_date}"


def test_create_url_for_range_of_energy_prices_when_date_end_is_not_none() -> None:
    bidding_zone = "DE-LU"
    date_start = datetime(2025, 1, 1)
    date_end = datetime(2025, 1, 2)

    url = create_url_for_range_of_energy_prices(
        bidding_zone=bidding_zone, date_start=date_start, date_end=date_end
    )

    assert (
        url
        == f"{ENERGY_PRICE_URL}?bzn={bidding_zone}&start={date_start}&end={date_end}"
    )


@patch(f"{url_creation_path}.get_tomorrows_date")
def test_create_url_for_range_of_energy_prices_when_date_end_is_none(
    mocked_function,
) -> None:
    mocked_tomorrows_date = datetime(2025, 1, 2)
    mocked_function.return_value = mocked_tomorrows_date
    bidding_zone = "DE-LU"
    date_start = datetime(2025, 1, 1)

    url = create_url_for_range_of_energy_prices(
        bidding_zone=bidding_zone, date_start=date_start, date_end=None
    )

    assert (
        url
        == f"{ENERGY_PRICE_URL}?bzn={bidding_zone}&start={date_start}&end={mocked_tomorrows_date}"
    )
