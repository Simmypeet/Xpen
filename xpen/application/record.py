from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Optional

from application.auxiliary import (
    Collapsible,
    HoveredBrightnessButton,
    Page,
)
from application.widget import Widget
from application.filter import Filter
from backend import Backend
from backend.account import RecordDiff, RecordCursor, LatestPosition
from PySide6.QtCore import QSize, Qt
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtGui import QColor, QValidator
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QFrame,
    QGraphicsDropShadowEffect,
    QGridLayout,
    QLabel,
    QLineEdit,
    QScrollArea,
    QSizePolicy,
    QTextEdit,
    QToolButton,
    QVBoxLayout,
    QWidget,
)


class _NumberValidator(QValidator):
    def validate(
        self, arg__1: str, arg__2: int
    ) -> tuple[QValidator.State, str, int]:
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


class _RecordLabel(Widget):
    __backend: Backend
    __main_widget: QWidget
    __main_layout: QVBoxLayout
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
            f"color: {self.__backend.preference.light_gray_color}; "
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
                color: {self.__backend.preference.black_color};
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
                color: {self.__backend.preference.light_gray_color};
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
            self.__backend.preference.red_color
            if record_diff.diff < 0
            else self.__backend.preference.green_color
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
            color: {self.__backend.preference.light_gray_color};
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
            self.__backend.preference.black_color
            if record_diff.record.note
            else self.__backend.preference.light_gray_color
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

    def __toggle(self) -> None:
        self.__toggle_button.setArrowType(
            Qt.ArrowType.DownArrow
            if self.__toggle_button.isChecked()
            else Qt.ArrowType.RightArrow
        )

        self.__detail_collapsible.toggle()

    @property
    def widget(self) -> QWidget:
        return self.__main_widget


