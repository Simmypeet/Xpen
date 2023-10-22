from __future__ import annotations

import atexit
import json
import os
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any, Optional, Sequence

from backend.corrupted import CorruptedDataFileError


@dataclass
class Record:
    tag: Optional[str]
    balance: Decimal
    date: datetime
    note: Optional[str]


@dataclass
class RecordFileKey:
    month_number: int
    year_number: int

    def __hash__(self) -> int:
        return hash((self.month_number, self.year_number))

    def __eq__(self, __value: object) -> bool:
        if not isinstance(__value, RecordFileKey):
            return False

        return (
            self.month_number == __value.month_number
            and self.year_number == __value.year_number
        )


@dataclass
class RecordDiff:
    record: Record
    diff: Decimal


class RecordFile:
    __records: list[Record]
    __record_file_key: RecordFileKey
    __account_data_directory: str

    __dirty: bool

    def __init__(
        self, record_file_key: RecordFileKey, account_data_directory: str
    ) -> None:
        # if the file does not exist, create a new one
        # otherwise, load the existing one

        self.__record_file_key = record_file_key
        self.__account_data_directory = account_data_directory
        self.__dirty = False

        if os.path.exists(self.get_record_file_path()):
            self.__records = self.__load_from_file(self.get_record_file_path())
        else:
            self.__records = []

        atexit.register(self.cleanup)

    @property
    def records(self) -> Sequence[Record]:
        return self.__records

    @staticmethod
    def __load_from_file(path: str) -> list[Record]:
        with open(path, "r") as file:
            try:
                json_data = json.load(file)
                records: list[Record] = []

                for record_json in json_data:
                    if "tag" in record_json:
                        tag = str(record_json["tag"])
                    else:
                        tag = None

                    balance = Decimal(record_json["balance"])
                    date = datetime.fromisoformat(record_json["date"])

                    if "note" in record_json:
                        note = str(record_json["note"])
                    else:
                        note = None

                    records.append(Record(tag, balance, date, note))

                # check if the date is still sorted
                for i in range(1, len(records)):
                    if records[i].date < records[i - 1].date:
                        raise CorruptedDataFileError()

                return records
            except Exception:
                raise CorruptedDataFileError()

    def get_record_file_path(self) -> str:
        return os.path.join(
            self.__account_data_directory,
            f"{self.__record_file_key.year_number}_{self.__record_file_key.month_number}.json",  # noqa: E501
        )

    def __save_to_file(self):
        with open(self.get_record_file_path(), "w") as file:
            records: list[Any] = []
            for record in self.__records:
                record_json = {
                    "balance": str(record.balance),
                    "date": record.date.isoformat(),
                }

                if record.tag is not None:
                    record_json["tag"] = record.tag

                if record.note is not None:
                    record_json["note"] = record.note

                records.append(record_json)

            json.dump(records, file)

    def cleanup(self):
        if self.__dirty:
            self.__save_to_file()
            self.__dirty = True

    def add_record(
        self, tag: Optional[str], balance: Decimal, note: Optional[str]
    ):
        self.__records.append(Record(tag, balance, datetime.now(), note))
        self.__dirty = True


