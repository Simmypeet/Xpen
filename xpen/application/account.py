import os
import string
from typing import Callable, Optional

from application import auxiliary
from application.auxiliary import HoveredBrightnessButton, InvalidPage, Page
from application.message import ToAccountPage, ToRecordPage
from application.widget import Widget
from backend import Backend
from backend.observer import Subject, Observer
from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QColor, QMouseEvent
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QGraphicsDropShadowEffect,
    QGridLayout,
    QLabel,
    QLineEdit,
    QMenu,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


class _Selection(Subject, Widget):
    __backend: Backend

    __account_selection_widget: QWidget
    __account_selection_layout: QGridLayout
    __account_selection_scroll: QScrollArea

    def __init__(self, backend: Backend) -> None:
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
                font: {self.__backend.preference.content_size}px;
                color: {self.__backend.preference.black_color};
                padding: {int(self.__backend.preference.content_size * 0.5)};
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
        line_margin = int(self.__backend.preference.content_size * 0.5)
        line.setStyleSheet(
            f"""
            color: {self.__backend.preference.light_gray_color};
            margin: 0px {line_margin}px 0px {line_margin}px;
            """
        )
        line.setLineWidth(1)
        line.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        self.__account_selection_layout.addWidget(line, 1, 0, 1, 3)

        accounts = self.__backend.get_accounts()
        for index, account in enumerate(accounts):
            account_name = QLabel(account.name)
            balance = QLabel(f"${account.current_balance}")
            last_modifier = account.last_modified
            date = QLabel(
                f"{last_modifier.day}-{last_modifier.month}-"
                f"{last_modifier.year} {last_modifier.hour}:"
                f"{last_modifier.minute}:{last_modifier.second}"
            )
            padding = int(self.__backend.preference.content_size * 0.25)
            style_sheet = f"""
                font: {self.__backend.preference.content_size}px;
                padding: {padding}px;
                color: {self.__backend.preference.black_color};
            """

            account_name.mousePressEvent = self.__select_account_lambda(
                account.name, account_name
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
                    color: {self.__backend.preference.light_gray_color};
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
        self, account_name: str, widget: QWidget
    ) -> Callable[[QMouseEvent], None]:
        return lambda event: self.__select_account_handler(
            event, account_name, widget
        )

    def __select_account_handler(
        self, mouse_event: QMouseEvent, name: str, widget: QWidget
    ) -> None:
        if mouse_event.button() == Qt.MouseButton.LeftButton:
            account = self.__backend.get_account_by_name(name)
            assert account is not None
            self.__backend.current_working_account = account
            self._notify(ToRecordPage(None))
        elif mouse_event.button() == Qt.MouseButton.RightButton:
            # show context menu
            context_menu = QMenu(widget)
            context_menu.setContextMenuPolicy(
                Qt.ContextMenuPolicy.CustomContextMenu
            )
            delete_action = context_menu.addAction("Delete")  # type: ignore
            rename_action = context_menu.addAction("Rename")  # type: ignore

            delete_action.triggered.connect(
                lambda: self.__delete_confirmation(name)
            )
            rename_action.triggered.connect(lambda: self.__rename_prompt(name))

            context_menu.exec(widget.mapToGlobal(mouse_event.pos()))
            pass

    def __rename_prompt(self, account_name: str) -> None:
        dialog = QDialog(self.__account_selection_widget)
        dialog.setWindowModality(Qt.WindowModality.WindowModal)

        layout = QVBoxLayout()

        rename_label = QLabel("Rename Account", parent=dialog)
        rename_label.setStyleSheet(
            f"""
            font: {self.__backend.preference.sub_header_size}px;
            color: {self.__backend.preference.black_color};
            font-weight: bold;
            """
        )

        line_edit = QLineEdit(parent=dialog)
        line_edit.setPlaceholderText("New Name")
        line_edit.setStyleSheet(
            self.__backend.preference.dialog_line_edit_style()
        )

        confirm_button = QPushButton("Rename")
        confirm_button.setStyleSheet(
            self.__backend.preference.prompt_button_style(
                self.__backend.preference.teal_green_color
            )
        )

        layout.addWidget(rename_label, alignment=Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(line_edit, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(confirm_button, alignment=Qt.AlignmentFlag.AlignRight)

        confirm_button.clicked.connect(lambda: rename())

        def rename():
            dialog.close()
            self.__rename_confirmation_handler(account_name, line_edit.text())
            # reload account page
            self._notify(ToAccountPage())

        dialog.setLayout(layout)

        dialog.exec()

    def __rename_confirmation_handler(
        self, account_name: str, to_name: str
    ) -> None:
        if not _is_valid_account_name(to_name):
            auxiliary.show_error_dialog(
                "Invalid Account Name",
                self.__account_selection_widget,
                self.__backend.preference,
            )
        elif self.__backend.get_account_by_name(to_name) is not None:
            auxiliary.show_error_dialog(
                "Account Already Exists",
                self.__account_selection_widget,
                self.__backend.preference,
            )
        else:
            account = self.__backend.get_account_by_name(account_name)
            assert account is not None

            self.__backend.rename_account(account, to_name)

    def __delete_confirmation(self, account_name: str) -> None:
        dialog = QDialog(self.__account_selection_widget)
        dialog.setWindowModality(Qt.WindowModality.WindowModal)

        layout = QGridLayout()
        confirmation_label = QLabel(
            f"Are you sure you want to delete **{account_name}**?"
        )
        confirmation_label.setTextFormat(Qt.TextFormat.MarkdownText)
        confirmation_label.setStyleSheet(
            f"""
            font: {self.__backend.preference.sub_header_size}px;
            color: {self.__backend.preference.black_color};
            padding: {self.__backend.preference.sub_header_size * 0.5}px;
            """
        )
        confirmation_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        button_style_sheet = self.__backend.preference.prompt_button_style(
            self.__backend.preference.light_gray_color
        )

        yes_button = QPushButton("Yes")
        yes_button.setStyleSheet(button_style_sheet)
        layout.addWidget(
            yes_button, 1, 0, alignment=Qt.AlignmentFlag.AlignRight
        )

        no_button = QPushButton("Cancel")
        no_button.setStyleSheet(button_style_sheet)
        layout.addWidget(no_button, 1, 1, alignment=Qt.AlignmentFlag.AlignLeft)

        layout.addWidget(confirmation_label, 0, 0, 1, 2)

        no_button.clicked.connect(lambda: dialog.close())
        yes_button.clicked.connect(lambda: delete_and_close())

        def delete_and_close():
            account = self.__backend.get_account_by_name(account_name)
            assert account is not None

            self.__backend.delete_account(account)
            dialog.close()
            # reload the account page
            self._notify(ToAccountPage())

        dialog.setLayout(layout)
        dialog.exec()

    @property
    def widget(self) -> QWidget:
        return self.__account_selection_scroll


def _is_valid_account_name(name: str) -> bool:
    for c in name:
        if c in string.punctuation:
            return False

    return len(name) > 0


class _Content(Widget, Observer, Subject):
    __backend: Backend
    __main_layout: QVBoxLayout
    __main_widget: QWidget

    __show_page: Optional[Widget]
    __account_create_button: HoveredBrightnessButton

    def __init__(self, backend: Backend) -> None:
        super().__init__()

        self.__backend = backend
        self.__show_page = None

        # initialize main widget
        self.__main_widget = QWidget()
        self.__main_widget.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )

        # initialize main layout
        self.__main_layout = QVBoxLayout()
        self.__main_layout.setContentsMargins(0, 0, 0, 0)
        self.__main_layout.setSpacing(0)

        # make the main widget use the main layout
        self.__main_widget.setLayout(self.__main_layout)

        # initialize main content
        self.__show_account_page()

        # initialize drop shadow for add new account button
        drop_shadow = QGraphicsDropShadowEffect(self.__main_widget)
        drop_shadow.setBlurRadius(10)
        drop_shadow.setColor(QColor(0, 0, 0, 100))
        drop_shadow.setOffset(1, 1)

        # Add new account button
        self.__account_create_button = HoveredBrightnessButton(
            self.__backend.resource.new_account_symbol,
            QSize(50, 50),
            f"""
            background-color: {self.__backend.preference.teal_green_color};
            border-radius: 21px;
            margin: 4px;
            """,
            icon_size_factor=0.3,
            hover_icon_size_factor=1.2,
        )
        self.__account_create_button.setGraphicsEffect(drop_shadow)
        self.__account_create_button.clicked.connect(
            lambda: self.__create_account_button_handler()
        )

        self.__main_layout.addWidget(
            self.__account_create_button, alignment=Qt.AlignmentFlag.AlignRight
        )

    def __account_created_handler(
        self, account_name: str, dialog_widget: QDialog
    ) -> None:
        dialog_widget.close()

        if account_name == "":
            auxiliary.show_error_dialog(
                "Account Name Cannot Be Empty",
                self.__main_widget,
                self.__backend.preference,
            )
        elif not _is_valid_account_name(account_name):
            auxiliary.show_error_dialog(
                "Invalid Account Name",
                self.__main_widget,
                self.__backend.preference,
            )
        elif os.path.exists(
            os.path.join(self.__backend.application_data_path, account_name)
        ):
            auxiliary.show_error_dialog(
                "Account Already Exists",
                self.__main_widget,
                self.__backend.preference,
            )
        else:
            os.makedirs(
                os.path.join(
                    self.__backend.application_data_path, account_name
                )
            )
            self.__show_account_page()

    @property
    def widget(self) -> QWidget:
        return self.__main_widget

    def _response(self, message: object) -> None:
        # cascade the message to the upper level
        self._notify(message)

    def __show_account_page(self) -> None:
        accounts = self.__backend.get_accounts()
        page_to_add: Widget | Subject
        if len(accounts) == 0:
            page_to_add = InvalidPage(self.__backend)
        else:
            page_to_add = _Selection(self.__backend)

        if isinstance(self.__show_page, Widget):
            self.__main_layout.replaceWidget(
                self.__show_page.widget, page_to_add.widget
            )
        else:
            self.__main_layout.addWidget(page_to_add.widget)

        # detach the current page
        if isinstance(self.__show_page, Subject):
            self.unsubscribe(self.__show_page)

        if isinstance(page_to_add, Subject):
            self.subscribe(page_to_add)

        self.__show_page = page_to_add

    def __create_account_button_handler(self) -> None:
        widget = QDialog(self.__main_widget)
        widget.setWindowModality(Qt.WindowModality.WindowModal)
        layout = QVBoxLayout()

        new_account_label = QLabel("New Account", parent=widget)
        new_account_label.setStyleSheet(
            self.__backend.preference.dialog_prompt_header_style
        )
        layout.addWidget(new_account_label)

        new_account_line_edit = QLineEdit(parent=widget)
        new_account_line_edit.setPlaceholderText("Account Name")
        new_account_line_edit.setStyleSheet(
            self.__backend.preference.dialog_line_edit_style()
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
            background-color: {self.__backend.preference.teal_green_color};
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


class AccountPage(Page, Subject, Observer):
    def __init__(self, backend: Backend) -> None:
        content = _Content(backend)
        self.subscribe(content)

        super().__init__(backend, "Accounts", content)

    def _response(self, message: object) -> None:
        self._notify(message)
