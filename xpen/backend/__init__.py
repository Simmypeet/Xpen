from __future__ import annotations

from dataclasses import dataclass
import os
from shutil import rmtree
from typing import Optional

from backend.account import Account
from backend.preference import Preference
from backend.resource import Resource


@dataclass
class InvalidAccountError(Exception):
    """The account provided is invalid for this backend"""

    pass


@dataclass
class AccountRenameConflictError(Exception):
    """The account with the given name allready exists"""

    pass


@dataclass
class InvalidApplicationDataPathError(Exception):
    """The given application data path does not exist or is not a directory"""

    pass


class Backend:
    """
    Contains all the backend logic for the application.
    """

    __preference: Preference
    __account_by_name: dict[str, Account]
    __resource: Resource
    __application_data_path: str
    __current_working_account: Optional[Account]

    def __init__(
        self,
        preference: Preference,
        resource: Resource,
        application_data_path: str,
    ) -> None:
        """Creates a new backend object.

        Args:
            preference (Preference): the preference of the user.
            resource (Resource): the resource object.
            application_data_path (str): the path to the application data
                folder where all the accounts are stored in.

        Raises:
            InvalidApplicationDataPathError: The given application data path
                does not exist or is not a directory
        """
        if not os.path.isdir(application_data_path):
            raise InvalidApplicationDataPathError()

        self.__preference = preference
        self.__resource = resource
        self.__account_by_name = {}
        self.__application_data_path = application_data_path
        self.__current_working_account = None

    @property
    def preference(self) -> Preference:
        """Gets the user preference configuration.

        Returns:
            Preference: The user preference configuration.
        """
        return self.__preference

    @property
    def resource(self) -> Resource:
        """Gets ther resource object.

        Returns:
            Resource: The resource object.
        """
        return self.__resource

    @property
    def application_data_path(self) -> str:
        """Gets the path to the application data folder.

        Returns:
            str: Path to the application data folder.
        """
        return self.__application_data_path

    @property
    def current_working_account(self) -> Optional[Account]:
        """Gets the current working account (if any)

        Returns:
            Optional[Account]: The current working account or None
        """
        return self.__current_working_account

    @current_working_account.setter
    def current_working_account(self, account: Account) -> None:
        """Changes the current working account.

        Args:
            account (Account): the account to change to.

        Raises:
            InvalidAccountError: The account is invalid for this backend.
        """
        if account not in self.__account_by_name.values():
            raise InvalidAccountError()

        self.__current_working_account = account

    def get_accounts(self) -> list[Account]:
        """Gets all the accounts found in the application data folder.

        Returns:
            list[Account]: A list of all the accounts found in the application
        """
        self.reload_accounts()

        return list(self.__account_by_name.values())

    def get_account_by_name(self, name: str) -> Account | None:
        """Gets the account with the given name

        Args:
            name (str): The name of the account to get.

        Returns:
            Account | None: Returns the account with the given name or None
        """
        self.reload_accounts()

        return self.__account_by_name.get(name, None)

    def rename_account(self, account: Account, new_account_name: str) -> None:
        """Preforms a rename of the given account.

        This as well rename the account folder in the application data folder.

        Args:
            account (Account): The account to rename.
            new_account_name (str): The new name given to the account.

        Raises:
            InvalidAccountError: The account is invalid for this backend.

            AccountRenameConflictError: The account with the given name
                already exists.
        """

        if account not in self.__account_by_name.values():
            raise InvalidAccountError()

        if new_account_name in self.__account_by_name:
            raise AccountRenameConflictError()

        del self.__account_by_name[account.name]

        self.__account_by_name[new_account_name] = account

        account._Account__rename(new_account_name)  # type: ignore

    def delete_account(self, account: Account) -> None:
        """Removes the given account from the backend.

        Args:
            account (Account): The account to remove.

        Raises:
            InvalidAccountError: The account is invalid for this backend.
        """
        self.reload_accounts()

        if account not in self.__account_by_name.values():
            raise InvalidAccountError()

        del self.__account_by_name[account.name]

        # delete the account data directory
        account_data_path = os.path.join(
            self.__application_data_path, account.name
        )
        # recrusively delete the directory
        rmtree(account_data_path)

    def reload_accounts(self) -> None:
        """
        Performs a search for all the accounts in the application data folder
        and adds them to the backend.
        """

        account_data_path = os.path.join(self.__application_data_path)

        for account_folder in os.listdir(account_data_path):
            account_path = os.path.join(account_data_path, account_folder)
            if not os.path.isdir(account_path):
                continue

            if account_folder not in self.__account_by_name:
                new_account = Account(account_path)
                self.__account_by_name[account_folder] = new_account
