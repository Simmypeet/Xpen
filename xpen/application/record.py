from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Optional

from application.auxiliary import (
    Collapsible,
    HoveredBrightnessButton,
    NoAccountPage,
)
from application.widget import Widget
from backend import Backend
from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QColor, QValidator
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QGraphicsDropShadowEffect,
    QLabel,
    QLineEdit,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
    QScrollArea,
    QGridLayout,
    QToolButton,
    QTextEdit,
)

from backend.account import RecordDiff, RecordIterator


class NumberValidator(QValidator):
    def validate(self, arg__1: str, arg__2: int):
        if arg__1 == "" or arg__1 == "-":
            return QValidator.State.Intermediate, arg__1, arg__2

        try:
            decimal = Decimal(arg__1)

            # zero is invalid
            if decimal.is_zero():
                return QValidator.State.Invalid, arg__1, arg__2

            # at most 2 decimal places
            if decimal.as_tuple().exponent < -2:  # type: ignore
                return QValidator.State.Invalid, arg__1, arg__2

            return QValidator.State.Acceptable, arg__1, arg__2
        except Exception:
            return QValidator.State.Invalid, arg__1, arg__2


class RecordLabel(Widget):
    __backend: Backend
    __main_widget: QWidget
    __main_layout: QVBoxLayout
    __record_widget: QWidget
    __detail_collapsible: Collapsible
    __toggle_button: QToolButton

    def __init__(self, backend: Backend, record_diff: RecordDiff) -> None:
        self.__main_widget = QWidget()
        self.__backend = backend

        self.__main_widget.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        self.__main_layout = QVBoxLayout()
        self.__main_layout.setContentsMargins(0, 0, 0, 0)
        self.__main_layout.setSpacing(0)
        self.__main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.__main_widget.setLayout(self.__main_layout)

        record_diff_grid = QGridLayout()
        record_diff_grid.setColumnStretch(1, 1)
        record_diff_grid.setColumnStretch(2, 1)
        record_diff_grid.setColumnStretch(3, 1)

        self.__toggle_button = QToolButton()
        self.__toggle_button.setFixedSize(25, 25)
        self.__toggle_button.setToolButtonStyle(
            Qt.ToolButtonStyle.ToolButtonTextBesideIcon
        )
        self.__toggle_button.setStyleSheet(
            "QToolButton { border: none;"
            f"color: {self.__backend.preference.account_line_separator}; "
            "}"
        )
        self.__toggle_button.setArrowType(Qt.ArrowType.RightArrow)
        self.__toggle_button.setCheckable(True)
        self.__toggle_button.setChecked(False)
        self.__toggle_button.toggled.connect(lambda: self.__toggle())

        record_diff_grid.addWidget(self.__toggle_button, 0, 0, 2, 1)

        record_diff_grid.setContentsMargins(0, 0, 0, 0)
        record_diff_grid.setSpacing(0)

        amount_label = QLabel(
            f"{self.__backend.preference.currency.currency_text()}"
            f" {record_diff.record.balance}",
        )
        amount_label.setStyleSheet(
            f"""
                font: 16px;
                color: {self.__backend.preference.font_color};
                margin: 4px;
                """
        )

        amount_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        record_diff_grid.addWidget(amount_label, 0, 1)

        date_label = QLabel(
            record_diff.record.date.strftime("%d/%m/%Y, %H:%M")
        )
        date_label.setStyleSheet(
            f"""
                font: 16px;
                color: {self.__backend.preference.account_line_separator};
                margin: 4px;
                """
        )
        date_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        record_diff_grid.addWidget(date_label, 1, 1)

        diff_label = QLabel(
            f"{'+' if record_diff.diff > 0 else '-'}"
            f"{self.__backend.preference.currency.currency_text()}"
            f" {abs(record_diff.diff)}"
        )
        diff_label_color = (
            self.__backend.preference.expense_color
            if record_diff.diff < 0
            else self.__backend.preference.income_color
        )
        diff_label.setStyleSheet(
            f"""
                font: 16px;
                color: {diff_label_color};
                margin: 4px;
                """
        )
        diff_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        record_diff_grid.addWidget(diff_label, 0, 3)

        tag_label = QLabel(
            f"Tag: {record_diff.record.tag}" if record_diff.record.tag else ""
        )
        tag_label.setStyleSheet(
            f"""
                font: 16px;
                font-weight: lighter;
                color: {self.__backend.preference.account_line_separator};
                margin: 4px;
                """
        )
        tag_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        record_diff_grid.addWidget(tag_label, 0, 2)
        self.__main_layout.addLayout(record_diff_grid)

        detail_widget = QFrame()
        detail_widget.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        detail_widget.setStyleSheet(
            """
            background-color: #ecf0f1;
            border-radius: 4px;
            margin: 4px;
            padding: 4px;
            """
        )

        detail_vbox_layout = QVBoxLayout()
        detail_vbox_layout.setContentsMargins(0, 0, 0, 0)
        detail_vbox_layout.setSpacing(0)

        note_label = QLabel(
            record_diff.record.note
            if record_diff.record.note
            else "No Note Added"
        )

        note_label.setWordWrap(True)
        note_label.setTextFormat(Qt.TextFormat.MarkdownText)

        note_color = (
            self.__backend.preference.font_color
            if record_diff.record.note
            else self.__backend.preference.account_line_separator
        )
        note_label.setStyleSheet(
            f"""
            font: 16px;
            color: {note_color};
            margin: 4px;
            """
        )
        note_label.setSizePolicy(
            QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Expanding
        )

        detail_vbox_layout.addWidget(note_label)

        detail_widget.setLayout(detail_vbox_layout)
        detail_widget.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )

        self.__detail_collapsible = Collapsible(detail_widget, 300)

        self.__main_layout.addWidget(self.__detail_collapsible.widget)

    def __toggle(self):
        self.__toggle_button.setArrowType(
            Qt.ArrowType.DownArrow
            if self.__toggle_button.isChecked()
            else Qt.ArrowType.RightArrow
        )

        self.__detail_collapsible.toggle()

    @property
    def widget(self) -> QWidget:
        return self.__main_widget