class _DayRecordLabel(Widget):
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
            color: {self.__backend.preference.black_color};
            padding-bottom: 4px;
            border-bottom: 1px solid
                {self.__backend.preference.light_gray_color};
            """
        )
        date_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.__day_record_list.addWidget(date_label)

        for record_diff in self.__records:
            record = _RecordLabel(self.__backend, record_diff)
            self.__day_record_list.addWidget(record.widget)

        self.__day_record_widget.setLayout(self.__day_record_list)

    @property
    def widget(self) -> QWidget:
        return self.__day_record_widget


class _RecordList(Widget):
    __backend: Backend

    __record_list_widget: QWidget
    __record_list_layout: QVBoxLayout
    __record_list_scroll: QScrollArea

    __filter: Filter

    def __init__(self, backend: Backend, filter: Filter) -> None:
        super().__init__()

        self.__backend = backend
        self.__filter = filter

        self.__record_list_scroll = QScrollArea()
        self.__record_list_widget = QWidget()
        self.__record_list_layout = QVBoxLayout()

        self.__record_list_layout.setSpacing(0)
        self.__record_list_layout.setContentsMargins(0, 0, 0, 0)

        self.__record_list_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        assert self.__backend.current_working_account is not None

        last_date: date | None = None
        record_diffs: list[RecordDiff] = []
        cursor = RecordCursor(
            self.__backend.current_working_account, LatestPosition()
        )

        while True:
            record_diff = cursor.previous()
            if record_diff is None:
                break

            if (
                last_date is None
                or last_date == record_diff.record.date.date()
            ):
                if self.__filter.filter(record_diff):
                    last_date = record_diff.record.date.date()
                    record_diffs.append(record_diff)
            else:
                if len(record_diffs) > 0:
                    self.__record_list_layout.addWidget(
                        _DayRecordLabel(
                            self.__backend, last_date, record_diffs
                        ).widget
                    )
                    record_diffs.clear()

                if self.__filter.filter(record_diff):
                    record_diffs.append(record_diff)
                    last_date = record_diff.record.date.date()

        if last_date is not None and len(record_diffs) > 0:
            self.__record_list_layout.addWidget(
                _DayRecordLabel(self.__backend, last_date, record_diffs).widget
            )

        self.__record_list_widget.setLayout(self.__record_list_layout)
        self.__record_list_widget.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.MinimumExpanding
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

        self.__record_list_scroll.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )

    @property
    def widget(self) -> QWidget:
        return self.__record_list_scroll


class _Content(Widget):
    __backend: Backend
    __main_layout: QVBoxLayout
    __main_widget: QWidget
    __record_list: _RecordList
    __new_record_button: HoveredBrightnessButton
    __filter_button: HoveredBrightnessButton
    __filter: Filter

    def __init__(
        self, backend: Backend, default_filter: Optional[Filter]
    ) -> None:
        self.__backend = backend

        self.__main_widget = QWidget()
        if default_filter is not None:
            self.__filter = default_filter
        else:
            self.__filter = Filter()

        self.__main_layout = QVBoxLayout()
        self.__main_layout.setContentsMargins(0, 0, 0, 0)
        self.__main_layout.setSpacing(0)
        self.__main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.__main_widget.setLayout(self.__main_layout)

        self.__record_list = _RecordList(self.__backend, self.__filter)
        self.__main_layout.addWidget(self.__record_list.widget)

        button_hbox_layout = QHBoxLayout()
        button_hbox_layout.setContentsMargins(0, 0, 0, 0)
        button_hbox_layout.setSpacing(0)
        button_hbox_layout.setAlignment(Qt.AlignmentFlag.AlignRight)
        button_hbox_layout.setDirection(QHBoxLayout.Direction.RightToLeft)

        def create_button(svg_icon: QSvgRenderer) -> HoveredBrightnessButton:
            drop_shadow = QGraphicsDropShadowEffect(self.__main_widget)
            drop_shadow.setBlurRadius(10)
            drop_shadow.setColor(QColor(0, 0, 0, 100))
            drop_shadow.setOffset(1, 1)

            button = HoveredBrightnessButton(
                svg_icon,
                QSize(50, 50),
                f"""
                background-color: {self.__backend.preference.teal_green_color};
                border-radius: 21px;
                margin: 4px;
                """,
                icon_size_factor=0.3,
                hover_icon_size_factor=1.2,
            )

            button.setGraphicsEffect(drop_shadow)

            return button

        # Add new account button
        self.__new_record_button = create_button(
            self.__backend.resource.new_account_symbol
        )
        self.__new_record_button.clicked.connect(
            lambda: self.__create_record_button_handler()
        )
        button_hbox_layout.addWidget(self.__new_record_button)

        self.__filter_button = create_button(
            self.__backend.resource.filter_symbol
        )
        self.__filter_button.clicked.connect(
            lambda: Filter.show_propmt_dialog(
                self.__backend.preference,
                self.__main_widget,
                self.__filter,
                lambda filter: self.__filter_updated(filter),
            )
        )
        button_hbox_layout.addWidget(self.__filter_button)

        self.__main_layout.addLayout(button_hbox_layout)

    def __filter_updated(self, new_filter: Filter) -> None:
        self.__filter = new_filter
        self.__refresh_record_list()

    def __refresh_record_list(self) -> None:
        new_record_list = _RecordList(self.__backend, self.__filter)
        self.__main_layout.replaceWidget(
            self.__record_list.widget, new_record_list.widget
        )
        self.__record_list = new_record_list

    def __create_record_button_handler(self):
        widget = QDialog(self.__main_widget)
        widget.setWindowModality(Qt.WindowModality.WindowModal)
        layout = QVBoxLayout()

        new_account_label = QLabel("New Record", parent=widget)
        new_account_label.setStyleSheet(
            self.__backend.preference.dialog_prompt_header_style
        )
        layout.addWidget(new_account_label)

        new_record_amount = QLineEdit(parent=widget)
        placeholder_text = "Amount `-` for expense"
        new_record_amount.setFixedWidth(200)
        new_record_amount.setPlaceholderText(placeholder_text)
        new_record_amount.setStyleSheet(
            self.__backend.preference.dialog_line_edit_style()
        )
        new_record_amount.textEdited.connect(
            lambda: self.__amount_edited_handler(new_record_amount)
        )
        new_record_amount.setValidator(_NumberValidator())
        layout.addWidget(new_record_amount)

        new_record_tag = QLineEdit(parent=widget)
        new_record_tag.setPlaceholderText("Tag")
        new_record_tag.setStyleSheet(
            self.__backend.preference.dialog_line_edit_style()
        )
        layout.addWidget(new_record_tag)

        new_record_note = QTextEdit(parent=widget)
        new_record_note.setPlaceholderText("Note")
        new_record_note.setFixedHeight(100)
        new_record_note.setStyleSheet(
            self.__backend.preference.dialog_line_edit_style()
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
            background-color: {self.__backend.preference.teal_green_color};
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

    def __amount_edited_handler(self, line_edit: QLineEdit) -> None:
        color = (
            self.__backend.preference.red_color
            if "-" in line_edit.text()
            else self.__backend.preference.green_color
            if len(line_edit.text()) > 0
            else self.__backend.preference.black_color
        )

        line_edit.setStyleSheet(
            self.__backend.preference.dialog_line_edit_style(color)
        )

    def __record_created_handler(
        self, amount_str: str, note: str, tag: str, dialog_widget: QDialog
    ) -> None:
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

        self.__refresh_record_list()

    @property
    def widget(self) -> QWidget:
        return self.__main_widget


class RecordPage(Page):
    def __init__(
        self, backend: Backend, default_filter: Optional[Filter]
    ) -> None:
        super().__init__(backend, "Records", _Content(backend, default_filter))
