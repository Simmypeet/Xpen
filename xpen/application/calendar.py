from __future__ import annotations

import calendar
from datetime import datetime, date
from typing import Callable, Final, Optional

from application.auxiliary import Page
from application.message import Date, ToCalendarPage, ToRecordPage
from application.filter import Filter
from application.widget import Widget
from backend import Backend
from backend.account import RecordCursor, RecordFileKey
from backend.observer import Observer, Subject
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)
from PySide6.QtGui import QMouseEvent


class _DatePicker(Widget, Subject):
    __main_widget: QWidget
    __hbox_layout: QHBoxLayout

    MONTH: Final[list[str]] = [
        "January",
        "February",
        "March",
        "April",
        "May",
        "June",
        "July",
        "August",
        "September",
        "October",
        "November",
        "December",
    ]

    __current_month: int
    __current_year: int

    __month_selector: QComboBox
    __year_label: QLabel

    @property
    def current_month(self) -> int:
        return self.__current_month

    @property
    def current_year(self) -> int:
        return self.__current_year

    def __init__(self, backend: Backend, default_date: Optional[Date]):
        super().__init__()

        if default_date is not None:
            self.__current_month = default_date.month
            self.__current_year = default_date.year
        else:
            current_datetime = datetime.now()

            self.__current_month = current_datetime.month
            self.__current_year = current_datetime.year

        self.__hbox_layout = QHBoxLayout()
        self.__hbox_layout.setSpacing(0)
        self.__hbox_layout.setContentsMargins(0, 0, 0, 0)
        self.__hbox_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.__main_widget = QWidget()
        self.__main_widget.setLayout(self.__hbox_layout)
        self.__main_widget.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        self.__main_widget.setStyleSheet(
            f"""
            background-color: #ecf0f1;
            border-radius: {backend.preference.content_size * 0.25}px;
            """
        )

        self.__month_selector = QComboBox()
        self.__month_selector.setMinimumContentsLength(10)
        self.__month_selector.setSizeAdjustPolicy(
            QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon
        )
        self.__month_selector.addItems(self.MONTH)
        self.__month_selector.setCurrentIndex(self.__current_month - 1)
        self.__month_selector.view().setTextElideMode(
            Qt.TextElideMode.ElideNone
        )
        self.__month_selector.currentIndexChanged.connect(
            lambda index: self._notify(  # type: ignore
                ToCalendarPage(
                    Date(index + 1, self.__current_year),  # type: ignore
                )
            )
        )
        self.__month_selector.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        # disable the down arrow
        self.__month_selector.setStyleSheet(
            f"""
            QComboBox {{
                font: {backend.preference.sub_header_size}px;
                color: {backend.preference.black_color};
                font-weight: bold;
                border: none;
            }}

            QComboBox::down-arrow {{
                image: none;
            }}

            QComboBox::drop-down {{
                width: 0px;
                border: none;
            }}

            QComboBox QAbstractItemView {{
                border: none;
                outline: none;
                background-color: #FFFFFF;
            }}
            """
        )

        self.__year_label = QLabel(str(self.__current_year))
        self.__year_label.setStyleSheet(
            f"""
            font: {backend.preference.sub_header_size}px;
            color: {backend.preference.black_color};
            font-weight: bold;
            """
        )

        self.__hbox_layout.addWidget(
            self.__month_selector, alignment=Qt.AlignmentFlag.AlignLeft
        )
        self.__hbox_layout.addWidget(
            self.__year_label,
            alignment=Qt.AlignmentFlag.AlignRight,
        )

    @property
    def widget(self) -> QWidget:
        return self.__main_widget


