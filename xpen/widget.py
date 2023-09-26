from PySide6.QtGui import QPainter, QPixmap, QIcon
from PySide6.QtWidgets import QPushButton, QWidget
from PySide6.QtCore import Qt, QSize, QEvent
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtGui import QEnterEvent, QColor

from typing import Final


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
        parent: QWidget | None = None,
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
        self.setIcon(self.__create_icon(HoveredBrightnessButton.NORMAL_OPACITY))

    def enterEvent(self, event: QEnterEvent) -> None:
        self.setIconSize(
            self.__button_size * self.__icon_size_factor * self.__hover_icon_size_factor
        )
        self.setIcon(self.__create_icon(HoveredBrightnessButton.HOVERED_OPACITY))
        return super().enterEvent(event)

    def leaveEvent(self, event: QEvent) -> None:
        self.setIconSize(self.__button_size * self.__icon_size_factor)
        self.setIcon(self.__create_icon(HoveredBrightnessButton.NORMAL_OPACITY))
        return super().leaveEvent(event)

    def __create_icon(self, brightness_factor: float) -> QIcon:
        pixmap = QPixmap(self.__button_size)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setOpacity(brightness_factor)
        self.__icon_svg.render(painter)
        painter.setCompositionMode(painter.CompositionMode.CompositionMode_SourceIn)
        painter.fillRect(pixmap.rect(), QColor(0, 0, 0, 255))
        painter.end()
        return QIcon(pixmap)
