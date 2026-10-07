from datetime import datetime
from unittest.mock import MagicMock, patch

import psycopg
import pytest
import pytz
from fastapi.testclient import TestClient

import data_source
from data_source.data_fetchers_from_db import app
from data_source.energy_charts.energy_price.price_col_name_in_db import (
    PriceDataColNameInDB,
)
from data_source.utilities.price_structure_in_db import PriceStructureInDB

test_client = TestClient(app)


def test_fetch_energy_prices_success() -> None:
    mock_rows = [
        {
            PriceDataColNameInDB.TIMESTAMP: "2026-06-01T00:00:00",
            PriceDataColNameInDB.ENERGY_PRICE: 50.0,
        },
        {
            PriceDataColNameInDB.TIMESTAMP: "2026-06-02T00:00:00",
            PriceDataColNameInDB.ENERGY_PRICE: 55.0,
        },
    ]

    # Mock cursor
    mock_cursor = MagicMock()
    mock_cursor.fetchall.return_value = mock_rows

    mock_connection = MagicMock()
    mock_connection.__enter__.return_value = mock_connection
    mock_connection.cursor.return_value.__enter__.return_value = mock_cursor

    with (
        patch.object(
            data_source.data_fetchers_from_db,
            "establish_db_connection",
            return_value=mock_connection,
        ),
        patch.object(data_source.data_fetchers_from_db, "create_energy_price_fetching_query") as mock_price_query,
        patch.object(data_source.data_fetchers_from_db, "fetch_earliest_timestamp_in_table") as earliest_timestamp,
        patch.object(data_source.data_fetchers_from_db, "get_current_date") as mocked_current_date,
    ):
        start_date = datetime(2026, 6, 1, tzinfo=pytz.UTC)
        end_date = datetime(2026, 6, 2, tzinfo=pytz.UTC)
        mock_price_query.return_value = (
            f"SELECT * FROM {PriceStructureInDB.SCHEMA_NAME}.{PriceStructureInDB.TABLE_NAME}",
            (1, start_date, end_date),
        )

        earliest_timestamp.return_value = datetime(2026, 5, 1, tzinfo=pytz.UTC)
        mocked_current_date.return_value = datetime(2026, 8, 1, tzinfo=pytz.UTC)

        response = test_client.get(
            "/energy_prices",
            params={
                "price_metadata_id": 1,
                "start_date": start_date,
                "end_date": end_date,
            },
        )

    mock_cursor.execute.assert_called_once()
    mock_price_query.assert_called_once()
    earliest_timestamp.assert_called_once()
    assert response.status_code == 200
    assert response.json() == mock_rows


def test_fetch_energy_prices_when_start_equals_end() -> None:
    mock_rows = [
        {
            PriceDataColNameInDB.TIMESTAMP: "2026-06-01T00:00:00",
            PriceDataColNameInDB.ENERGY_PRICE: 50.0,
        },
        {
            PriceDataColNameInDB.TIMESTAMP: "2026-06-02T00:00:00",
            PriceDataColNameInDB.ENERGY_PRICE: 55.0,
        },
    ]

    # Mock cursor
    mock_cursor = MagicMock()
    mock_cursor.fetchall.return_value = mock_rows

    mock_connection = MagicMock()
    mock_connection.__enter__.return_value = mock_connection
    mock_connection.cursor.return_value.__enter__.return_value = mock_cursor

    with (
        patch.object(
            data_source.data_fetchers_from_db,
            "establish_db_connection",
            return_value=mock_connection,
        ),
        patch.object(data_source.data_fetchers_from_db, "create_energy_price_fetching_query") as mock_price_query,
        patch.object(data_source.data_fetchers_from_db, "fetch_earliest_timestamp_in_table") as earliest_timestamp,
        patch.object(data_source.data_fetchers_from_db, "get_current_date") as mocked_current_date,
    ):
        start_date = datetime(2026, 6, 1, tzinfo=pytz.UTC)
        end_date = datetime(2026, 6, 1, tzinfo=pytz.UTC)
        mock_price_query.return_value = (
            f"SELECT * FROM {PriceStructureInDB.SCHEMA_NAME}.{PriceStructureInDB.TABLE_NAME}",
            (1, start_date, end_date),
        )

        earliest_timestamp.return_value = datetime(2026, 5, 1, tzinfo=pytz.UTC)
        mocked_current_date.return_value = datetime(2026, 8, 1, tzinfo=pytz.UTC)

        with pytest.raises(ValueError):
            test_client.get(
                "/energy_prices",
                params={
                    "price_metadata_id": 1,
                    "start_date": start_date,
                    "end_date": end_date,
                },
            )