class RecordIterator:
    __recrod_file_keys: list[RecordFileKey]
    __current_record_file_index: int
    __current_record_index: int
    __current_record_file: Optional[RecordFile]

    __account: Account

    def __init__(self, account: Account) -> None:
        self.__account = account
        self.__recrod_file_keys = account.record_file_keys

        self.__recrod_file_keys.sort(
            key=lambda x: (x.year_number, x.month_number)
        )

        self.__current_record_file = None
        self.__current_record_file_index = -1
        self.__current_record_index = -1

        for i, record_file in enumerate(reversed(self.__recrod_file_keys)):
            current_record_file = self.__account.get_record_file(record_file)

            if len(current_record_file.records) > 0:
                self.__current_record_file = current_record_file
                self.__current_record_file_index = (
                    len(self.__recrod_file_keys) - i - 1
                )
                self.__current_record_index = (
                    len(self.__current_record_file.records) - 1
                )
                break

    def __next_position(self) -> Optional[tuple[int, int]]:
        if self.__current_record_file is None:
            return None

        if self.__current_record_index > 0:
            return (
                self.__current_record_file_index,
                self.__current_record_index - 1,
            )
        else:
            for i in reversed(range(0, self.__current_record_file_index)):
                current_record_file = self.__account.get_record_file(
                    self.__recrod_file_keys[i]
                )

                if len(current_record_file.records) > 0:
                    self.__current_record_file = current_record_file
                    self.__current_record_file_index = (
                        len(self.__recrod_file_keys) - i - 1
                    )
                    self.__current_record_index = (
                        len(self.__current_record_file.records) - 1
                    )
                    break
            else:
                return None

    def forward(self) -> None:
        next_record = self.__next_position()

        if next_record is None:
            self.__current_record_file = None
            self.__current_record_file_index = -1
            self.__current_record_index = -1
            return

        self.__current_record_file = self.__account.get_record_file(
            self.__recrod_file_keys[next_record[0]]
        )
        self.__current_record_file_index = next_record[0]
        self.__current_record_index = next_record[1]

    def next(self) -> Optional[RecordDiff]:
        result = self.peek()
        self.forward()
        return result

    def __iter__(self) -> RecordIterator:
        return self

    def __next__(self) -> RecordDiff:
        result = self.next()

        if result is None:
            raise StopIteration()

        return result

    def peek(self) -> Optional[RecordDiff]:
        if self.__current_record_file is None:
            return None

        record = self.__current_record_file.records[
            self.__current_record_index
        ]

        match self.__next_position():
            case None:
                return RecordDiff(record, record.balance)
            case (next_record_file_index, next_record_index):
                if next_record_file_index == self.__current_record_file_index:
                    return RecordDiff(
                        record,
                        record.balance
                        - self.__current_record_file.records[
                            next_record_index
                        ].balance,
                    )
                else:
                    next_record_file = self.__account.get_record_file(
                        self.__recrod_file_keys[next_record_file_index]
                    )
                    return RecordDiff(
                        record,
                        record.balance
                        - next_record_file.records[next_record_index].balance,
                    )


class CorruptedRecordFileError(CorruptedDataFileError):
    """An exception raised when the preference file is invalid/corrupted"""

    pass


class Account:
    __account_data_directory: str

    __record_files_by_key: dict[RecordFileKey, RecordFile]
    __record_file_keys: list[RecordFileKey]

    def __init__(self, account_data_directory: str) -> None:
        self.__account_data_directory = account_data_directory
        self.__record_files_by_key = {}

        for record in self.__search_available_record_files():
            self.__record_files_by_key[record] = RecordFile(
                record, self.__account_data_directory
            )

        self.__record_file_keys = list(self.__record_files_by_key.keys())
        self.__record_file_keys.sort(
            key=lambda x: (x.year_number, x.month_number)
        )

    def __search_available_record_files(self) -> list[RecordFileKey]:
        # list all the .json file with YYYY_MM.json format
        # and return a list of RecordFileKey

        records: list[RecordFileKey] = []
        for file_name in os.listdir(self.__account_data_directory):
            if not (file_name.endswith(".json") or os.path.isfile(file_name)):
                continue
            file_name = file_name.removesuffix(".json")
            split = file_name.split("_")

            if len(split) != 2:
                continue

            # must not have leading zeros
            if len(split[0]) == 0 or len(split[1]) == 0:
                continue
            if split[0][0] == "0" or split[1][0] == "0":
                continue

            year_number: int = 0
            month_number: int = 0

            try:
                year_number = int(split[0])
                month_number = int(split[1])
            except Exception:
                continue

            try:
                datetime(year_number, month_number, 1)
            except Exception:
                continue

            records.append(RecordFileKey(month_number, year_number))

        return records

    @property
    def record_file_keys(self) -> list[RecordFileKey]:
        return list(self.__record_files_by_key.keys())

    @property
    def account_name(self) -> str:
        # returns the stem of the account data directory
        return os.path.basename(self.__account_data_directory)

    @property
    def last_modified(self) -> datetime:
        modified_time = os.path.getmtime(self.__account_data_directory)
        modified_date_time = datetime.fromtimestamp(modified_time)
        return modified_date_time

    @property
    def current_balance(self) -> Decimal:
        if len(self.__record_file_keys) == 0:
            return Decimal(0)
        else:
            record_file = self.__record_files_by_key[
                self.__record_file_keys[-1]
            ]

            if len(record_file.records):
                return record_file.records[-1].balance
            else:
                return Decimal(0)

    def get_record_file(self, key: RecordFileKey) -> RecordFile:
        if key not in self.__record_files_by_key:
            self.__record_files_by_key[key] = RecordFile(
                key, self.__account_data_directory
            )
            self.__record_file_keys.append(key)

        return self.__record_files_by_key[key]

    def add_record(
        self,
        tag: Optional[str],
        amount: Decimal,
        note: Optional[str],
    ):
        record_file_key = RecordFileKey(
            datetime.today().month, datetime.today().year
        )
        self.get_record_file(record_file_key).add_record(tag, amount, note)
