from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum

from backend.corrupted import CorruptedDataFileError


class Currency(Enum):
    """An enumeration of all supported currencies"""

    THB = (1,)
    USD = 2

    def currency_text(self) -> str:
        """
        Returns the currency text of the currency.

        :return: The currency text of the currency
        """

        if self == Currency.THB:
            return "THB"
        elif self == Currency.USD:
            return "USD"
        else:
            raise Exception("Unknown currency")


class CorruptedPreferenceFileError(CorruptedDataFileError):
    """An exception raised when the preference file is invalid/corrupted"""

    pass


@dataclass(frozen=True)
class Preference:
    """Represents the user preference of the application"""

    currency: Currency = Currency.THB
    font: str = "San Francisco"
    font_color: str = "#2d3436"
    page_text_background: str = "#fab1a0"
    account_line_separator: str = "#b2bec3"
    generic_background_1: str = "#dfe6e9"
    sidebar_background_1: str = "#55efc4"
    button_color_1: str = "#55efc4"
    button_color_2: str = "#ff7675"
    expense_color: str = "#c0392b"
    income_color: str = "#27ae60"
    scroll_style_sheet: str = """
        QScrollBar:vertical {
            border: none;
            background: #FFFFFF;
            width: 10px;
            margin: 0px 0px 0px 0px;
        }

        QScrollBar::handle:vertical {
            background: #D0D0D0;
            min-height: 20px;
            border-radius: 5px;
        }

        QScrollBar::add-line:vertical {
            border: none;
            background: none;
            height: 0px;
            subcontrol-position: bottom;
            subcontrol-origin: margin;
        }

        QScrollBar::sub-line:vertical {
            border: none;
            background: none;
            height: 0px;
            subcontrol-position: top;
            subcontrol-origin: margin;
        }

        QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
            background: none;
        }
    """

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
                "account_line_separator": self.account_line_separator,
                "text_background_2": self.page_text_background,
                "generic_background_1": self.generic_background_1,
                "sidebar_background_1": self.sidebar_background_1,
                "button_color_1": self.button_color_1,
                "button_color_2": self.button_color_2,
                "expense_color": self.expense_color,
                "income_color": self.income_color,
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
            try:
                currency_json = preference_json["currency"]
                currency = None

                if currency_json == "THB":
                    currency = Currency.THB
                elif currency_json == "USD":
                    currency = Currency.USD
                else:
                    raise CorruptedPreferenceFileError()

                font = str(preference_json["font"])
                font_color = str(preference_json["font_color"])
                page_text_background = str(
                    preference_json["page_text_background"]
                )
                account_line_separator = str(
                    preference_json["account_line_separator"]
                )
                generic_background_1 = str(
                    preference_json["generic_background_1"]
                )
                sidebar_background_1 = str(
                    preference_json["sidebar_background_1"]
                )
                button_color_1 = str(preference_json["button_color_1"])
                button_color_2 = str(preference_json["button_color_2"])
                expense_color = str(preference_json["expense_color"])
                income_color = str(preference_json["income_color"])

                return Preference(
                    currency,
                    font,
                    font_color,
                    page_text_background,
                    account_line_separator,
                    generic_background_1,
                    sidebar_background_1,
                    button_color_1,
                    button_color_2,
                    expense_color,
                    income_color,
                )
            except Exception:
                raise CorruptedPreferenceFileError()
