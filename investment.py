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

class ETFInvestment(Investment):
    def __init__(self, name, initial_value, annual_return_rate, mer_fee):
        super().__init__(name, initial_value)
        self.rate = annual_return_rate
        self.mer_fee = mer_fee

    def calculate_annual_return(self):
        # standard compounds interest
        growth = self.value * self.rate
        self.value += growth
        return growth

    def apply_costs(self):
        # management expense ratio (MER)
        cost = self.value *self.mer_fee
        self.value -= cost
        return cost

