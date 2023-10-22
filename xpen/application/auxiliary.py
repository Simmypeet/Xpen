from typing import Final, Optional

from application.widget import Widget
from backend import Backend
from PySide6.QtCore import (
    QEvent,
    QSize,
    Qt,
    QParallelAnimationGroup,
    QAbstractAnimation,
    QPropertyAnimation,
    QEasingCurve,
)
from PySide6.QtGui import (
    QColor,
    QEnterEvent,
    QIcon,
    QPainter,
    QPixmap,
)
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import (
    QPushButton,
    QWidget,
    QVBoxLayout,
    QLabel,
    QSizePolicy,
)


class HoveredBrightnessButton(QPushButton):
    __icon_svg: QSvgRenderer
    __button_size: QSize
    __icon_size_factor: float
    __hover_icon_size_factor: float

    NORMAL_OPACITY: Final[float] = 0.75
    HOVERED_OPACITY: Final[float] = 1.25

    def __init__(
        self,
        icon_svg: QSvgRenderer,
        button_size: QSize,
        style: str = "background-color: transparent; border: 0px;",
        icon_size_factor: float = 0.5,
        hover_icon_size_factor: float = 1.3,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.__button_size = button_size
        self.__icon_svg = icon_svg
        self.__icon_size_factor = icon_size_factor
        self.__hover_icon_size_factor = hover_icon_size_factor
        self.setIconSize(button_size * self.__icon_size_factor)
        self.setFixedSize(button_size)
        self.setFlat(True)
        self.setStyleSheet(style)
        self.setIcon(
            self.__create_icon(HoveredBrightnessButton.NORMAL_OPACITY)
        )

    def enterEvent(self, event: QEnterEvent) -> None:
        self.setIconSize(
            self.__button_size
            * self.__icon_size_factor
            * self.__hover_icon_size_factor
        )
        self.setIcon(
            self.__create_icon(HoveredBrightnessButton.HOVERED_OPACITY)
        )
        return super().enterEvent(event)

    def leaveEvent(self, event: QEvent) -> None:
        self.setIconSize(self.__button_size * self.__icon_size_factor)
        self.setIcon(
            self.__create_icon(HoveredBrightnessButton.NORMAL_OPACITY)
        )
        return super().leaveEvent(event)

    def __create_icon(self, brightness_factor: float) -> QIcon:
        pixmap = QPixmap(self.__button_size)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setOpacity(brightness_factor)
        self.__icon_svg.render(painter)
        painter.setCompositionMode(
            painter.CompositionMode.CompositionMode_SourceIn
        )
        painter.fillRect(pixmap.rect(), QColor(0, 0, 0, 255))
        painter.end()
        return QIcon(pixmap)


class NoAccountPage(Widget):
    """
    A page shown when no account is found or no account is selected.
    """

    __widget: QWidget
    __backend: Backend

    __no_account_layout: QVBoxLayout

    def __init__(self, backend: Backend):
        self.__widget = QWidget()
        self.__backend = backend

        self.__no_account_layout = QVBoxLayout()
        self.__no_account_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # show no account page and prompt user to create one
        pixmap = QPixmap(QSize(50, 50))
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        self.__backend.resource.account_not_found_symol.render(painter)
        painter.setCompositionMode(
            painter.CompositionMode.CompositionMode_SourceIn
        )
        painter.fillRect(
            pixmap.rect(), QColor(self.__backend.preference.font_color)
        )
        painter.end()

        no_account_symbol = QLabel()
        no_account_symbol.setPixmap(pixmap)
        no_account_symbol.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.__no_account_layout.addWidget(no_account_symbol)

        no_account_text = QLabel(
            "No Accounts Found\n\nSelect or Create New One to Start"
        )
        no_account_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        no_account_text.setStyleSheet(
            f"""
            font: 16px;
            color: {self.__backend.preference.font_color};
            """
        )

        self.__no_account_layout.addWidget(no_account_text)
        self.__no_account_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.__widget.setLayout(self.__no_account_layout)

        self.__widget.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )

    @property
    def widget(self) -> QWidget:
        return self.__widget


class Collapsible(Widget):
    __content_area: QWidget

    __animation_duration: int
    __expanded: bool

    def __init__(
        self,
        content: QWidget,
        animation_duration: int = 300,
    ) -> None:
        super().__init__()

        self.__animation_duration = animation_duration
        self.__content_area = content
        self.__expanded = False

        # Let the entire widget grow and shrink with its content
        self.__toggle_animation = QParallelAnimationGroup(self.__content_area)
        # Don't waste space

        self.__set_content_layout()

    def toggle(self) -> None:
        self.__toggle_animation.setDirection(
            QAbstractAnimation.Direction.Backward
            if self.__expanded
            else QAbstractAnimation.Direction.Forward
        )
        self.__toggle_animation.start()

        self.__expanded = not self.__expanded

    def __set_content_layout(self) -> None:
        content_animation = QPropertyAnimation(
            self.__content_area, b"maximumHeight"
        )
        content_animation.setStartValue(0)
        content_animation.setEasingCurve(QEasingCurve.Type.InOutQuart)
        content_animation.setDuration(self.__animation_duration)
        content_animation.setEndValue(self.__content_area.sizeHint().height())
        self.__toggle_animation.addAnimation(content_animation)
        self.__content_area.setMaximumHeight(0)

    @property
    def widget(self) -> QWidget:
        return self.__content_area
