from dataclasses import dataclass

from typing import Optional
from application.filter import Filter


class ToAccountPage:
    """
    Signals to go to account page
    """

    pass


@dataclass(frozen=True)
class ToRecordPage:
    """
    Signals to go to record page
    """

    filter: Optional[Filter]

    pass


@dataclass(frozen=True)
class Date:
    month: int
    year: int


@dataclass(frozen=True)
class ToCalendarPage:
    """
    Signals to go to calendar page
    """

    date: Optional[Date]

    pass
