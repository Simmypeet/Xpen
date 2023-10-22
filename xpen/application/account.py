import os
import string
from typing import Callable, Optional

from application.auxiliary import HoveredBrightnessButton, NoAccountPage
from application.message import ToRecordPage
from application.observer import Observer, Subject
from application.widget import Widget
from backend import Backend
from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QColor, QMouseEvent
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QGraphicsDropShadowEffect,
    QGridLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


class AccountSelectionPage(Subject, Widget):
    __backend: Backend

    __account_selection_widget: QWidget
    __account_selection_layout: QGridLayout
    __account_selection_scroll: QScrollArea

    def __init__(self, backend: Backend):
        super().__init__()

        self.__backend = backend

        self.__account_selection_scroll = QScrollArea()
        self.__account_selection_widget = QWidget()
        self.__account_selection_layout = QGridLayout()

        self.__account_selection_layout.setSpacing(0)
        self.__account_selection_layout.setContentsMargins(0, 0, 0, 0)

        self.__account_selection_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        def create_header_label(text: str) -> QLabel:
            label = QLabel(text)
            label.setStyleSheet(
                f"""
                font: 14px;
                color: {self.__backend.preference.font_color};
                padding: 6px 2px 6px 6px;
                font-weight: bold;
                """
            )
            label.setSizePolicy(
                QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
            )
            label.setAlignment(Qt.AlignmentFlag.AlignHCenter)

            return label

        self.__account_selection_layout.addWidget(
            create_header_label("Name"),
            0,
            0,
            alignment=Qt.AlignmentFlag.AlignLeft,
        )
        self.__account_selection_layout.addWidget(
            create_header_label("Balance"),
            0,
            1,
            alignment=Qt.AlignmentFlag.AlignLeft,
        )
        self.__account_selection_layout.addWidget(
            create_header_label("Last Modified"),
            0,
            2,
            alignment=Qt.AlignmentFlag.AlignLeft,
        )

        self.__account_selection_layout.setColumnStretch(0, 2)
        self.__account_selection_layout.setColumnStretch(1, 1)
        self.__account_selection_layout.setColumnStretch(2, 1)

        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Plain)
        line.setStyleSheet(
            f"""
            color: {self.__backend.preference.account_line_separator};
            margin: 0px 8px 0px 8px;
            """
        )
        line.setLineWidth(1)
        line.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        self.__account_selection_layout.addWidget(line, 1, 0, 1, 3)

        accounts = self.__backend.get_accounts()
        for index, account in enumerate(accounts):
            account_name = QLabel(account.account_name)
            balance = QLabel(f"${account.current_balance}")
            last_modifier = account.last_modified
            date = QLabel(
                f"{last_modifier.day}-{last_modifier.month}-"
                f"{last_modifier.year} {last_modifier.hour}:"
                f"{last_modifier.minute}:{last_modifier.second}"
            )
            style_sheet = f"""
                font: 14px;
                padding: 4px 2px 4px 6px;
                color: {self.__backend.preference.font_color};
            """

            account_name.mousePressEvent = self.__select_account_lambda(
                account.account_name
            )  # type: ignore

            account_name.setStyleSheet(style_sheet)
            balance.setStyleSheet(style_sheet)
            date.setStyleSheet(style_sheet)

            self.__account_selection_layout.addWidget(
                account_name, 2 + (index * 2), 0
            )
            self.__account_selection_layout.addWidget(
                balance, 2 + (index * 2), 1
            )
            self.__account_selection_layout.addWidget(date, 2 + (index * 2), 2)

            if index != len(accounts) - 1:
                line = QFrame()
                line.setFrameShape(QFrame.Shape.HLine)
                line.setFrameShadow(QFrame.Shadow.Plain)
                line.setContentsMargins(8, 0, 8, 0)
                line.setStyleSheet(
                    f"""QFrame {{
                    color: {self.__backend.preference.account_line_separator};
                    }}
                    """
                )
                line.setLineWidth(1)
                line.setSizePolicy(
                    QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
                )
                self.__account_selection_layout.addWidget(
                    line, 3 + (index * 2), 0, 1, 3
                )

        self.__account_selection_widget.setLayout(
            self.__account_selection_layout
        )
        self.__account_selection_widget.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        self.__account_selection_scroll.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )
        self.__account_selection_scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.__account_selection_scroll.verticalScrollBar().setStyleSheet(
            self.__backend.preference.scroll_style_sheet
        )
        self.__account_selection_scroll.setWidgetResizable(True)
        self.__account_selection_scroll.setWidget(
            self.__account_selection_widget
        )
        # disable border
        self.__account_selection_scroll.setStyleSheet(
            """
            QScrollArea {
                border: none;
            }
            """
        )

    def __select_account_lambda(
        self, account_name: str
    ) -> Callable[[QMouseEvent], None]:
        return lambda event: self.__select_account_handler(event, account_name)

    def __select_account_handler(self, mouse_event: QMouseEvent, name: str):
        if mouse_event.button() == Qt.MouseButton.LeftButton:
            self.__backend.current_working_account = (
                self.__backend.get_account_by_name(name)
            )
            self.notify(ToRecordPage())

    @property
    def widget(self) -> QWidget:
        return self.__account_selection_scroll