class DayRecordLabel(Widget):
    __backend: Backend
    __date: date
    __records: list[RecordDiff]

    __day_record_widget: QWidget
    __day_record_list: QVBoxLayout

    def __init__(
        self, backend: Backend, date: date, recrods: list[RecordDiff]
    ) -> None:
        self.__date = date
        self.__records = recrods
        self.__backend = backend

        self.__day_record_widget = QWidget()
        self.__day_record_widget.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )

        self.__day_record_list = QVBoxLayout()
        self.__day_record_list.setContentsMargins(12, 12, 12, 12)

        today_datetime = datetime.today().date()

        if self.__date == today_datetime:
            date_show = "Today"
        elif self.__date == today_datetime - timedelta(days=1):
            date_show = "Yesterday"
        else:
            date_show = self.__date.strftime("%Y-%m-%d")

        date_label = QLabel(date_show)
        date_label.setStyleSheet(
            f"""
            font: 20px;
            color: {self.__backend.preference.font_color};
            padding-bottom: 4px;
            border-bottom: 1px solid
                {self.__backend.preference.account_line_separator};
            """
        )
        date_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.__day_record_list.addWidget(date_label)

        for record_diff in self.__records:
            record = RecordLabel(self.__backend, record_diff)
            self.__day_record_list.addWidget(record.widget)

        self.__day_record_widget.setLayout(self.__day_record_list)

    @property
    def widget(self) -> QWidget:
        return self.__day_record_widget


class RecordListPage(Widget):
    __backend: Backend

    __record_list_widget: QWidget
    __record_list_layout: QVBoxLayout
    __record_list_scroll: QScrollArea

    def __init__(self, backend: Backend):
        super().__init__()

        self.__backend = backend

        self.__record_list_scroll = QScrollArea()
        self.__record_list_widget = QWidget()
        self.__record_list_layout = QVBoxLayout()

        self.__record_list_layout.setSpacing(0)
        self.__record_list_layout.setContentsMargins(0, 0, 0, 0)

        self.__record_list_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        assert self.__backend.current_working_account is not None

        # TODO: add record list here bozo
        last_date: date | None = None
        record_diffs: list[RecordDiff] = []
        for record_diff in RecordIterator(
            self.__backend.current_working_account
        ):
            if (
                last_date is None
                or last_date == record_diff.record.date.date()
            ):
                last_date = record_diff.record.date.date()
                record_diffs.append(record_diff)
            else:
                self.__record_list_layout.addWidget(
                    DayRecordLabel(
                        self.__backend, last_date, record_diffs
                    ).widget
                )
                record_diffs = [record_diff]
                last_date = record_diff.record.date.date()

        if last_date is not None:
            self.__record_list_layout.addWidget(
                DayRecordLabel(self.__backend, last_date, record_diffs).widget
            )

        self.__record_list_widget.setLayout(self.__record_list_layout)
        self.__record_list_widget.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )

        self.__record_list_scroll.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )
        self.__record_list_scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.__record_list_scroll.setWidgetResizable(True)
        self.__record_list_scroll.verticalScrollBar().setStyleSheet(
            self.__backend.preference.scroll_style_sheet
        )
        self.__record_list_scroll.setWidget(self.__record_list_widget)
        # disable border
        self.__record_list_scroll.setStyleSheet(
            """
            QScrollArea {
                border: none;
            }
            """
        )

    @property
    def widget(self) -> QWidget:
        return self.__record_list_scroll


