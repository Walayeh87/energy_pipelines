from unittest.mock import Mock, patch

import pytest
from requests.exceptions import ConnectionError, RequestException, Timeout

from data_source.data_fetcher_via_url import fetch_data


# Fixtures
@pytest.fixture
def mock_successful_response() -> None:
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"price": [50.0, 51.0], "unit": "EUR/MWh"}
    return mock_response


@pytest.fixture
def mock_failing_response() -> None:
    mock_response = Mock()
    mock_response.status_code = 500
    mock_response.raise_for_status.side_effect = RequestException("Server Error")
    return mock_response


# Tests for input validation
def test_invalid_max_attempts() -> None:
    with pytest.raises(ValueError):
        fetch_data("https://api.example.com", max_attempts=0)


def test_invalid_retry_delay() -> None:
    with pytest.raises(ValueError):
        fetch_data("https://api.example.com", retry_delay_in_s=0)


# Tests for successful requests
data_fetcher_path = "data_source.data_fetcher_via_url"


@patch(f"{data_fetcher_path}.requests.get")
@patch(f"{data_fetcher_path}.time.sleep")
def test_success_on_retry(mock_sleep, mock_get, mock_successful_response) -> None:
    """Test successful data fetch after retrying failed attempts"""
    # First two attempts fail, third succeeds
    mock_failure = Mock()
    mock_failure.raise_for_status.side_effect = ConnectionError("Connection failed")

    mock_get.side_effect = [mock_failure, mock_failure, mock_successful_response]

    url = "https://api.example.com"
    result = fetch_data(url, max_attempts=3, retry_delay_in_s=1)

    assert result == {"price": [50.0, 51.0], "unit": "EUR/MWh"}
    assert mock_get.call_count == 3
    assert mock_sleep.call_count == 2
    mock_sleep.assert_called_with(1)


# Tests for failure scenarios
@patch(f"{data_fetcher_path}.requests.get")
@patch(f"{data_fetcher_path}.time.sleep")
def test_all_attempts_fail(mock_sleep, mock_get, mock_failing_response) -> None:
    """Test that RuntimeError is raised when all attempts fail"""
    mock_get.return_value = mock_failing_response

    url = "https://api.example.com"
    max_attempts = 3

    with pytest.raises(RuntimeError, match=f"Failed to fetch data after {max_attempts} attempts"):
        fetch_data(url, max_attempts=max_attempts, retry_delay_in_s=1)

    assert mock_get.call_count == max_attempts
    assert mock_sleep.call_count == max_attempts - 1


@patch(f"{data_fetcher_path}.requests.get")
def test_connection_error_retries(mock_get) -> None:
    """Test retry behavior on connection errors"""
    mock_get.side_effect = ConnectionError("Cannot connect to server")

    url = "https://api.example.com"
    max_attempts = 2

    with pytest.raises(RuntimeError, match=f"Failed to fetch data after {max_attempts} attempts"):
        fetch_data(url, max_attempts=max_attempts, retry_delay_in_s=1)

    assert mock_get.call_count == max_attempts


@patch(f"{data_fetcher_path}.requests.get")
def test_timeout_error_retries(mock_get) -> None:
    """Test retry behavior on timeout errors"""
    mock_get.side_effect = Timeout("Request timed out")

    url = "https://api.example.com"
    max_attempts = 2

    with pytest.raises(RuntimeError, match=f"Failed to fetch data after {max_attempts} attempts"):
        fetch_data(url, max_attempts=max_attempts, retry_delay_in_s=1)

    assert mock_get.call_count == max_attempts


@patch(f"{data_fetcher_path}.requests.get")
def test_http_404_error(mock_get) -> None:
    """Test behavior on HTTP 404 error"""
    mock_response = Mock()
    mock_response.status_code = 404
    mock_response.raise_for_status.side_effect = RequestException("404 Not Found")
    mock_get.return_value = mock_response

    url = "https://api.example.com/invalid"
    max_attempts = 2

    with pytest.raises(RuntimeError, match=f"Failed to fetch data after {max_attempts} attempts"):
        fetch_data(url, max_attempts=max_attempts, retry_delay_in_s=1)

    assert mock_get.call_count == max_attempts


# Test for timeout parameter
@patch(f"{data_fetcher_path}.requests.get")
def test_timeout_parameter(mock_get, mock_successful_response) -> None:
    """Test that timeout parameter is passed correctly"""
    mock_get.return_value = mock_successful_response

    fetch_data("https://api.example.com")

    # Check that timeout was passed
    mock_get.assert_called_with("https://api.example.com", timeout=30)


# Parameterized tests for different HTTP status codes
@pytest.mark.parametrize(
    "status_code,error_message",
    [
        (400, "Bad Request"),
        (401, "Unauthorized"),
        (403, "Forbidden"),
        (404, "Not Found"),
        (500, "Internal Server Error"),
        (502, "Bad Gateway"),
        (503, "Service Unavailable"),
    ],
)
@patch(f"{data_fetcher_path}.requests.get")
def test_various_http_errors(mock_get, status_code, error_message) -> None:
    """Test retry behavior for various HTTP error status codes"""
    mock_response = Mock()
    mock_response.status_code = status_code
    mock_response.raise_for_status.side_effect = RequestException(error_message)
    mock_get.return_value = mock_response

    url = "https://api.example.com"
    max_attempts = 2

    with pytest.raises(RuntimeError):
        fetch_data(url, max_attempts=max_attempts, retry_delay_in_s=1)

    assert mock_get.call_count == max_attempts


# Test for response.json() parsing error
@patch(f"{data_fetcher_path}.requests.get")
def test_invalid_json_response(mock_get) -> None:
    """Test handling of invalid JSON response"""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.raise_for_status.return_value = None
    mock_response.json.side_effect = ValueError("Invalid JSON")
    mock_get.return_value = mock_response

    url = "https://api.example.com"

    with pytest.raises(ValueError):
        fetch_data(url, max_attempts=1, retry_delay_in_s=1)
