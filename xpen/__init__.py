from __future__ import annotations
from xpen.preference import Preference
from xpen.resource import Resource
from xpen.widget import HoveredBrightnessButton
from xpen.account import Account
from typing import Final
from PySide6.QtGui import QPixmap, QPainter, QColor
from PySide6.QtWidgets import (
    QMessageBox,
    QApplication,
    QMainWindow,
    QVBoxLayout,
    QWidget,
    QFrame,
    QSizePolicy,
    QHBoxLayout,
    QLabel,
    QGraphicsDropShadowEffect,
    QGridLayout,
    QScrollArea,
    QLineEdit,
    QDialog,
    QPushButton,
)
from enum import Enum
from PySide6.QtCore import Qt, QSize
import platformdirs
import os
from abc import ABC, abstractmethod


class Page(ABC):
    @abstractmethod
    def get_page_widget(self) -> QWidget:
        raise NotImplementedError()


class PageType(Enum):
    AccountSelection = (0,)
    Record = (1,)
    CalendarView = (2,)
    ChartView = (3,)
    Setting = (4,)


class RecordPage(Page):
    __application: Application

    __record_page_widget: QWidget
    __record_page_layout: QVBoxLayout
    __account: Account

    def __init__(self, application: Application, account_name: str):
        self.__application = application

        # pedantic check
        self.__account = application.get_accounts_by_name(account_name)

    def get_page_widget(self) -> QWidget:
        return self.__record_page_widget


class NoAccountPage(Page):
    __application: Application

    __no_account_widget: QWidget
    __no_account_layout: QVBoxLayout

    def __init__(self, application: Application):
        self.__application = application

        self.__no_account_widget = QWidget()
        self.__no_account_layout = QVBoxLayout()
        self.__no_account_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # show no account page and prompt user to create one
        pixmap = QPixmap(QSize(50, 50))
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        self.__application.get_resource().account_not_found_symol.render(painter)
        painter.setCompositionMode(painter.CompositionMode.CompositionMode_SourceIn)
        painter.fillRect(
            pixmap.rect(), QColor(self.__application.get_preference().font_color)
        )
        painter.end()

        no_account_symbol = QLabel()
        no_account_symbol.setPixmap(pixmap)
        no_account_symbol.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.__no_account_layout.addWidget(no_account_symbol)

        no_account_text = QLabel("No Accounts Found\n\nCreate New One to Start")
        no_account_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        no_account_text.setStyleSheet(
            f"""
            font: 16px;
            color: {self.__application.get_preference().font_color};
            """
        )

        self.__no_account_layout.addWidget(no_account_text)
        self.__no_account_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.__no_account_widget.setLayout(self.__no_account_layout)

        self.__no_account_widget.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )

    # pverride
    def get_page_widget(self) -> QWidget:
        return self.__no_account_widget


