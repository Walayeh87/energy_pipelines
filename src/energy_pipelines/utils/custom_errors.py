class EmptyTableError(Exception):
    """Raised when a DB table is empty."""


class APIFetchingError(Exception):
    """Raised when an error occurs while fetching data from the API."""
