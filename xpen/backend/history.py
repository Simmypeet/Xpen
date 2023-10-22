from __future__ import annotations
from dataclasses import dataclass
import json

from backend.corrupted import CorruptedDataFileError


class CorruptedHistoryFileError(CorruptedDataFileError):
    """An exception raised when the preference file is invalid/corrupted"""

    pass


@dataclass
class History:
    """
    A class collecting all the interaction history of the application.
    """

    last_accessed_account_name: str
    """
    The name of the last accessed account.
    """

    def load_from_file(self, file_path: str) -> History:
        """
        Loads the history from the file at the given path.

        :param path: The path to the history file
        """

        with open(file_path) as history_file:
            history_json = json.load(history_file)

            try:
                last_accessed_account_name = str(
                    history_json["last_accessed_account_name"]
                )

                return History(last_accessed_account_name)
            except Exception:
                raise CorruptedHistoryFileError()
