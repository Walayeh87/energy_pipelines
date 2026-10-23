"""The mappers here should be updated manually when new algo/site is added."""

from energy_pipelines.core.database.param_models import TempScheduleCreatorParams

ALGO_MODEL_MAPPER = {1: TempScheduleCreatorParams}
SITE_MAPPER = {"First Site": 3, "Second Site": 4, "Third Site": 9}  # It should be updated manually