class RecordPage(Widget):
    __backend: Backend

    __account_frame: QFrame
    __page_layout: QVBoxLayout

    __new_record_button: HoveredBrightnessButton
    __current_widget: Optional[Widget]

    def __init__(self, backend: Backend):
        super().__init__()

        self.__backend = backend
        self.__current_widget = None
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
        account_label = QLabel("Records")
        account_label.setStyleSheet(
            f"""
            font: 24px;
            color: {self.__backend.preference.font_color};
            padding: 15px;
            background-color: {self.__backend.preference.generic_background_1};
            """
        )
        account_label.setAlignment(Qt.AlignmentFlag.AlignLeft)

        self.__page_layout.insertWidget(
            0,
            account_label,
        )

        # Add account page layout
        self.__show_record_page()

        drop_shadow = QGraphicsDropShadowEffect(self.__account_frame)
        drop_shadow.setBlurRadius(10)
        drop_shadow.setColor(QColor(0, 0, 0, 100))
        drop_shadow.setOffset(1, 1)

        # Add new account button
        self.__new_record_button = HoveredBrightnessButton(
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
        self.__new_record_button.setGraphicsEffect(drop_shadow)

        self.__new_record_button.clicked.connect(
            lambda: self.__create_record_button_handler()
        )

        if self.__backend.current_working_account is not None:
            self.__page_layout.addWidget(
                self.__new_record_button,
                alignment=Qt.AlignmentFlag.AlignRight,
            )

    def __show_record_page(self):
        if self.__backend.current_working_account is not None:
            widget_to_add = RecordListPage(self.__backend)
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

    @property
    def widget(self) -> QWidget:
        return self.__account_frame

    def __amount_edited_handler(self, line_edit: QLineEdit):
        color = (
            self.__backend.preference.expense_color
            if "-" in line_edit.text()
            else self.__backend.preference.income_color
            if len(line_edit.text()) > 0
            else self.__backend.preference.font_color
        )
        style = f"""
        font: 16px;
        color: {color};
        border: 0px;
        padding: 4px;
        """

        line_edit.setStyleSheet(style)

    def __create_record_button_handler(self):
        widget = QDialog(self.__account_frame)
        widget.setWindowModality(Qt.WindowModality.WindowModal)
        layout = QVBoxLayout()

        new_account_label = QLabel("New Record", parent=widget)
        new_account_label.setStyleSheet(
            f"""
            font: 16px;
            color: {self.__backend.preference.font_color};
            font-weight: bold;
            padding: 0px 8px 0px 0px;
            """
        )
        layout.addWidget(new_account_label)

        new_record_amount = QLineEdit(parent=widget)
        placeholder_text = "Amount `-` for expense"
        new_record_amount.setFixedWidth(200)
        new_record_amount.setPlaceholderText(placeholder_text)
        new_record_amount.setStyleSheet(
            f"""
            font: 16px;
            color: {self.__backend.preference.font_color};
            border: 0px;
            padding: 4px;
            """
        )
        new_record_amount.textEdited.connect(
            lambda: self.__amount_edited_handler(new_record_amount)
        )
        new_record_amount.setValidator(NumberValidator())
        layout.addWidget(new_record_amount)

        new_record_tag = QLineEdit(parent=widget)
        new_record_tag.setPlaceholderText("Tag")
        new_record_tag.setStyleSheet(
            f"""
            font: 16px;
            color: {self.__backend.preference.font_color};
            border: 0px;
            padding: 4px;
            """
        )
        layout.addWidget(new_record_tag)

        new_record_note = QTextEdit(parent=widget)
        new_record_note.setPlaceholderText("Note")
        new_record_note.setFixedHeight(100)
        new_record_note.setStyleSheet(
            f"""
            font: 16px;
            color: {self.__backend.preference.font_color};
            border: 0px;
            padding: 4px;
            """
        )
        new_record_note.verticalScrollBar().setStyleSheet(
            self.__backend.preference.scroll_style_sheet
        )
        layout.addWidget(new_record_note)

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
            lambda: self.__record_created_handler(
                new_record_amount.text(),
                new_record_note.toPlainText(),
                new_record_tag.text(),
                widget,
            )
        )
        layout.addWidget(
            new_account_button, alignment=Qt.AlignmentFlag.AlignRight
        )
        new_account_button.setGraphicsEffect(graphics_effect)

        widget.setLayout(layout)
        widget.exec()

    def __record_created_handler(
        self, amount_str: str, note: str, tag: str, dialog_widget: QDialog
    ):
        try:
            amount = Decimal(amount_str)
            dialog_widget.close()
        except Exception:
            return

        assert self.__backend.current_working_account is not None

        new_balance = (
            self.__backend.current_working_account.current_balance + amount
        )

        self.__backend.current_working_account.add_record(
            tag if len(tag) > 0 else None,
            new_balance,
            note if len(note) > 0 else None,
        )

        # refresh
        self.__show_record_page()
