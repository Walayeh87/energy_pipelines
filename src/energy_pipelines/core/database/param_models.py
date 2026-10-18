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


ALGO_MODEL_MAPPER = {1: TempScheduleCreatorParams, 2: AdvancedTempScheduleCreatorParams}
