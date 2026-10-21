from pandas.core.frame import DataFrame

from energy_pipelines.core.database.table_models import AlgosOutput


def preprocess_temp_schedule(
    temp_schedule: DataFrame,
    site_id: int,
    algo_id: int,
) -> DataFrame:
    only_col = temp_schedule.columns[0]
    temp_schedule = temp_schedule.rename(columns={only_col: AlgosOutput.values.key})
    temp_schedule[AlgosOutput.site_id.key] = site_id
    temp_schedule[AlgosOutput.algo_id.key] = algo_id
    temp_schedule = temp_schedule.reset_index(names=AlgosOutput.timestamp.key)

    temp_schedule = temp_schedule.sort_values(AlgosOutput.timestamp.key)

    return temp_schedule
