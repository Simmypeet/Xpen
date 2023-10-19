from abc import ABC, abstractmethod


class Observer(ABC):
    @abstractmethod
    def response(self, message: object) -> None:
        pass


class Subject(ABC):
    """
    Represents a subject in the observer pattern.
    """

    __observers: list[Observer]

    def __init__(self) -> None:
        self.__observers = []

    def attach(self, observer: Observer) -> None:
        self.__observers.append(observer)

    def detach(self, observer: Observer) -> None:
        self.__observers.remove(observer)

    def notify(self, message: object) -> None:
        for observer in self.__observers:
            observer.response(message)
