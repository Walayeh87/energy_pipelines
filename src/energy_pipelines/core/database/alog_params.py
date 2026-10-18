from typing import TypedDict

from pydantic import BaseModel, ConfigDict


class ScheduleSettingTemps(TypedDict):
    min_temp: int | float
    max_temp: int | float
    default_temp: int | float


class AdvancedScheduleSettingTemps(TypedDict):
    min_temp: int | float
    max_temp: int | float
    default_temp: int | float
    mean_temp: int | float


class TempScheduleCreatorParams(BaseModel):
    model_config = ConfigDict(extra="forbid")

    temps: ScheduleSettingTemps
    freq: str


class AdvancedTempScheduleCreatorParams(BaseModel):
    model_config = ConfigDict(extra="forbid")

    temps: AdvancedScheduleSettingTemps
    freq: str


ALGO_MODEL_MAPPER = {
    # If you rename the algo names in the mapper, don't forget to rename the corresponding names
    # in algos.algo table!
    "temp_schedule_creator": TempScheduleCreatorParams,
    "advanced_temp_schedule_creator": AdvancedTempScheduleCreatorParams,
}
