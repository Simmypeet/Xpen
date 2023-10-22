from typing import Optional
from application.widget import Widget
from backend import Backend

from PySide6.QtWidgets import QFrame, QVBoxLayout, QSizePolicy, QLabel, QWidget
from PySide6.QtCore import Qt

from application.auxiliary import NoAccountPage
from backend.account import RecordFile


class ContentPage(Widget):
    __backend: Backend
    __main_widget: QWidget
    __current_record_file: RecordFile

    def __init__(self, backend: Backend) -> None:
        self.__backend = backend
        self.__main_widget = QWidget()

    @property
    def widget(self) -> QWidget:
        return self.__main_widget


class CalendarPage(Widget):
    __backend: Backend

    __calendar_frame: QFrame
    __page_layout: QVBoxLayout

    __current_widget: Optional[Widget]

    def __init__(self, backend: Backend) -> None:
        self.__backend = backend

        self.__current_widget = None

        self.__calendar_frame = QFrame()
        self.__calendar_frame.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        self.__page_layout = QVBoxLayout()
        self.__page_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.__page_layout.setContentsMargins(0, 0, 0, 0)
        self.__page_layout.setSpacing(0)

        self.__calendar_frame.setLayout(self.__page_layout)

        # Add calendar label
        calendar_label = QLabel("Calendar")
        calendar_label.setStyleSheet(
            f"""
            font: 24px;
            color: {self.__backend.preference.font_color};
            padding: 15px;
            background-color: {self.__backend.preference.generic_background_1};
            """
        )
        calendar_label.setAlignment(Qt.AlignmentFlag.AlignLeft)

        self.__page_layout.addWidget(calendar_label)

        self.__show_calendar_page()

    @property
    def widget(self) -> QWidget:
        return self.__calendar_frame

    def __show_calendar_page(self):
        if self.__backend.current_working_account is not None:
            widget_to_add = ContentPage(self.__backend)
        else:
            widget_to_add = NoAccountPage(self.__backend)

        if self.__current_widget is not None:
            self.__page_layout.replaceWidget(
                self.__current_widget.widget,
                widget_to_add.widget,
            )
        else:
            self.__page_layout.addWidget(widget_to_add.widget)

        self.__current_widget = widget_to_add
