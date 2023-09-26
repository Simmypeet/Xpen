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
)
from enum import Enum
from PySide6.QtCore import Qt, QSize
import platformdirs
import os


class PageType(Enum):
    AccountSelection = (0,)
    Record = (1,)
    CalendarView = (2,)
    ChartView = (3,)
    Setting = (4,)


class AccountSelectionPage:
    __application: Application

    __whole_page_frame: QFrame
    __whole_page_layout: QVBoxLayout

    __new_account_button: HoveredBrightnessButton

    def __init__(self, application: Application):
        self.__application = application
        self.__whole_page_frame = QFrame()
        self.__whole_page_frame.setStyleSheet(
            f"background-color: {self.__application.get_preference().generic_background_1}"
        )
        self.__whole_page_frame.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        self.__whole_page_layout = QVBoxLayout()
        self.__whole_page_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.__whole_page_layout.setContentsMargins(0, 0, 0, 0)
        self.__whole_page_layout.setSpacing(0)
        self.__whole_page_frame.setLayout(self.__whole_page_layout)

        # Add account label
        account_label = QLabel("Accounts")
        account_label.setStyleSheet(
            f"""
            font: 24px;
            color: {self.__application.get_preference().font_color};
            background-color: {self.__application.get_preference().page_text_background};
            padding: 20px;
            font-weight: 10;
            """
        )
        account_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.__whole_page_layout.insertWidget(
            0,
            account_label,
        )

        # Add account page layout
        self.__show_account_page()

        drop_shadow = QGraphicsDropShadowEffect(self.__whole_page_frame)
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

        self.__whole_page_layout.insertWidget(
            2,
            self.__new_account_button,
            alignment=Qt.AlignmentFlag.AlignRight,
        )

        self.__application.add_widget_to_page(self.__whole_page_frame)

    def __show_account_page(self):
        accounts = self.__application.get_accounts()
        if len(accounts) == 0:
            no_account_widget = QWidget()
            no_account_layout = QVBoxLayout()
            no_account_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

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
            no_account_layout.addWidget(no_account_symbol)

            no_account_text = QLabel("No Accounts Found\n\nCreate New One to Start")
            no_account_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
            no_account_text.setStyleSheet(
                f"""
                font: 16px;
                color: {self.__application.get_preference().font_color};
                font-weight: 10;
                """
            )

            no_account_layout.addWidget(no_account_text)
            no_account_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            no_account_widget.setLayout(no_account_layout)

            no_account_widget.setSizePolicy(
                QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
            )

            self.__whole_page_layout.insertWidget(1, no_account_widget)
        else:
            scroll = QScrollArea()
            account_grid_widget = QWidget()
            account_grid_layout = QGridLayout()

            account_grid_layout.setSpacing(0)
            account_grid_layout.setContentsMargins(0, 0, 0, 0)

            account_grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

            def create_header_label(text: str) -> QLabel:
                label = QLabel(text)
                label.setStyleSheet(
                    f"""
                    font: 12px;
                    color: {self.__application.get_preference().font_color};
                    padding: 4px 2px 4px 6px;
                    font-weight: bold;
                    """
                )
                label.setSizePolicy(
                    QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
                )
                label.setAlignment(Qt.AlignmentFlag.AlignHCenter)

                return label

            account_grid_layout.addWidget(
                create_header_label("Name"), 0, 0, alignment=Qt.AlignmentFlag.AlignLeft
            )
            account_grid_layout.addWidget(
                create_header_label("Balance"),
                0,
                1,
                alignment=Qt.AlignmentFlag.AlignLeft,
            )
            account_grid_layout.addWidget(
                create_header_label("Last Access"),
                0,
                2,
                alignment=Qt.AlignmentFlag.AlignLeft,
            )

            account_grid_layout.setColumnStretch(0, 2)
            account_grid_layout.setColumnStretch(1, 1)
            account_grid_layout.setColumnStretch(2, 1)

            line = QFrame()
            line.setFrameShape(QFrame.Shape.HLine)
            line.setFrameShadow(QFrame.Shadow.Plain)
            line.setStyleSheet(
                f"""
                color: {self.__application.get_preference().page_text_background};
                """
            )
            line.setLineWidth(2)
            line.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            account_grid_layout.addWidget(line, 1, 0, 1, 3)

            for index, account in enumerate(accounts):
                account_name = QLabel(account.get_account_name())
                balance = QLabel("$200,000.24")
                date = QLabel("25 Aug BE 2556 15:42")
                style_sheet = f"""
                    font: 12px;
                    padding: 4px 2px 4px 6px;
                    color: {self.__application.get_preference().font_color};
                """

                account_name.setStyleSheet(style_sheet)
                balance.setStyleSheet(style_sheet)
                date.setStyleSheet(style_sheet)

                account_grid_layout.addWidget(account_name, 2 + (index * 2), 0)
                account_grid_layout.addWidget(balance, 2 + (index * 2), 1)
                account_grid_layout.addWidget(date, 2 + (index * 2), 2)

                line = QFrame()
                line.setFrameShape(QFrame.Shape.HLine)
                line.setFrameShadow(QFrame.Shadow.Plain)
                line.setContentsMargins(8, 0, 8, 0)
                line.setStyleSheet(
                    f"""QFrame {{
                    color: {self.__application.get_preference().page_text_background};
                    }}
                    """
                )
                line.setLineWidth(1)
                line.setSizePolicy(
                    QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
                )
                account_grid_layout.addWidget(line, 3 + (index * 2), 0, 1, 3)

            account_grid_widget.setLayout(account_grid_layout)
            account_grid_widget.setSizePolicy(
                QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
            )
            scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
            scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            scroll.setWidgetResizable(True)
            scroll.setWidget(account_grid_widget)
            # disable border
            scroll.setStyleSheet(
                """ 
                QScrollArea {
                    border: none;
                }
                """
            )
            self.__whole_page_layout.insertWidget(1, scroll)

    def get_page_frame(self) -> QFrame:
        return self.__whole_page_frame


