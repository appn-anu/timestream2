import datetime

try:
    dataclass()
except NameError:
    from dataclasses import dataclass


@dataclass
class Timepoint:
    """
    Timepoint: a generalised "moment in time", including both timepoint and
    optional index within a timepoint.

    >>> Timepoint(
    """
    timestamp: datetime.datetime
    subsecond: int = 0
    index: str

    def __str__(self):
        idx = "" if self.index is None else f"_{self.index}"
        subsec = f"_{self.subsec:02d}"
        return f"{self.timestamp.strftime('%Y_%m_%d_%H_%M_%S')}{subsec}{idx}"

