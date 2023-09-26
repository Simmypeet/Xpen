from dataclasses import dataclass
from enum import Enum
import datetime


class RecordType(Enum):
    """An enumeration of all supported record types"""

    INCOME = 1
    EXPENSE = 2


@dataclass
class Record:
    tag: str | None
    amount: int
    date: datetime.date
    note: str | None
    type: RecordType


@dataclass
class RecordFileKey:
    month_number: int
    year_number: int


@dataclass
class CustomAccountAvatar:
    path: str


@dataclass
class DefaultAccountAvatar:
    number: int


AccountAvator = CustomAccountAvatar | DefaultAccountAvatar


class Account:
    __account_data_directory: str
    __avatar: AccountAvator
    __account_name: str

    __found_record_files: list[RecordFileKey]

    def __init__(self, account_name: str) -> None:
        self.__account_name = account_name

    def get_account_name(self) -> str:
        return self.__account_name
