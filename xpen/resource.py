from __future__ import annotations

import os
from dataclasses import dataclass

from PySide6.QtSvg import QSvgRenderer


@dataclass(frozen=True)
class Resource:
    account_bar_icon: QSvgRenderer
    record_bar_icon: QSvgRenderer
    calendar_bar_icon: QSvgRenderer
    chart_bar_icon: QSvgRenderer
    setting_bar_icon: QSvgRenderer

    account_not_found_symol: QSvgRenderer
    new_account_symbol: QSvgRenderer

    @staticmethod
    def load_from_resource_folder(resource_folder: str) -> Resource:
        account_bar_icon = QSvgRenderer(
            os.path.join(resource_folder, "icon", "account_bar_icon.svg")
        )
        record_bar_icon = QSvgRenderer(
            os.path.join(resource_folder, "icon", "record_bar_icon.svg")
        )
        calendar_bar_icon = QSvgRenderer(
            os.path.join(resource_folder, "icon", "calendar_bar_icon.svg")
        )
        chart_bar_icon = QSvgRenderer(
            os.path.join(resource_folder, "icon", "chart_bar_icon.svg")
        )
        setting_bar_icon = QSvgRenderer(
            os.path.join(resource_folder, "icon", "setting_bar_icon.svg")
        )
        account_not_found_symbol = QSvgRenderer(
            os.path.join(resource_folder, "symbol", "account_not_found_symbol.svg")
        )
        new_account_symbol = QSvgRenderer(
            os.path.join(resource_folder, "symbol", "new_account_symbol.svg")
        )

        return Resource(
            account_bar_icon,
            record_bar_icon,
            calendar_bar_icon,
            chart_bar_icon,
            setting_bar_icon,
            account_not_found_symbol,
            new_account_symbol,
        )
