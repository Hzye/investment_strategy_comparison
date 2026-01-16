from abc import ABC, abstractmethod
from dataclasses import dataclass

class Investment(ABC):
    def __init__(self, name: str, initial_value: float):
        self.name = name
        self.value = initial_value
        self.history = []

    @abstractmethod
    def calculate_annual_return(self):
        pass

    @abstractmethod
    def apply_costs(self):
        pass

    def log_status(self, year):
        self.history.append({"year": year, "value": self.value})