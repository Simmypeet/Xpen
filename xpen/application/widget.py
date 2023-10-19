from abc import ABC, abstractmethod
from PySide6.QtWidgets import QWidget


class Widget(ABC):
    """
    Abstract class that has a widget property.

    This is a workaround that `QWidget` can't be derived with `abc.ABC`.
    """

    @property
    @abstractmethod
    def widget(self) -> QWidget:
        pass