class SideBarMenu:
    __application: Application

    __side_bar_box: QVBoxLayout

    MENU_SIZE: Final[int] = 40

    def __init__(self, application: Application) -> None:
        self.__application = application
        self.__side_bar_menu = QVBoxLayout()

        self.__side_bar_menu.setContentsMargins(0, 0, 0, 0)
        self.__side_bar_menu.addWidget(
            HoveredBrightnessButton(
                self.__application.get_resource().account_bar_icon,
                QSize(SideBarMenu.MENU_SIZE, SideBarMenu.MENU_SIZE),
            )
        )
        self.__side_bar_menu.addWidget(
            HoveredBrightnessButton(
                self.__application.get_resource().record_bar_icon,
                QSize(SideBarMenu.MENU_SIZE, SideBarMenu.MENU_SIZE),
            )
        )
        self.__side_bar_menu.addWidget(
            HoveredBrightnessButton(
                self.__application.get_resource().calendar_bar_icon,
                QSize(SideBarMenu.MENU_SIZE, SideBarMenu.MENU_SIZE),
            )
        )
        self.__side_bar_menu.addWidget(
            HoveredBrightnessButton(
                self.__application.get_resource().chart_bar_icon,
                QSize(SideBarMenu.MENU_SIZE, SideBarMenu.MENU_SIZE),
            )
        )
        self.__side_bar_menu.addWidget(
            HoveredBrightnessButton(
                self.__application.get_resource().setting_bar_icon,
                QSize(SideBarMenu.MENU_SIZE, SideBarMenu.MENU_SIZE),
            )
        )

        self.__side_bar_menu.addStretch(1)
        self.__side_bar_menu.setAlignment(Qt.AlignmentFlag.AlignLeft)

        widget = QWidget()
        widget.setFixedWidth(SideBarMenu.MENU_SIZE)
        widget.setLayout(self.__side_bar_menu)

        widget.setStyleSheet(
            f"background-color: {self.__application.get_preference().sidebar_background_1}"
        )

        self.__application.add_widget_to_page(widget)


class Application:
    __appdata_path: str
    __preference: Preference

    __resource: Resource

    # main widget
    __application: QApplication
    __main_window: QMainWindow
    __page_layout: QHBoxLayout

    __side_bar_menu: SideBarMenu

    def __init__(self):
        RESET_DIR_PROMPT = (
            "The application data directory is invalid. Do you want to delete/reset it"
        )

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

        self.__main_window.setStyleSheet(
            f"background-color: {self.__preference.generic_background_1}"
        )

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

        # creates the side bar menu
        self.__side_bar_menu = SideBarMenu(self)

        AccountSelectionPage(self)

        self.__application.exec()

    def get_resource(self) -> Resource:
        return self.__resource

    def get_preference(self) -> Preference:
        """Gets the preference of the application"""
        return self.__preference

    def add_widget_to_page(self, widget: QWidget) -> None:
        self.__page_layout.addWidget(widget)

    def get_accounts(self) -> list[Account]:
        # search all the account data folder
        account_data_folder = os.path.join(self.__appdata_path)

        accounts: list[Account] = []
        for account_name in os.listdir(account_data_folder):
            account_path = os.path.join(account_data_folder, account_name)

            if os.path.isdir(account_path):
                accounts.append(Account(account_name))

        return accounts


if __name__ == "__main__":
    Application()
