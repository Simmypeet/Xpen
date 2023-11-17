from __future__ import annotations

import os
from dataclasses import dataclass

from PySide6.QtSvg import QSvgRenderer


@dataclass(frozen=True)
class Resource:
    """
    Contains all the graphical resources used by the application.
    """

    account_bar_icon: QSvgRenderer
    record_bar_icon: QSvgRenderer
    calendar_bar_icon: QSvgRenderer
    account_not_found_symol: QSvgRenderer
    new_account_symbol: QSvgRenderer
    filter_symbol: QSvgRenderer

    @staticmethod
    def load_from_resource_folder(resource_folder: str) -> Resource:
        """Loads the resource from the given resource folder.

        Args:
            resource_folder (str): The path to the resource folder.

        Returns:
            Resource: The resource object.
        """
        account_bar_icon = QSvgRenderer(
            os.path.join(resource_folder, "icon", "account_bar_icon.svg")
        )
        record_bar_icon = QSvgRenderer(
            os.path.join(resource_folder, "icon", "record_bar_icon.svg")
        )
        calendar_bar_icon = QSvgRenderer(
            os.path.join(resource_folder, "icon", "calendar_bar_icon.svg")
        )
        account_not_found_symbol = QSvgRenderer(
            os.path.join(
                resource_folder, "symbol", "account_not_found_symbol.svg"
            )
        )
        new_account_symbol = QSvgRenderer(
            os.path.join(resource_folder, "symbol", "new_account_symbol.svg")
        )
        filter_symbol = QSvgRenderer(
            os.path.join(resource_folder, "symbol", "filter_symbol.svg")
        )

        return Resource(
            account_bar_icon,
            record_bar_icon,
            calendar_bar_icon,
            account_not_found_symbol,
            new_account_symbol,
            filter_symbol,
        )
