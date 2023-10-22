from typing import Optional
from backend.account import Account
from backend.history import History
from backend.preference import Preference
from backend.resource import Resource
import os


class Backend:
    """
    Is the class containing all the data used by the application.
    """

    __preference: Preference
    __account_by_name: dict[str, Account]
    __resource: Resource
    __history: History
    __application_data_path: str
    __current_working_account: Optional[Account]

    def __init__(
        self,
        preference: Preference,
        resource: Resource,
        history: History,
        application_data_path: str,
    ) -> None:
        self.__preference = preference
        self.__resource = resource
        self.__history = history
        self.__account_by_name = {}
        self.__application_data_path = application_data_path
        self.__current_working_account = None

    @property
    def preference(self) -> Preference:
        return self.__preference

    @property
    def resource(self) -> Resource:
        return self.__resource

    @property
    def history(self) -> History:
        return self.__history

    @property
    def application_data_path(self) -> str:
        return self.__application_data_path

    @property
    def current_working_account(self) -> Optional[Account]:
        return self.__current_working_account

    @current_working_account.setter
    def current_working_account(self, account: Account) -> None:
        assert account in self.__account_by_name.values()

        self.__current_working_account = account

    def get_accounts(self) -> list[Account]:
        self.reload_accounts()

        return list(self.__account_by_name.values())

    def get_account_by_name(self, name: str) -> Account:
        self.reload_accounts()

        assert name in self.__account_by_name

        return self.__account_by_name[name]

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
                self.__account_by_name[account_folder] = Account(account_path)
