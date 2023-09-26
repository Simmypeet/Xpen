from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
import json


class Currency(Enum):
    """An enumeration of all supported currencies"""

    THB = (1,)
    USD = 2


class InvalidPreferenceFileError(Exception):
    """An exception raised when the preference file is invalid"""

    pass


@dataclass(frozen=True)
class Preference:
    """Represents the user preference of the application"""

    currency: Currency = Currency.THB
    """The currency used in the application"""

    font: str = "San Francisco"
    """The font used in the application"""

    font_color: str = "#2c3e50"

    page_text_background: str = "#bdc3c7"

    page_text_bottom_border: str = "#95a5a6"

    generic_background_1: str = "#ecf0f1"
    """1st variant of the generic background color used in the application"""

    sidebar_background_1: str = "#2ecc71"

    button_color_1: str = "#9b59b6"

    def save(self, file_path: str):
        """
        Saves the preference to the file at the given path.
        """

        with open(file_path, "w") as preference_file:
            preference_json = {
                "currency": self.currency.name,
                "font": self.font,
                "font_color": self.font_color,
                "page_text_background": self.page_text_background,
                "page_text_bottom_border": self.page_text_bottom_border,
                "text_background_2": self.page_text_background,
                "generic_background_1": self.generic_background_1,
                "sidebar_background_1": self.sidebar_background_1,
                "button_color_1": self.button_color_1,
            }

            json.dump(preference_json, preference_file)

    @staticmethod
    def load_from_file(path: str) -> Preference:
        """
        Loads the preference from the file at the given path.

        The accepted format is JSON.

        :param path: The path to the preference file
        """

        with open(path) as preference_file:
            preference_json = json.load(preference_file)

            # reads the currency
            currency_json = preference_json["currency"]
            currency = None

            if currency_json == "THB":
                currency = Currency.THB
            elif currency_json == "USD":
                currency = Currency.USD
            else:
                raise InvalidPreferenceFileError()

            # reads the font
            font = str(preference_json["font"])

            # reads the font color
            font_color = str(preference_json["font_color"])

            # reads the text background color
            page_text_background = str(preference_json["page_text_background"])

            # reads the text background color
            page_text_bottom_border = str(preference_json["page_text_bottom_border"])

            # reads the generic background color
            generic_background_1 = str(preference_json["generic_background_1"])

            # reads the sidebar background color
            sidebar_background_1 = str(preference_json["sidebar_background_1"])

            button_color_1 = str(preference_json["button_color_1"])

            return Preference(
                currency,
                font,
                font_color,
                page_text_background,
                page_text_bottom_border,
                generic_background_1,
                sidebar_background_1,
                button_color_1,
            )