class AccountPage(Widget, Subject, Observer):
    __backend: Backend

    __account_frame: QFrame
    __page_layout: QVBoxLayout

    __new_account_button: HoveredBrightnessButton
    __current_page: Optional[Widget | Subject]

    def __init__(self, backend: Backend):
        super().__init__()

        self.__backend = backend
        self.__current_page = None
        self.__account_frame = QFrame()
        self.__account_frame.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        self.__page_layout = QVBoxLayout()
        self.__page_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.__page_layout.setContentsMargins(0, 0, 0, 0)
        self.__page_layout.setSpacing(0)
        self.__account_frame.setLayout(self.__page_layout)

        # Add account label
        account_label = QLabel("Accounts")
        account_label.setStyleSheet(
            f"""
            font: 24px;
            color: {self.__backend.preference.font_color};
            padding: 15px;
            background-color: {self.__backend.preference.generic_background_1};
            """
        )
        account_label.setAlignment(Qt.AlignmentFlag.AlignLeft)

        self.__page_layout.addWidget(account_label)

        # Add account page layout
        self.__show_account_page()

        drop_shadow = QGraphicsDropShadowEffect(self.__account_frame)
        drop_shadow.setBlurRadius(10)
        drop_shadow.setColor(QColor(0, 0, 0, 100))
        drop_shadow.setOffset(1, 1)

        # Add new account button
        self.__new_account_button = HoveredBrightnessButton(
            self.__backend.resource.new_account_symbol,
            QSize(50, 50),
            f"""
            background-color: {self.__backend.preference.button_color_1};
            border-radius: 21px;
            margin: 4px;
            """,
            icon_size_factor=0.3,
            hover_icon_size_factor=1.2,
        )
        self.__new_account_button.setGraphicsEffect(drop_shadow)

        self.__new_account_button.clicked.connect(
            lambda: self.__create_account_button_handler()
        )

        self.__page_layout.addWidget(
            self.__new_account_button, alignment=Qt.AlignmentFlag.AlignRight
        )

    def __create_account_button_handler(self):
        widget = QDialog(self.__account_frame)
        widget.setWindowModality(Qt.WindowModality.WindowModal)
        layout = QVBoxLayout()

        new_account_label = QLabel("New Account", parent=widget)
        new_account_label.setStyleSheet(
            f"""
            font: 16px;
            color: {self.__backend.preference.font_color};
            font-weight: bold;
            """
        )
        layout.addWidget(new_account_label)

        new_account_line_edit = QLineEdit(parent=widget)
        new_account_line_edit.setPlaceholderText("Account Name")
        new_account_line_edit.setStyleSheet(
            f"""
            font: 16px;
            color: {self.__backend.preference.font_color};
            border: 0px;
            padding: 8px;
            """
        )
        layout.addWidget(new_account_line_edit)

        graphics_effect = QGraphicsDropShadowEffect(widget)
        graphics_effect.setBlurRadius(10)
        graphics_effect.setColor(QColor(0, 0, 0, 100))
        graphics_effect.setOffset(1, 1)
        new_account_button = HoveredBrightnessButton(
            self.__backend.resource.new_account_symbol,
            QSize(36, 36),
            f"""
            background-color: {self.__backend.preference.button_color_1};
            border-radius: 18px;
            """,
            icon_size_factor=0.4,
            hover_icon_size_factor=1.1,
        )
        new_account_button.clicked.connect(
            lambda: self.__account_created_handler(
                new_account_line_edit.text(), widget
            )
        )
        layout.addWidget(
            new_account_button, alignment=Qt.AlignmentFlag.AlignRight
        )
        new_account_button.setGraphicsEffect(graphics_effect)

        widget.setLayout(layout)
        widget.exec()

    def __account_created_handler(
        self, account_name: str, dialog_widget: QDialog
    ):
        dialog_widget.close()

        def show_error_dialog(message: str):
            error_dialog = QDialog(self.__account_frame)
            error_dialog.setWindowModality(Qt.WindowModality.WindowModal)

            layout = QVBoxLayout()

            error_label = QLabel(message)
            error_label.setStyleSheet(
                f"""
                font: 16px;
                color: {self.__backend.preference.font_color};
                padding: 8px;
                """
            )
            layout.addWidget(error_label)

            close_button = QPushButton("Close")
            close_button.setStyleSheet(
                f"""
                font: 16px;
                color: {self.__backend.preference.font_color};
                padding: 8px;
                border-radius: 4px;
                border: 0px;
                background-color: {self.__backend.preference.button_color_2};
                """
            )
            close_button.clicked.connect(lambda: error_dialog.close())
            layout.addWidget(
                close_button, alignment=Qt.AlignmentFlag.AlignCenter
            )

            error_dialog.setLayout(layout)

            error_dialog.exec()

        if account_name == "":
            show_error_dialog("Account Name Cannot Be Empty")
        elif not AccountPage.__is_valid_account_name(account_name):
            show_error_dialog("Invalid Account Name")
        elif os.path.exists(
            os.path.join(self.__backend.application_data_path, account_name)
        ):
            show_error_dialog("Account Already Exists")
        else:
            os.makedirs(
                os.path.join(
                    self.__backend.application_data_path, account_name
                )
            )
            self.__show_account_page()

    @staticmethod
    def __is_valid_account_name(name: str) -> bool:
        for c in name:
            if c in string.punctuation:
                return False

        return True

    def __show_account_page(self):
        accounts = self.__backend.get_accounts()
        page_to_add: Widget | Subject
        if len(accounts) == 0:
            page_to_add = NoAccountPage(self.__backend)
        else:
            page_to_add = AccountSelectionPage(self.__backend)

        if isinstance(self.__current_page, Widget):
            self.__page_layout.replaceWidget(
                self.__current_page.widget, page_to_add.widget
            )
        else:
            self.__page_layout.addWidget(page_to_add.widget)

        if isinstance(self.__current_page, Subject):
            self.__current_page.detach(self)

        if isinstance(page_to_add, Subject):
            page_to_add.attach(self)

        self.__current_page = page_to_add

    def response(self, message: object) -> None:
        # cascade the message to the downstream observer
        return self.notify(message)

    @property
    def widget(self) -> QWidget:
        return self.__account_frame