class _Content(Widget, Observer, Subject):
    __main_widget: QWidget
    __grid_layout: QGridLayout
    __date_picker: _DatePicker
    __backend: Backend

    __date_frames: list[QWidget]

    def __init__(self, backend: Backend, default_date: Optional[Date]) -> None:
        super().__init__()

        self.__backend = backend
        self.__grid_layout = QGridLayout()
        self.__grid_layout.setContentsMargins(0, 0, 0, 0)
        self.__grid_layout.setSpacing(0)

        self.__main_widget = QWidget()
        self.__main_widget.setLayout(self.__grid_layout)
        self.__main_widget.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        margin = backend.preference.content_size
        self.__main_widget.setContentsMargins(margin, margin, margin, margin)

        self.__date_picker = _DatePicker(backend, default_date)
        self.subscribe(self.__date_picker)

        self.__grid_layout.addWidget(self.__date_picker.widget, 0, 0, 1, 7)
        self.__grid_layout.setRowStretch(0, 2)

        WEEKDAYS = [
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
            "Saturday",
            "Sunday",
        ]

        self.__grid_layout.setRowStretch(1, 1)
        for i, day in enumerate(WEEKDAYS):
            label = QLabel(day)
            label.setStyleSheet(
                f"""
                font: {backend.preference.content_size}px;
                color: {backend.preference.black_color};
                font-weight: bold;
                border-bottom: 1px solid {backend.preference.black_color};
                margin-left: {backend.preference.content_size * 0.5}px;
                margin-right: {backend.preference.content_size * 0.5}px;
                """
            )
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.__grid_layout.addWidget(label, 1, i)

        self.__create_grid_layout_for(
            self.__date_picker.current_month, self.__date_picker.current_year
        )

    def _response(self, message: object) -> None:
        self._notify(message)

    # month starts from 0
    def __create_grid_layout_for(self, month: int, year: int) -> None:
        assert self.__backend.current_working_account is not None

        start_at, number_of_days = calendar.monthrange(year, month)

        current_day = 1 - start_at

        self.__backend.current_working_account.record_file_keys
        record_file = (
            self.__backend.current_working_account.get_record_file_or_default(
                RecordFileKey(month, year)
            )
        )

        if len(record_file.records) > 0:
            cursor = RecordCursor(
                self.__backend.current_working_account, record_file.records[0]
            )
        else:
            cursor = None

        for row in range(0, 6):
            self.__grid_layout.setRowStretch(row + 2, 3)
            for column in range(0, 7):
                if current_day <= 0 or current_day > number_of_days:
                    current_day += 1
                    continue

                day_diff = 0
                if cursor is not None:
                    while True:
                        current = cursor.peek()

                        if current is None:
                            break

                        if (
                            current.record.date.day != current_day
                            or current.record.date.month != month
                            or current.record.date.year != year
                        ):
                            break

                        day_diff += current.diff
                        cursor.next()

                frame = QWidget()
                frame.setSizePolicy(
                    QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
                )
                frame.setContentsMargins(8, 8, 8, 8)

                vbox_layout = QVBoxLayout()
                vbox_layout.setContentsMargins(0, 0, 0, 0)
                vbox_layout.setSpacing(0)
                vbox_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

                day_label = QLabel(str(current_day))
                day_label.setStyleSheet(
                    f"""
                    font: {self.__backend.preference.sub_header_size}px;
                    color: {self.__backend.preference.black_color};
                    font-weight: bold;
                    """
                )
                day_label.setAlignment(
                    Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight
                )
                vbox_layout.addWidget(day_label)

                if day_diff != 0:
                    diff_label = QLabel(
                        f"+{day_diff}" if day_diff > 0 else f"-{-day_diff}"
                    )
                    color = (
                        self.__backend.preference.green_color
                        if day_diff > 0
                        else self.__backend.preference.red_color
                    )
                    diff_label.setStyleSheet(
                        f"""
                        font: {self.__backend.preference.sub_header_size}px;
                        color: {color};
                        """
                    )
                    diff_label.setAlignment(
                        Qt.AlignmentFlag.AlignBottom
                        | Qt.AlignmentFlag.AlignRight
                    )
                    diff_label.setSizePolicy(
                        QSizePolicy.Policy.Expanding,
                        QSizePolicy.Policy.Expanding,
                    )
                    vbox_layout.addWidget(diff_label)
                    frame.mousePressEvent = self.__to_record_page(
                        current_day
                    )  # type:ignore

                frame.setLayout(vbox_layout)

                self.__grid_layout.addWidget(frame, row + 2, column)

                current_day += 1

    def __to_record_page(self, day: int) -> Callable[[QMouseEvent], None]:
        filter_date = date(
            self.__date_picker.current_year,
            self.__date_picker.current_month,
            day,
        )
        return lambda event: self._notify(
            ToRecordPage(Filter((filter_date, filter_date)))
        )

    @property
    def widget(self) -> QWidget:
        return self.__main_widget


class CalendarPage(Page, Subject, Observer):
    def __init__(self, bakcend: Backend, default_date: Optional[Date]) -> None:
        content = _Content(bakcend, default_date)
        self.subscribe(content)
        super().__init__(bakcend, "Calendar", content)

    def _response(self, message: object) -> None:
        self._notify(message)
