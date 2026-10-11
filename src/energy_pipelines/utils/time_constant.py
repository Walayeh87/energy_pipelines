from enum import Enum


class TimeConstant(int, Enum):
    SEC_IN_MIN = 60
    SEC_IN_H = 3600
    SEC_IN_DAY = 3600 * 24
    SEC_IN_WEEK = 3600 * 24 * 7

    MIN_IN_H = 60
    MIN_IN_DAY = 60 * 24

    H_IN_DAY = 24

    DAY_IN_WEEK = 7

    def __repr__(self) -> str:
        return repr(self.value)
