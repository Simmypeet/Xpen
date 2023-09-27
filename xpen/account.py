from dataclasses import dataclass
from enum import Enum
from datetime import date
import os


class RecordType(Enum):
    """An enumeration of all supported record types"""

    INCOME = 1
    EXPENSE = 2


@dataclass
class Record:
    tag: str | None
    amount: int
    date: date
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


class RecordFile:
    __records: list[Record]
    __record_file_key: RecordFileKey

    __dirty: bool


class Account:
    __account_data_directory: str

    __record_files_by_key: dict[RecordFileKey, RecordFile]

    def __init__(self, account_data_directory: str) -> None:
        self.__account_data_directory = account_data_directory

    def __search_available_record_files(self) -> list[RecordFileKey]:
        # list all the .json file with YYYY_MM.json format
        # and return a list of RecordFileKey

        records: list[RecordFileKey] = []
        for file_name in os.listdir(self.__account_data_directory):
            if not (file_name.endswith(".json") or os.path.isfile(file_name)):
                continue

            split = file_name.split("_")

            if len(split) != 2:
                continue

            year_number: int = 0
            month_number: int = 0

            try:
                year_number = int(split[0])
                month_number = int(split[1])
            except Exception:
                continue

            try:
                date(year_number, month_number, 1)
            except Exception:
                continue

            records.append(RecordFileKey(month_number, year_number))

        return records

    def get_account_name(self) -> str:
        # returns the stem of the account data directory
        return os.path.basename(self.__account_data_directory)

    def get_last_modified(self) -> date | None:
        return date(2023, 1, 1)

    def get_current_balance(self) -> int:
        return 69420
