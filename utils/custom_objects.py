from dataclasses import dataclass


@dataclass
class DbId:
    value: int

    def __post_init__(self) -> None:
        if self.value < 1:
            raise ValueError("ID must be a positive integer.")
