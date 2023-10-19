import os
from typing import Final

import platformdirs
from application.account import AccountPage
from application.auxiliary import HoveredBrightnessButton
from application.message import ToAccountPage
from application.observer import Observer, Subject
from application.widget import Widget
from backend import Backend
from backend.history import History
from backend.preference import Preference
from backend.resource import Resource
from PySide6.QtCore import QSize, Qt
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QMainWindow,
    QMessageBox,
    QVBoxLayout,
    QWidget,
)


class SideBarMenu(Subject):
    __side_bar_widget: QWidget
    __data: Backend

    MENU_SIZE: Final[int] = 40

    def __init__(
        self,
        data: Backend,
    ) -> None:
        super().__init__()

        self.__side_bar_layout = QVBoxLayout()
        self.__data = data

        self.__side_bar_layout.setContentsMargins(0, 0, 0, 0)
        self.__side_bar_layout.addWidget(
            self.__create_side_bar_button(
                self.__data.resource.account_bar_icon,
                lambda: self.notify(None),
            )
        )
        self.__side_bar_layout.addWidget(
            self.__create_side_bar_button(
                self.__data.resource.record_bar_icon,
                lambda: self.notify(None),
            )
        )
        self.__side_bar_layout.addWidget(
            HoveredBrightnessButton(
                self.__data.resource.calendar_bar_icon,
                QSize(SideBarMenu.MENU_SIZE, SideBarMenu.MENU_SIZE),
            )
        )
        self.__side_bar_layout.addWidget(
            HoveredBrightnessButton(
                self.__data.resource.chart_bar_icon,
                QSize(SideBarMenu.MENU_SIZE, SideBarMenu.MENU_SIZE),
            )
        )
        self.__side_bar_layout.addWidget(
            HoveredBrightnessButton(
                self.__data.resource.setting_bar_icon,
                QSize(SideBarMenu.MENU_SIZE, SideBarMenu.MENU_SIZE),
            )
        )

        self.__side_bar_layout.addStretch(1)
        self.__side_bar_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

        self.__side_bar_widget = QWidget()
        self.__side_bar_widget.setFixedWidth(SideBarMenu.MENU_SIZE)
        self.__side_bar_widget.setLayout(self.__side_bar_layout)

        self.__side_bar_widget.setStyleSheet(
            f"background-color: {self.__data.preference.sidebar_background_1}"
        )

    def __create_side_bar_button(
        self, icon: QSvgRenderer, command: object
    ) -> HoveredBrightnessButton:
        button = HoveredBrightnessButton(
            icon,
            QSize(SideBarMenu.MENU_SIZE, SideBarMenu.MENU_SIZE),
        )

        button.clicked.connect(command)

        return button

    # override
    def get_page_widget(self) -> QWidget:
        return self.__side_bar_widget


class Application(Observer):
    # main widget
    __application: QApplication
    __main_window: QMainWindow
    __page_layout: QHBoxLayout

    __side_bar_menu: SideBarMenu

    __backend: Backend
    __current_page: Widget | None

    def __init__(self):
        super().__init__()

        RESET_DIR_PROMPT = "The application data directory is corrupted. \
            Do you want to delete/reset it"

        # creates a qt application
        self.__application = QApplication()
        self.__main_window = QMainWindow()
        self.__main_window.show()
        self.__current_page = None
        self.__main_window.setGeometry(0, 0, 800, 600)

        # gets the application data path
        appdata_path = platformdirs.user_data_dir("xpen", "xpen")

        # if the application data directory does not exist, create it and
        # initialize it
        if not os.path.exists(appdata_path):
            os.makedirs(appdata_path)
        # the directory exists, check if it's directory and valid
        else:
            if not os.path.isdir(appdata_path):
                msg_box = QMessageBox()
                msg_box.setText(RESET_DIR_PROMPT)
                msg_box.setStandardButtons(
                    QMessageBox.StandardButton.Ok
                    | QMessageBox.StandardButton.No
                )
                msg_box.setDefaultButton(QMessageBox.StandardButton.No)

                response = msg_box.exec()

                # if the user wants to reset the directory, delete it and
                # create a new one
                if response == QMessageBox.StandardButton.Ok:
                    os.remove(appdata_path)
                    os.makedirs(appdata_path)
                else:
                    exit(1)

        # loads the preference
        preference_file_path = os.path.join(appdata_path, "preference.json")

        try:
            preference = Preference.load_from_file(preference_file_path)
        except Exception:
            # remove the preference file if it exists
            if os.path.exists(preference_file_path):
                os.remove(preference_file_path)

            preference = Preference()
            preference.save(preference_file_path)

        resource = Resource.load_from_resource_folder(
            os.path.join(os.path.dirname(__file__), "resources")
        )

        self.__backend = Backend(
            preference, resource, History("test"), appdata_path
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
        self.__side_bar_menu = SideBarMenu(self.__backend)
        self.__page_layout.insertWidget(
            0, self.__side_bar_menu.get_page_widget()
        )

        self.__side_bar_menu.attach(self)

        self.__set_page(AccountPage(self.__backend))

        self.__application.exec()

    def get_main_window(self) -> QMainWindow:
        """Returns the QMainWindow object of the application"""

        return self.__main_window

    def response(self, message: object) -> None:
        match message:
            case ToAccountPage():
                pass
            case object():
                pass

    def __set_page(self, page: Widget) -> None:
        if self.__current_page is not None:
            self.__page_layout.replaceWidget(
                self.__current_page.widget,
                self.__side_bar_menu.get_page_widget(),
            )
        else:
            self.__page_layout.insertWidget(1, page.widget)

        if isinstance(self.__current_page, Subject):
            self.__current_page.detach(self)

        if isinstance(page, Subject):
            page.attach(self)

        self.__current_page = page
