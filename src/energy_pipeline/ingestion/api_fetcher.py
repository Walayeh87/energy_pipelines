import logging
import time
from typing import Any

import requests
from requests import RequestException

from constants.time_constant import TimeConstant

logger = logging.getLogger(__name__)


def fetch_data_from_api(
    url: str,
    max_attempts: int = 200,
    retry_delay_in_s: int = 30,
    request_timeout_in_s: int = 30,
) -> dict[str, Any]:
    """
    Fetch data from API with retry logic.

    Args:
        url: API endpoint URL
        max_attempts: Number of retry attempts
        retry_delay_in_s: Seconds to wait between retries
        request_timeout_in_s: Timeout for each request
    Returns:
        JSON response as dictionary

    Raises:
        Exception: If all retry attempts fail
    """
    if max_attempts < 1:
        raise ValueError(f"max_attempts must be at least 1. Got {max_attempts}")

    if retry_delay_in_s < 1:
        raise ValueError(f"retry_delay_in_s must be at least 1 second. Got {retry_delay_in_s}")

    if request_timeout_in_s < 1:
        raise ValueError(f"request_timeout_in_s must be at least 1 second. Got {request_timeout_in_s}")

    if retry_delay_in_s * max_attempts > 2 * TimeConstant.SEC_IN_H:
        raise ValueError("Total retry time exceeds 2 hours. Adjust retry parameters.")

    for attempt in range(1, max_attempts + 1):
        try:
            response = requests.get(url, timeout=request_timeout_in_s)
            response.raise_for_status()  # Raises HTTPError for 4xx/5xx
            data_as_dict = response.json()

            if len(data_as_dict) == 0:
                logger.warning("Fetched data is empty!")
            else:
                logger.info("Items have been fetched successfully from the source.")

            return data_as_dict

        except RequestException as e:
            if attempt == max_attempts:
                raise RuntimeError(f"Failed to fetch data after {max_attempts} attempts.") from e

            logger.warning(f"Attempt {attempt} failed: {e}. Retrying in {retry_delay_in_s} seconds...")
            time.sleep(retry_delay_in_s)

        except ValueError as e:
            raise ValueError("Invalid json.") from e

    raise Exception(f"Unexpected error in {fetch_data_from_api.__name__}, most likely due to network issues.")
