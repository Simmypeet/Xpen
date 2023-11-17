from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from datetime import date
from typing import Callable, Optional

from application import auxiliary
from application.widget import Widget
from backend.account import RecordDiff
from backend.preference import Preference
from PySide6.QtCore import QDate, Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QDateEdit,
    QDialog,
    QGridLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


@dataclass
class Filter:
    date_range: Optional[tuple[date, date]] = None
    tag: Optional[str] = None
    show_income: bool = True
    show_expense: bool = True

    def filter(self, record: RecordDiff) -> bool:
        """Determines whether the record should be shown or not"""

        if self.date_range is not None:
            if record.record.date.date() < self.date_range[0]:
                return False
            if record.record.date.date() > self.date_range[1]:
                return False

        if self.tag is not None:
            if record.record.tag != self.tag:
                return False

        if self.show_expense and record.diff < 0:
            return True

        if self.show_income and record.diff > 0:
            return True

        return False

    def deepcopy(self) -> Filter:
        """Returns a deep copy of the filter"""

        return Filter(
            date_range=None
            if self.date_range is None
            else (
                date(
                    self.date_range[0].year,
                    self.date_range[0].month,
                    self.date_range[0].day,
                ),
                date(
                    self.date_range[1].year,
                    self.date_range[1].month,
                    self.date_range[1].day,
                ),
            ),
            tag=None if self.tag is None else deepcopy(self.tag),
            show_income=self.show_income,
            show_expense=self.show_expense,
        )

    @staticmethod
    def show_propmt_dialog(
        preference: Preference,
        parent_widget: QWidget,
        existing_filter: Filter,
        on_save: Callable[[Filter], None],
    ) -> None:
        """Shows a dialog to prompt the user to modify the filter settings"""

        propmt_dialog = QDialog(parent_widget)
        propmt_dialog.setWindowModality(Qt.WindowModality.WindowModal)

        new_filter = existing_filter.deepcopy()

        layout = QVBoxLayout()

        filter_label = QLabel("Filter")
        filter_label.setStyleSheet(preference.dialog_prompt_header_style)
        layout.addWidget(filter_label)

        # Tag filter
        tag_line_edit = QLineEdit(parent=propmt_dialog)
        tag_line_edit.setPlaceholderText("Tag Filter")
        tag_line_edit.setText("" if new_filter.tag is None else new_filter.tag)
        tag_line_edit.setStyleSheet(
            preference.dialog_line_edit_style(preference.black_color)
        )
        layout.addWidget(tag_line_edit, alignment=Qt.AlignmentFlag.AlignLeft)

        check_box_style = f"""
            font: {preference.content_size}px;
            color: {preference.black_color};
            padding: {preference.content_size * 0.5}px;
        """

        # Income filter button
        show_income_button = QCheckBox("Show Income")
        show_income_button.setChecked(new_filter.show_income)
        show_income_button.setStyleSheet(check_box_style)
        layout.addWidget(
            show_income_button, alignment=Qt.AlignmentFlag.AlignLeft
        )

        # Expense filter button
        show_expense_button = QCheckBox("Show Expense")
        show_expense_button.setChecked(new_filter.show_expense)
        show_expense_button.setStyleSheet(check_box_style)
        layout.addWidget(
            show_expense_button, alignment=Qt.AlignmentFlag.AlignLeft
        )

        # Filter date range
        filter_date_button = QCheckBox("Filter Date")
        filter_date_button.setChecked(new_filter.date_range is not None)
        filter_date_button.setStyleSheet(check_box_style)
        layout.addWidget(
            filter_date_button, alignment=Qt.AlignmentFlag.AlignLeft
        )

        date_filter_edit = _DateFilterEdit(new_filter, preference)
        layout.addWidget(date_filter_edit.widget)

        save_button = QPushButton("Save")
        save_button.setStyleSheet(
            preference.prompt_button_style(preference.teal_green_color)
        )
        save_button.clicked.connect(lambda: save_button_callback())

        def save_button_callback():
            if filter_date_button.isChecked():
                if date_filter_edit.to_date < date_filter_edit.from_date:
                    propmt_dialog.close()
                    auxiliary.show_error_dialog(
                        "Invalid date range", parent_widget, preference
                    )
                    on_save(new_filter)

                new_filter.date_range = (
                    date_filter_edit.from_date,
                    date_filter_edit.to_date,
                )
            else:
                new_filter.date_range = None

            new_filter.tag = (
                tag_line_edit.text() if len(tag_line_edit.text()) > 0 else None
            )

            new_filter.show_income = show_income_button.isChecked()
            new_filter.show_expense = show_expense_button.isChecked()

            on_save(new_filter)
            propmt_dialog.close()

        layout.addWidget(save_button, alignment=Qt.AlignmentFlag.AlignCenter)

        propmt_dialog.setLayout(layout)
        propmt_dialog.exec()


class _DateFilterEdit(Widget):
    __main_widget: QWidget
    __existing_filter: Filter
    __from_date_edit: QDateEdit
    __to_date_edit: QDateEdit

    def __init__(
        self, existing_filter: Filter, preference: Preference
    ) -> None:
        self.__existing_filter = existing_filter

        self.__main_widget = QWidget()
        margin = int(preference.content_size * 0.25)
        self.__main_widget.setContentsMargins(margin, margin, margin, margin)

        grid_layout = QGridLayout()
        grid_layout.setContentsMargins(0, 0, 0, 0)
        grid_layout.setSpacing(0)

        def create_label(text: str):
            label = QLabel(text)
            label.setStyleSheet(
                f"""
                font: {preference.content_size}px;
                color: {preference.black_color};
                font-weight: bold;
                """
            )
            label.setAlignment(Qt.AlignmentFlag.AlignLeft)
            return label

        grid_layout.addWidget(create_label("From:"), 0, 0)
        grid_layout.addWidget(create_label("To:"), 0, 1)

        from_python_date = (
            date.today()
            if self.__existing_filter.date_range is None
            else self.__existing_filter.date_range[0]
        )
        self.__from_date_edit = QDateEdit()
        self.__from_date_edit.setDate(
            QDate(
                from_python_date.year,
                from_python_date.month,
                from_python_date.day,
            )
        )
        self.__from_date_edit.setStyleSheet(
            preference.dialog_line_edit_style(preference.black_color)
        )
        grid_layout.addWidget(self.__from_date_edit, 1, 0)

        to_python_date = (
            date.today()
            if self.__existing_filter.date_range is None
            else self.__existing_filter.date_range[1]
        )
        self.__to_date_edit = QDateEdit()
        self.__to_date_edit.setDate(
            QDate(
                to_python_date.year,
                to_python_date.month,
                to_python_date.day,
            )
        )
        self.__to_date_edit.setSelectedSection(QDateEdit.Section.NoSection)
        self.__to_date_edit.setStyleSheet(
            preference.dialog_line_edit_style(preference.black_color)
        )
        grid_layout.addWidget(self.__to_date_edit, 1, 1)

        self.__main_widget.setLayout(grid_layout)

    @property
    def widget(self) -> QWidget:
        return self.__main_widget

    @property
    def from_date(self) -> date:
        return date(
            self.__from_date_edit.date().year(),
            self.__from_date_edit.date().month(),
            self.__from_date_edit.date().day(),
        )

    @property
    def to_date(self) -> date:
        return date(
            self.__to_date_edit.date().year(),
            self.__to_date_edit.date().month(),
            self.__to_date_edit.date().day(),
        )
