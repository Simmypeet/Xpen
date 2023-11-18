from __future__ import annotations

import atexit
import os
import pickle
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional, Sequence

from backend.observer import Subject, Observer


@dataclass(frozen=True)
class Record:
    """Represents a single record entry in the account"""

    tag: Optional[str]
    """The tag of the record"""
    balance: Decimal
    """The current balance of the account"""
    date: datetime
    """The date time when the record was created"""
    note: Optional[str]
    """Optional note for the record"""


@dataclass(frozen=True)
class RecordFileKey:
    """Represents a key used to identify/locate a record file"""

    month_number: int
    """The month number of the record file (1-12)"""
    year_number: int
    """The year number of the record file"""

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
    """Contains the record and the difference from the previous record"""

    record: Record
    """The record"""
    diff: Decimal
    """The difference from the previous record""" ""


class RecordFile:
    """
    A collection of records created within a month.
    """

    __records: list[Record]
    __record_file_key: RecordFileKey
    __parent_account: Account

    __dirty: bool

    def __init__(
        self, record_file_key: RecordFileKey, parent_account: Account
    ) -> None:
        """Creates a new record file object.

        Args:
            record_file_key (RecordFileKey): The key of the record file.
                Contains the month and year number.
            parent_account (Account): The account that owns this record file.
        """
        # if the file does not exist, create a new one
        # otherwise, load the existing one

        self.__record_file_key = record_file_key
        self.__parent_account = parent_account
        self.__dirty = False

        if os.path.exists(self.get_record_file_path()):
            self.__records = self.__load_from_file(self.get_record_file_path())
        else:
            self.__records = []

        atexit.register(self.cleanup)

    @property
    def records(self) -> Sequence[Record]:
        return self.__records

    def make_dirty(self) -> None:
        self.__dirty = True

    @staticmethod
    def __load_from_file(path: str) -> list[Record]:
        with open(path, "rb") as file:
            try:
                records = pickle.load(file)
                return records
            except Exception:
                raise CorruptedRecordFileError()

    def get_record_file_path(self) -> str:
        return os.path.join(
            self.__parent_account.account_data_directory,
            f"{self.__record_file_key.year_number}_{self.__record_file_key.month_number}.dat",  # noqa: E501
        )

    def __save_to_file(self) -> None:
        with open(self.get_record_file_path(), "wb") as file:
            pickle.dump(self.__records, file)

    def cleanup(self) -> None:
        if self.__dirty:
            self.__save_to_file()
            self.__dirty = True

    def add_record(
        self, tag: Optional[str], balance: Decimal, note: Optional[str]
    ) -> Record:
        new_record = Record(tag, balance, datetime.now(), note)
        self.__records.append(new_record)
        self.__dirty = True

        return new_record


class OldestPosition:
    """Used to signify the oldest position/record in the account"""

    pass


class LatestPosition:
    """Used to signify the latest position/record in the account"""

    pass


@dataclass
class _ValidPosition:
    record_file_index: int
    record_index: int


_RecordPosition = OldestPosition | LatestPosition | _ValidPosition


class InvalidatedRecordCursorError(Exception):
    """
    The account has made modifications since the cursor was created hence
    the cursor is no longer valid.
    """

    pass


