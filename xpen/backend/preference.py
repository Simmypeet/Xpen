from __future__ import annotations

import pickle
from dataclasses import dataclass
from enum import Enum
from typing import Optional


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


class CorruptedPreferenceFileError(Exception):
    """Raised when the preference file cannot be loaded due to corruption"""

    pass


@dataclass(frozen=True)
class Preference:
    """Represents the user preference of the application"""

    currency: Currency = Currency.THB
    font: str = "San Francisco"
    black_color: str = "#2d3436"
    light_red_color: str = "#fab1a0"
    light_gray_color: str = "#b2bec3"
    teal_white_color: str = "#dfe6e9"
    teal_green_color: str = "#55efc4"
    teal_red_color: str = "#ff7675"
    red_color: str = "#c0392b"
    green_color: str = "#27ae60"
    calm_green_color: str = "#1abc9c"
    header_size: int = 24
    sub_header_size: int = 18
    content_size: int = 14

    def prompt_button_style(self, color: str) -> str:
        return f"""
            font: {self.content_size}px;
            color: {self.black_color};
            padding: {self.content_size * 0.5}px;
            border-radius: {self.content_size * 0.25}px;
            border: 0px;
            background-color: {color};
        """

    @property
    def dialog_prompt_header_style(self) -> str:
        return f"""
            font: {self.sub_header_size}px;
            color: {self.black_color};
            font-weight: bold;
        """

    def dialog_line_edit_style(self, color: Optional[str] = None) -> str:
        return f"""
            font: {self.content_size}px;
            color: {self.black_color if color is None else color};
            border: 0px;
            padding: {self.content_size * 0.5}px;
        """

    @property
    def scroll_style_sheet(self) -> str:
        return """
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
            }"""

    @property
    def page_header_label_style(self) -> str:
        return f"""
        font: {self.header_size}px;
        color: {self.black_color};
        padding: {int(self.header_size * 0.75)} ;
        background-color: {self.teal_white_color};
        """

    def save(self, file_path: str) -> None:
        """
        Saves the preference to the file at the given path.
        """

        with open(file_path, "wb") as preference_file:
            pickle.dump(self, preference_file)

    @staticmethod
    def load_from_file(path: str) -> Preference:
        """
        Loads the preference from the file at the given path.

        :param path: The path to the preference file
        """

        with open(path, "rb") as preference_file:
            try:
                preference = pickle.load(preference_file)

                if not isinstance(preference, Preference):
                    raise CorruptedPreferenceFileError()

                return preference
            except Exception:
                raise CorruptedPreferenceFileError()