class AccountSelectionPage(Page):
    __application: Application

    __account_selection_widget: QWidget
    __account_selection_layout: QGridLayout
    __account_selection_scroll: QScrollArea

    def __init__(self, application: Application):
        self.__application = application

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
                font: 12px;
                color: {self.__application.get_preference().font_color};
                padding: 6px 2px 6px 6px;
                font-weight: bold;
                """
            )
            label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            label.setAlignment(Qt.AlignmentFlag.AlignHCenter)

            return label

        self.__account_selection_layout.addWidget(
            create_header_label("Name"), 0, 0, alignment=Qt.AlignmentFlag.AlignLeft
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
            color: {self.__application.get_preference().account_line_separator};
            margin: 0px 8px 0px 8px;
            """
        )
        line.setLineWidth(1)
        line.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.__account_selection_layout.addWidget(line, 1, 0, 1, 3)

        accounts = self.__application.get_accounts()
        for index, account in enumerate(accounts):
            account_name = QLabel(account.get_account_name())
            balance = QLabel(f"${account.get_current_balance()}")
            date = QLabel(f"{account.get_last_modified()}")
            style_sheet = f"""
                font: 12px;
                padding: 4px 2px 4px 6px;
                color: {self.__application.get_preference().font_color};
            """

            account_name.setStyleSheet(style_sheet)
            balance.setStyleSheet(style_sheet)
            date.setStyleSheet(style_sheet)

            self.__account_selection_layout.addWidget(account_name, 2 + (index * 2), 0)
            self.__account_selection_layout.addWidget(balance, 2 + (index * 2), 1)
            self.__account_selection_layout.addWidget(date, 2 + (index * 2), 2)

            if index != len(accounts) - 1:
                line = QFrame()
                line.setFrameShape(QFrame.Shape.HLine)
                line.setFrameShadow(QFrame.Shadow.Plain)
                line.setContentsMargins(8, 0, 8, 0)
                line.setStyleSheet(
                    f"""QFrame {{
                    color: {self.__application.get_preference().account_line_separator};
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

        self.__account_selection_widget.setLayout(self.__account_selection_layout)
        self.__account_selection_widget.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        self.__account_selection_scroll.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )
        self.__account_selection_scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.__account_selection_scroll.setWidgetResizable(True)
        self.__account_selection_scroll.setWidget(self.__account_selection_widget)
        # disable border
        self.__account_selection_scroll.setStyleSheet(
            """ 
            QScrollArea {
                border: none;
            }
            """
        )

    def get_page_widget(self) -> QWidget:
        return self.__account_selection_scroll


class AccountPage(Page):
    __application: Application

    __page_frame: QFrame
    __page_layout: QVBoxLayout

    __new_account_button: HoveredBrightnessButton
    __current_page: Page | None

    def __init__(self, application: Application):
        self.__application = application
        self.__page_frame = QFrame()
        self.__current_page = None
        self.__page_frame.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        self.__page_layout = QVBoxLayout()
        self.__page_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.__page_layout.setContentsMargins(0, 0, 0, 0)
        self.__page_layout.setSpacing(0)
        self.__page_frame.setLayout(self.__page_layout)

        # Add account label
        account_label = QLabel("Accounts")
        account_label.setStyleSheet(
            f"""
            font: 24px;
            color: {self.__application.get_preference().font_color};
            padding: 15px 30px 15px 30px;
            background-color: {self.__application.get_preference().generic_background_1};
            """
        )
        account_label.setAlignment(Qt.AlignmentFlag.AlignLeft)

        self.__page_layout.insertWidget(
            0,
            account_label,
        )

        # Add account page layout
        self.__show_account_page()

        drop_shadow = QGraphicsDropShadowEffect(self.__page_frame)
        drop_shadow.setBlurRadius(10)
        drop_shadow.setColor(QColor(0, 0, 0, 100))
        drop_shadow.setOffset(1, 1)

        # Add new account button
        self.__new_account_button = HoveredBrightnessButton(
            self.__application.get_resource().new_account_symbol,
            QSize(50, 50),
            f"""
            background-color: {self.__application.get_preference().button_color_1};
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

        self.__page_layout.insertWidget(
            2,
            self.__new_account_button,
            alignment=Qt.AlignmentFlag.AlignRight,
        )

    def __create_account_button_handler(self):
        widget = QDialog(self.__page_frame)
        widget.setWindowModality(Qt.WindowModality.WindowModal)
        layout = QVBoxLayout()

        new_account_label = QLabel("New Account", parent=widget)
        new_account_label.setStyleSheet(
            f"""
            font: 16px;
            color: {self.__application.get_preference().font_color};    
            font-weight: bold;
            """
        )
        layout.addWidget(new_account_label)

        new_account_line_edit = QLineEdit(parent=widget)
        new_account_line_edit.setPlaceholderText("Account Name")
        new_account_line_edit.setStyleSheet(
            f"""
            font: 16px;
            color: {self.__application.get_preference().font_color};
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
            self.__application.get_resource().new_account_symbol,
            QSize(36, 36),
            f"""
            background-color: {self.__application.get_preference().button_color_1};
            border-radius: 18px;
            """,
            icon_size_factor=0.4,
            hover_icon_size_factor=1.1,
        )
        new_account_button.clicked.connect(
            lambda: self.__account_created_handler(new_account_line_edit.text(), widget)
        )
        layout.addWidget(new_account_button, alignment=Qt.AlignmentFlag.AlignRight)
        new_account_button.setGraphicsEffect(graphics_effect)

        widget.setLayout(layout)
        widget.exec()

    def __account_created_handler(self, account_name: str, dialog_widget: QDialog):
        dialog_widget.close()

        def show_error_dialog(message: str):
            error_dialog = QDialog(self.__page_frame)
            error_dialog.setWindowModality(Qt.WindowModality.WindowModal)

            layout = QVBoxLayout()

            error_label = QLabel(message)
            error_label.setStyleSheet(
                f"""
                font: 16px;
                color: {self.__application.get_preference().font_color};
                padding: 8px;
                """
            )
            layout.addWidget(error_label)

            close_button = QPushButton("Close")
            close_button.setStyleSheet(
                f"""
                font: 16px;
                color: {self.__application.get_preference().font_color};
                padding: 8px;
                border-radius: 4px;
                border: 0px;
                background-color: {self.__application.get_preference().button_color_2};
                """
            )
            close_button.clicked.connect(lambda: error_dialog.close())
            layout.addWidget(close_button, alignment=Qt.AlignmentFlag.AlignCenter)

            error_dialog.setLayout(layout)

            error_dialog.exec()

        if not account_name.isalnum():
            show_error_dialog("Invalid Account Name")
        elif os.path.exists(
            os.path.join(self.__application.get_appdata_path(), account_name)
        ):
            show_error_dialog("Account Already Exists")
        else:
            os.makedirs(
                os.path.join(self.__application.get_appdata_path(), account_name)
            )
            self.__show_account_page()

    # override
    def get_page_widget(self) -> QWidget:
        return self.__page_frame

    def __show_account_page(self):
        accounts = self.__application.get_accounts()
        page_to_add: Page | None = None
        if len(accounts) == 0:
            page_to_add = NoAccountPage(self.__application)
        else:
            page_to_add = AccountSelectionPage(self.__application)

        if self.__current_page is not None:
            self.__page_layout.replaceWidget(
                self.__current_page.get_page_widget(), page_to_add.get_page_widget()
            )
        else:
            self.__page_layout.addWidget(page_to_add.get_page_widget())

        self.__current_page = page_to_add

    def get_page_frame(self) -> QFrame:
        return self.__page_frame


class SideBarMenu(Page):
    __application: Application

    __side_bar_widget: QWidget
    __side_bar_layout: QVBoxLayout

    MENU_SIZE: Final[int] = 40

    def __init__(self, application: Application) -> None:
        self.__application = application
        self.__side_bar_layout = QVBoxLayout()

        self.__side_bar_layout.setContentsMargins(0, 0, 0, 0)
        self.__side_bar_layout.addWidget(
            HoveredBrightnessButton(
                self.__application.get_resource().account_bar_icon,
                QSize(SideBarMenu.MENU_SIZE, SideBarMenu.MENU_SIZE),
            )
        )
        self.__side_bar_layout.addWidget(
            HoveredBrightnessButton(
                self.__application.get_resource().record_bar_icon,
                QSize(SideBarMenu.MENU_SIZE, SideBarMenu.MENU_SIZE),
            )
        )
        self.__side_bar_layout.addWidget(
            HoveredBrightnessButton(
                self.__application.get_resource().calendar_bar_icon,
                QSize(SideBarMenu.MENU_SIZE, SideBarMenu.MENU_SIZE),
            )
        )
        self.__side_bar_layout.addWidget(
            HoveredBrightnessButton(
                self.__application.get_resource().chart_bar_icon,
                QSize(SideBarMenu.MENU_SIZE, SideBarMenu.MENU_SIZE),
            )
        )
        self.__side_bar_layout.addWidget(
            HoveredBrightnessButton(
                self.__application.get_resource().setting_bar_icon,
                QSize(SideBarMenu.MENU_SIZE, SideBarMenu.MENU_SIZE),
            )
        )

        self.__side_bar_layout.addStretch(1)
        self.__side_bar_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

        self.__side_bar_widget = QWidget()
        self.__side_bar_widget.setFixedWidth(SideBarMenu.MENU_SIZE)
        self.__side_bar_widget.setLayout(self.__side_bar_layout)

        self.__side_bar_widget.setStyleSheet(
            f"background-color: {self.__application.get_preference().sidebar_background_1}"
        )

    # override
    def get_page_widget(self) -> QWidget:
        return self.__side_bar_widget


class Application:
    __appdata_path: str
    __preference: Preference

    __resource: Resource

    # main widget
    __application: QApplication
    __main_window: QMainWindow
    __page_layout: QHBoxLayout

    __side_bar_menu: SideBarMenu
    __current_page: Page | None

    __acounts_by_name: dict[str, Account]

    def __init__(self):
        RESET_DIR_PROMPT = (
            "The application data directory is invalid. Do you want to delete/reset it"
        )

        self.__current_page = None
        self.__acounts_by_name = {}

        # creates a qt application
        self.__application = QApplication()
        self.__main_window = QMainWindow()
        self.__main_window.show()
        self.__main_window.setGeometry(0, 0, 800, 600)

        # gets the application data path
        self.__appdata_path = platformdirs.user_data_dir("xpen", "xpen")

        # if the application data directory does not exist, create it and initialize it
        if not os.path.exists(self.__appdata_path):
            os.makedirs(self.__appdata_path)
        # the directory exists, check if it's directory and valid
        else:
            if not os.path.isdir(self.__appdata_path):
                msg_box = QMessageBox()
                msg_box.setText(RESET_DIR_PROMPT)
                msg_box.setStandardButtons(
                    QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.No
                )
                msg_box.setDefaultButton(QMessageBox.StandardButton.No)

                response = msg_box.exec()

                # if the user wants to reset the directory, delete it and create a new
                # one
                if response == QMessageBox.StandardButton.Ok:
                    os.remove(self.__appdata_path)
                    os.makedirs(self.__appdata_path)
                else:
                    exit(1)

        # loads the preference
        preference_file_path = os.path.join(self.__appdata_path, "preference.json")

        try:
            self.__preference = Preference.load_from_file(preference_file_path)
        except Exception:
            # remove the preference file if it exists
            if os.path.exists(preference_file_path):
                os.remove(preference_file_path)

            self.__preference = Preference()
            self.__preference.save(preference_file_path)

        self.__resource = Resource.load_from_resource_folder(
            os.path.join(os.path.dirname(__file__), "resources")
        )

        self.__page_layout = QHBoxLayout()
        self.__page_layout.setContentsMargins(0, 0, 0, 0)
        self.__page_layout.setSpacing(0)
        self.__page_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        widget = QWidget()
        widget.setLayout(self.__page_layout)
        self.__main_window.setCentralWidget(widget)
        self.__main_window.setWindowTitle("Xpen")
        self.__main_window.setStyleSheet("background-color: #ffffff")

        # creates the side bar menu
        self.__side_bar_menu = SideBarMenu(self)
        self.__page_layout.insertWidget(0, self.__side_bar_menu.get_page_widget())

        self.add_widget_to_page(AccountPage(self))

        self.__application.exec()

    def get_resource(self) -> Resource:
        return self.__resource

    def get_preference(self) -> Preference:
        """Gets the preference of the application"""
        return self.__preference

    def add_widget_to_page(self, widget: Page) -> None:
        if self.__current_page is not None:
            self.__page_layout.replaceWidget(
                self.__current_page.get_page_widget(), widget.get_page_widget()
            )
            self.__current_page = widget
        else:
            self.__page_layout.insertWidget(1, widget.get_page_widget())

    def get_main_window(self) -> QMainWindow:
        return self.__main_window

    def get_appdata_path(self) -> str:
        return self.__appdata_path

    def get_accounts(self) -> list[Account]:
        # search all the account data folder
        account_data_folder = os.path.join(self.__appdata_path)

        accounts: list[Account] = []
        for account_name in os.listdir(account_data_folder):
            account_path = os.path.join(account_data_folder, account_name)

            if not os.path.isdir(account_path):
                continue

            if account_name not in self.__acounts_by_name:
                self.__acounts_by_name[account_name] = Account(account_path)

            accounts.append(self.__acounts_by_name[account_name])

        return accounts

    def get_accounts_by_name(self, name: str) -> Account:
        self.get_accounts()

        return self.__acounts_by_name[name]


if __name__ == "__main__":
    app = Application()
