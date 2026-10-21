from dataclasses import dataclass, fields

from pandas import DataFrame

from energy_pipelines.core.database.table_models import AlgosOutput


@dataclass
class TempScheduleValidationResult:
    # IMPORTANT!
    # When is_valid is True, the rest must be None.
    # When is_valid is False, one of the rest must be True, the others are None.
    # If this behavior changed, consider modifying get_error!
    is_valid: bool

    has_length_mismatch: bool | None = None
    timestamps_have_nats: bool | None = None
    values_have_nans: bool | None = None
    implausible_values: bool | None = None


def get_error(result: TempScheduleValidationResult) -> str:
    return next(field.name for field in fields(result) if getattr(result, field.name) is True)


def validate_backup_temp_schedule(
    temp_schedule: DataFrame,
    default_temp: int | float,
    expected_length: int,
) -> TempScheduleValidationResult:
    if len(temp_schedule) != expected_length:
        return TempScheduleValidationResult(is_valid=False, has_length_mismatch=True)

    if temp_schedule[AlgosOutput.timestamp.key].isna().any():
        return TempScheduleValidationResult(is_valid=False, timestamps_have_nats=True)

    if temp_schedule[AlgosOutput.values.key].isna().any():
        return TempScheduleValidationResult(is_valid=False, values_have_nans=True)

    if (
        temp_schedule[AlgosOutput.values.key].min() != default_temp
        or temp_schedule[AlgosOutput.values.key].max() != default_temp
    ):
        return TempScheduleValidationResult(is_valid=False, implausible_values=True)

    return TempScheduleValidationResult(is_valid=True)


def validate_temp_schedule(
    temp_schedule: DataFrame,
    min_temp: int | float,
    max_temp: int | float,
    expected_length: int,
) -> TempScheduleValidationResult:
    if len(temp_schedule) != expected_length:
        return TempScheduleValidationResult(is_valid=False, has_length_mismatch=True)

    if temp_schedule[AlgosOutput.timestamp.key].isna().any():
        return TempScheduleValidationResult(is_valid=False, timestamps_have_nats=True)

    if temp_schedule[AlgosOutput.values.key].isna().any():
        return TempScheduleValidationResult(is_valid=False, values_have_nans=True)

    if (
        temp_schedule[AlgosOutput.values.key].min() < min_temp
        or temp_schedule[AlgosOutput.values.key].max() > max_temp
    ):
        return TempScheduleValidationResult(is_valid=False, implausible_values=True)

    return TempScheduleValidationResult(is_valid=True)
