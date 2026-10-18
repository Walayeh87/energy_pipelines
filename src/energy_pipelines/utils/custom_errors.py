class EmptyTableError(Exception):
    """Raised when a DB table is empty."""


class TempSchedulePipelineError(Exception):
    """Raised when an error occurs in the temperature schedule pipeline."""
