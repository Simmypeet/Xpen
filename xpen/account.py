import atexit
import json
import os
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any


@dataclass
class Record:
    tag: str | None
    balance: Decimal
    date: datetime
    note: str | None


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


class RecordFile(object):
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

    @staticmethod
    def __load_from_file(path: str) -> list[Record]:
        file = open(path, "r")

        json_data = json.load(file)
        records: list[Record] = []

        for record_json in json_data:
            tag = str(record_json["tag"])
            balance = Decimal(record_json["balance"])
            date = record_json["date"]
            note = str(record_json["note"])

            records.append(Record(tag, balance, date, note))

        # sort the records by date time
        records.sort(key=lambda x: x.date)

        return records

    def get_record_file_path(self) -> str:
        return os.path.join(
            self.__account_data_directory,
            f"{self.__record_file_key.year_number}_{self.__record_file_key.month_number}.json",
        )

    def __save_to_file(self):
        with open(self.get_record_file_path(), "w") as file:
            records: list[Any] = []
            for record in self.__records:
                record_json = {
                    "tag": record.tag,
                    "balance": str(record.balance),
                    "date": record.date.isoformat(),
                    "note": record.note,
                }
                records.append(record_json)

            json.dump(records, file)

    def cleanup(self):
        if self.__dirty:
            self.__save_to_file()
            self.__dirty = True

    def add_record(
        self,
        tag: str | None,
        balance: Decimal,
        note: str | None,
    ):
        self.__records.append(Record(tag, balance, datetime.now(), note))
        self.__dirty = True


class Account:
    __account_data_directory: str

    __record_files_by_key: dict[RecordFileKey, RecordFile]

    def __init__(self, account_data_directory: str) -> None:
        self.__account_data_directory = account_data_directory
        self.__record_files_by_key = {}

        for record in self.__search_available_record_files():
            self.__record_files_by_key[record] = RecordFile(
                record, self.__account_data_directory
            )

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

    def get_account_name(self) -> str:
        # returns the stem of the account data directory
        return os.path.basename(self.__account_data_directory)

    def get_last_modified(self) -> datetime:
        modified_time = os.path.getmtime(self.__account_data_directory)
        modified_date_time = datetime.fromtimestamp(modified_time)
        return modified_date_time

    def get_current_balance(self) -> int:
        return 69420

    def get_record_file(self, key: RecordFileKey) -> RecordFile:
        if key not in self.__record_files_by_key:
            self.__record_files_by_key[key] = RecordFile(
                key, self.__account_data_directory
            )

        return self.__record_files_by_key[key]

    def add_record(
        self,
        tag: str | None,
        amount: Decimal,
        note: str | None,
    ):
        record_file_key = RecordFileKey(datetime.today().month, datetime.today().year)
        self.get_record_file(record_file_key).add_record(tag, amount, note)
