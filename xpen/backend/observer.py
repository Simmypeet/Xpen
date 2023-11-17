from __future__ import annotations
from abc import ABC, abstractmethod


class Subject(ABC):
    """A subject which observers can subscribe to."""

    __observers: list[Observer]

    def __init__(self) -> None:
        self.__observers = []

    def _notify(self, message: object) -> None:
        """Notifies all the subscribed with the given message.

        Args:
            message (object): The message to pass to along to the observers.
        """
        for observer in self.__observers:
            observer._response(message)  # type: ignore


class Observer(ABC):
    """An observer which can subscribe to a subject."""

    @abstractmethod
    def _response(self, message: object) -> None:
        raise NotImplementedError()

    def subscribe(self, sub: Subject) -> None:
        """Subscribes to the given subject.

        Args:
            sub (Subject): The subject to subscribe to.
        """
        if self not in sub._Subject__observers:  # type: ignore
            sub._Subject__observers.append(self)  # type: ignore

    def unsubscribe(self, sub: Subject) -> bool:
        """Unsubscribes from the given subject.

        Args:
            sub (Subject): The subject to unsubscribe from.

        Returns:
            bool: True if the observer was subscribed to the subject,
                False, otherwise.
        """
        if self in sub._Subject__observers:  # type: ignore
            sub._Subject__observers.remove(self)  # type: ignore
            return True

        return False