class RecordCursor(Observer):
    """Represents a cursor scanning through the records in an account."""

    __account: Account

    __record_file_keys: list[RecordFileKey]
    __record_position: _RecordPosition
    __valid: bool

    def _response(self, message: object) -> None:
        match message:
            case NewRecordMessage(_):
                self.__valid = False
            case _:
                pass

    def __init__(
        self,
        account: Account,
        position: OldestPosition | LatestPosition | Record,
    ):
        """Creates a new record cursor object.

        Args:
            account (Account): The account that cursor will read from
            position (OldestPosition | LatestPosition | Record): The position
                where the cursor will start
        """
        self.__valid = True
        self.__account = account
        self.__record_file_keys = account.record_file_keys

        match position:
            case Record() as record:
                record_file_key = RecordFileKey(
                    record.date.month, record.date.year
                )
                record_file = account.get_record_file_or_default(
                    record_file_key
                )
                record_index = record_file.records.index(record)

                assert record_index != -1

                self.__record_position = _ValidPosition(
                    self.__record_file_keys.index(record_file_key),
                    record_index,
                )

            case OldestPosition():
                self.__record_position = self.__next_position(OldestPosition())

            case LatestPosition():
                self.__record_position = self.__previous_position(
                    LatestPosition()
                )

    def previous(self) -> Optional[RecordDiff]:
        """
        Reads the record at the current position and moves the cursor to
        the previous position (less recent).

        Raises:
            InvalidatedRecordCursorError: If the cursor is no longer valid

        Returns:
            Optional[RecordDiff]: The record at the current position or None if
                the cursor is at the beginning of the account.
        """
        result = self.peek()
        self.__record_position = self.__previous_position(
            self.__record_position
        )
        return result

    def next(self) -> Optional[RecordDiff]:
        """
        Reads the record at the current position and moves the cursor to
        the next position (more recent).

        Raises:
            InvalidatedRecordCursorError: If the cursor is no longer valid

        Returns:
            Optional[RecordDiff]: The record at the current position or None if
                the cursor is at the end of the account.
        """
        result = self.peek()
        self.__record_position = self.__next_position(self.__record_position)
        return result

    def peek(self) -> Optional[RecordDiff]:
        """Reads the record at the current position without moving the cursor.

        Raises:
            InvalidatedRecordCursorError: If the cursor is no longer valid

        Returns:
            Optional[RecordDiff]: The record at the current position or None if
                the cursor is at the end of the account.
        """
        if not self.__valid:
            raise InvalidatedRecordCursorError()

        previous_position = self.__previous_position(self.__record_position)

        match (self.__record_position, previous_position):
            case (_ValidPosition() as valid, previous_position):
                record = self.__get_record_from_position(valid)
                current_balance = record.balance
                previous_balance = self.__get_balance_from_position(
                    previous_position
                )

                return RecordDiff(record, current_balance - previous_balance)
            case _:
                return None

    def __get_record_from_position(
        self, valid_position: _ValidPosition
    ) -> Record:
        record_file = self.__account.get_record_file_or_default(
            self.__record_file_keys[valid_position.record_file_index]
        )
        return record_file.records[valid_position.record_index]

    def __get_balance_from_position(
        self, position: _RecordPosition
    ) -> Decimal:
        match position:
            case OldestPosition():
                return Decimal(0)
            case LatestPosition():
                return Decimal(0)
            case _ValidPosition() as valid_position:
                record_file = self.__account.get_record_file_or_default(
                    self.__record_file_keys[valid_position.record_file_index]
                )
                return record_file.records[valid_position.record_index].balance

    def __previous_position(
        self, position: _RecordPosition
    ) -> _RecordPosition:
        match position:
            case OldestPosition():
                return OldestPosition()

            case LatestPosition():
                for i in range(len(self.__record_file_keys) - 1, -1, -1):
                    record_file = self.__account.get_record_file_or_default(
                        self.__record_file_keys[i]
                    )

                    if len(record_file.records) > 0:
                        return _ValidPosition(
                            i,
                            len(record_file.records) - 1,
                        )

                return OldestPosition()

            case _ValidPosition() as valid_position:
                if valid_position.record_index > 0:
                    return _ValidPosition(
                        valid_position.record_file_index,
                        valid_position.record_index - 1,
                    )
                else:
                    for i in range(
                        valid_position.record_file_index - 1, -1, -1
                    ):
                        record_file = (
                            self.__account.get_record_file_or_default(
                                self.__record_file_keys[i]
                            )
                        )

                        if len(record_file.records) > 0:
                            return _ValidPosition(
                                i,
                                len(record_file.records) - 1,
                            )

                    return OldestPosition()

    def __next_position(self, position: _RecordPosition) -> _RecordPosition:
        """
        Gets the next position one more *recent* than the current position
        """
        match position:
            case OldestPosition():
                for record_file_key in self.__record_file_keys:
                    record_file = self.__account.get_record_file_or_default(
                        record_file_key
                    )

                    if len(record_file.records) > 0:
                        return _ValidPosition(
                            self.__record_file_keys.index(record_file_key),
                            0,
                        )

                return LatestPosition()

            case LatestPosition():
                return LatestPosition()

            case _ValidPosition() as valid_position:
                record_file = self.__account.get_record_file_or_default(
                    self.__record_file_keys[valid_position.record_file_index]
                )

                if valid_position.record_index + 1 < len(record_file.records):
                    return _ValidPosition(
                        valid_position.record_file_index,
                        valid_position.record_index + 1,
                    )
                else:
                    for i in range(
                        valid_position.record_file_index + 1,
                        len(self.__record_file_keys),
                    ):
                        record_file = (
                            self.__account.get_record_file_or_default(
                                self.__record_file_keys[i]
                            )
                        )

                        if len(record_file.records) > 0:
                            return _ValidPosition(
                                i,
                                0,
                            )

                    return LatestPosition()


