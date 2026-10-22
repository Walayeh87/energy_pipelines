from datetime import datetime

from pandas.core.frame import DataFrame

from energy_pipelines.core.database.table_models import AlgosOutput, FailingAlgosOutput
from energy_pipelines.core.processing.energy_price_processing import EnergyPriceProcessingResult


def preprocess_failing_temp_schedule(
    site_id: int,
    algo_id: int,
    temp_schedule: DataFrame,
    reporting_time_in_local_tz: datetime,
    failing_reason: str,
    energy_price_processing_result: EnergyPriceProcessingResult,
    is_backup: bool,
) -> DataFrame:
    failing_algos_output = DataFrame(index=temp_schedule.index)

    failing_algos_output[FailingAlgosOutput.site_id.key] = site_id
    failing_algos_output[FailingAlgosOutput.algo_id.key] = algo_id

    processed_prices = energy_price_processing_result.processed_prices.reset_index(drop=True)
    mask_of_filled_values = energy_price_processing_result.mask_of_filled_values.reset_index(drop=True)
    failing_algos_output[FailingAlgosOutput.processed_prices.key] = (
        processed_prices if len(processed_prices) > 0 else None
    )
    failing_algos_output[FailingAlgosOutput.mask_of_filled_prices_values.key] = (
        mask_of_filled_values if len(mask_of_filled_values) > 0 else None
    )
    failing_algos_output[FailingAlgosOutput.price_processing_issue.key] = (
        energy_price_processing_result.processing_issue
    )

    failing_algos_output[FailingAlgosOutput.values.key] = temp_schedule[AlgosOutput.values.key]
    failing_algos_output[FailingAlgosOutput.timestamp.key] = temp_schedule[AlgosOutput.timestamp.key]
    failing_algos_output[FailingAlgosOutput.reporting_time_in_local_tz.key] = reporting_time_in_local_tz
    failing_algos_output[FailingAlgosOutput.failing_reason.key] = failing_reason
    failing_algos_output[FailingAlgosOutput.is_backup.key] = is_backup

    return failing_algos_output