def test_fetch_energy_prices_when_start_is_before_earliest_ts() -> None:
    mock_rows = [
        {
            PriceDataColNameInDB.TIMESTAMP: "2026-06-01T00:00:00",
            PriceDataColNameInDB.ENERGY_PRICE: 50.0,
        },
        {
            PriceDataColNameInDB.TIMESTAMP: "2026-06-02T00:00:00",
            PriceDataColNameInDB.ENERGY_PRICE: 55.0,
        },
    ]

    # Mock cursor
    mock_cursor = MagicMock()
    mock_cursor.fetchall.return_value = mock_rows

    mock_connection = MagicMock()
    mock_connection.__enter__.return_value = mock_connection
    mock_connection.cursor.return_value.__enter__.return_value = mock_cursor

    with (
        patch.object(
            data_source.data_fetchers_from_db,
            "establish_db_connection",
            return_value=mock_connection,
        ),
        patch.object(data_source.data_fetchers_from_db, "create_energy_price_fetching_query") as mock_price_query,
        patch.object(data_source.data_fetchers_from_db, "fetch_earliest_timestamp_in_table") as earliest_timestamp,
        patch.object(data_source.data_fetchers_from_db, "get_current_date") as mocked_current_date,
    ):
        start_date = datetime(2026, 1, 1, tzinfo=pytz.UTC)
        end_date = datetime(2026, 6, 1, tzinfo=pytz.UTC)
        mock_price_query.return_value = (
            f"SELECT * FROM {PriceStructureInDB.SCHEMA_NAME}.{PriceStructureInDB.TABLE_NAME}",
            (1, start_date, end_date),
        )

        earliest_timestamp.return_value = datetime(2026, 5, 1, tzinfo=pytz.UTC)
        mocked_current_date.return_value = datetime(2026, 8, 1, tzinfo=pytz.UTC)

        with pytest.raises(ValueError):
            test_client.get(
                "/energy_prices",
                params={
                    "price_metadata_id": 1,
                    "start_date": start_date,
                    "end_date": end_date,
                },
            )


def test_fetch_energy_prices_when_end_is_in_future() -> None:
    mock_rows = [
        {
            PriceDataColNameInDB.TIMESTAMP: "2026-06-01T00:00:00",
            PriceDataColNameInDB.ENERGY_PRICE: 50.0,
        },
        {
            PriceDataColNameInDB.TIMESTAMP: "2026-06-02T00:00:00",
            PriceDataColNameInDB.ENERGY_PRICE: 55.0,
        },
    ]

    # Mock cursor
    mock_cursor = MagicMock()
    mock_cursor.fetchall.return_value = mock_rows

    mock_connection = MagicMock()
    mock_connection.__enter__.return_value = mock_connection
    mock_connection.cursor.return_value.__enter__.return_value = mock_cursor

    with (
        patch.object(
            data_source.data_fetchers_from_db,
            "establish_db_connection",
            return_value=mock_connection,
        ),
        patch.object(data_source.data_fetchers_from_db, "create_energy_price_fetching_query") as mock_price_query,
        patch.object(data_source.data_fetchers_from_db, "fetch_earliest_timestamp_in_table") as earliest_timestamp,
        patch.object(data_source.data_fetchers_from_db, "get_current_date") as mocked_current_date,
    ):
        start_date = datetime(2026, 1, 1, tzinfo=pytz.UTC)
        end_date = datetime(2026, 6, 2, tzinfo=pytz.UTC)
        mock_price_query.return_value = (
            f"SELECT * FROM {PriceStructureInDB.SCHEMA_NAME}.{PriceStructureInDB.TABLE_NAME}",
            (1, start_date, end_date),
        )

        earliest_timestamp.return_value = datetime(2026, 4, 1, tzinfo=pytz.UTC)
        mocked_current_date.return_value = datetime(2026, 5, 1, tzinfo=pytz.UTC)

        with pytest.raises(ValueError):
            test_client.get(
                "/energy_prices",
                params={
                    "price_metadata_id": 1,
                    "start_date": start_date,
                    "end_date": end_date,
                },
            )


def test_fetch_energy_prices_db_error() -> None:
    mock_cursor = MagicMock()
    mock_cursor.execute.side_effect = psycopg.Error("DB failure")

    mock_connection = MagicMock()
    mock_connection.__enter__.return_value = mock_connection
    mock_connection.cursor.return_value.__enter__.return_value = mock_cursor

    with (
        patch.object(
            data_source.data_fetchers_from_db,
            "establish_db_connection",
            return_value=mock_connection,
        ),
        patch.object(data_source.data_fetchers_from_db, "create_energy_price_fetching_query") as mock_price_query,
        patch.object(data_source.data_fetchers_from_db, "fetch_earliest_timestamp_in_table") as earliest_timestamp,
        patch.object(data_source.data_fetchers_from_db, "get_current_date") as mocked_current_date,
    ):
        start_date = datetime(2026, 6, 1, tzinfo=pytz.UTC)
        end_date = datetime(2026, 6, 2, tzinfo=pytz.UTC)
        mock_price_query.return_value = (
            f"SELECT * FROM {PriceStructureInDB.SCHEMA_NAME}.{PriceStructureInDB.TABLE_NAME}",
            (1, start_date, end_date),
        )

        earliest_timestamp.return_value = datetime(2026, 5, 1, tzinfo=pytz.UTC)
        mocked_current_date.return_value = datetime(2026, 8, 1, tzinfo=pytz.UTC)

        response = test_client.get(
            "/energy_prices",
            params={
                "price_metadata_id": 1,
                "start_date": start_date,
                "end_date": end_date,
            },
        )

    mock_cursor.execute.assert_called_once()
    mock_price_query.assert_called_once()
    earliest_timestamp.assert_called_once()
    assert response.status_code == 500
    assert response.json()["detail"] == "Database error"