class CorruptedRecordFileError(Exception):
    """An exception raised when the preference file is invalid/corrupted"""

    pass


class InvalidAccountDataPathError(Exception):
    """The given account data path does not exist or is not a directory"""

    pass


@dataclass(frozen=True)
class NewRecordMessage:
    """A message sent when a new record is added to the account."""

    record: Record


class Account(Subject):
    """A class representing an account."""

    __data_directory: str

    __record_files_by_key: dict[RecordFileKey, RecordFile]
    __record_file_keys: list[RecordFileKey]

    def __init__(
        self,
        account_data_directory: str,
    ) -> None:
        """Creates a new account object.

        Args:
            account_data_directory (str): The path to the account data folder
                where all the records are stored in.

        Raises:
            InvalidAccountDataPathError: If the given path does not exist or
                is not a directory.
        """
        super().__init__()

        if not os.path.isdir(account_data_directory):
            raise InvalidAccountDataPathError()

        self.__data_directory = account_data_directory
        self.__record_files_by_key = {}

        for record in self.__search_available_record_files():
            self.__record_files_by_key[record] = RecordFile(record, self)

        self.__record_file_keys = list(self.__record_files_by_key.keys())
        self.__record_file_keys.sort(
            key=lambda x: (x.year_number, x.month_number)
        )

    @property
    def account_data_directory(self) -> str:
        """Gets the account data directory.

        Returns:
            str: The account data directory.
        """
        return self.__data_directory

    def __rename(self, new_name: str) -> None:  # type:ignore
        parent_directory = os.path.dirname(self.__data_directory)
        new_directory = os.path.join(parent_directory, new_name)

        os.rename(self.__data_directory, new_directory)

        self.__data_directory = new_directory

        for record in self.__record_files_by_key.values():
            record.make_dirty()

    def __search_available_record_files(self) -> list[RecordFileKey]:
        # list all the .dat file with YYYY_MM.dat format
        # and return a list of RecordFileKey

        records: list[RecordFileKey] = []
        for file_name in os.listdir(self.__data_directory):
            if not (file_name.endswith(".dat") or os.path.isfile(file_name)):
                continue
            file_name = file_name.removesuffix(".dat")
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
        """
        Gets the record file keys in ascending order i.e. oldest to latest
        """

        return list(self.__record_files_by_key.keys())

    @property
    def name(self) -> str:
        """Gets the name of the account."""
        # returns the stem of the account data directory
        return os.path.basename(self.__data_directory)

    @property
    def last_modified(self) -> datetime:
        """
        Gets the last modified time of the account data directory based on
        the os's last modified time.
        """
        modified_time = os.path.getmtime(self.__data_directory)
        modified_date_time = datetime.fromtimestamp(modified_time)
        return modified_date_time

    @property
    def current_balance(self) -> Decimal:
        """Gets the current balance of the account."""
        cursor = RecordCursor(self, LatestPosition())
        record = cursor.peek()

        if record is not None:
            return record.record.balance
        else:
            return Decimal(0)

    def get_record_file_or_default(self, key: RecordFileKey) -> RecordFile:
        """Gets the record file with the given key. If the record file does not
        exist, a new empty record file will be created.

        Args:
            key (RecordFileKey): The key of the record file.

        Returns:
            RecordFile: The record file with the given key.
        """
        if key not in self.__record_files_by_key:
            self.__record_files_by_key[key] = RecordFile(key, self)
            self.__record_file_keys.append(key)

        return self.__record_files_by_key[key]

    def add_record(
        self,
        tag: Optional[str],
        amount: Decimal,
        note: Optional[str],
    ) -> Record:
        """Adds a new record to the account.

        Args:
            tag (Optional[str]): The tag of the record.
            amount (Decimal): The *difference* amount from the previous record.
            note (Optional[str]): The note of the record.

        Returns:
            Record: The record that was added.
        """
        record_file_key = RecordFileKey(
            datetime.today().month, datetime.today().year
        )
        new_record = self.get_record_file_or_default(
            record_file_key
        ).add_record(tag, amount, note)
        self._notify(NewRecordMessage(new_record))
        return new_record
