from abc import ABC, abstractmethod
from dataclasses import dataclass

@dataclass
class SimulationConfig:
    inflation_rate: float = 0.03
    tax_rate: float = 0.30
    duration_years: int = 30

@dataclass
class Mortgage:
    principal: float
    interest_rate: float
    term_years: int

    def calculate_annual_payment(self):
        # standard amortization formula (M = P [ i(1 + i)^n ] / [ (1 + i)^n – 1])
        # simplified annual view
        r = self.interest_rate
        n = self.term_years
        if r == 0: return self.principal / n
        numerator = r * (1 + r)**n
        denominator = (1 + r)**n - 1
        return self.principal * (numerator / denominator)

    def pay_year(self):
        """
        Returns:
            tuple(float, float, float): (interest_paid, principal_paid, total_payment)
        """
        if self.principal <= 0:
            return 0, 0, 0

        annual_payment = self.calculate_annual_payment()
        interest_component = self.principal * self.interest_rate
        
        # Ensure we don't overpay the last chunk
        principal_component = annual_payment - interest_component
        if principal_component > self.principal:
            principal_component = self.principal
            annual_payment = interest_component + principal_component

        self.principal -= principal_component
        return interest_component, principal_component, annual_payment

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

class LeveragedProperty(Investment):
    def __init__(self, name, purchase_price, growth_rate, rental_yield, expenses, mortgage: Mortgage):
        super().__init__(name, purchase_price) # Initial value is full asset price
        self.growth_rate = growth_rate
        self.rental_yield = rental_yield
        self.expenses = expenses
        self.mortgage = mortgage
        self.equity = purchase_price - mortgage.principal # Track actual equity
        
    def calculate_year_financials(self):
        # 1. Asset Growth
        appreciation = self.value * self.growth_rate
        self.value += appreciation
        
        # 2. Income (Rent)
        rental_income = self.value * self.rental_yield
        
        # 3. Outflows (Expenses + Mortgage)
        interest, principal, mortgage_payment = self.mortgage.pay_year()
        total_outflow = self.expenses + mortgage_payment
        
        # 4. Net Position (Cashflow)
        # If negative, this is what you paid "out of pocket"
        net_cash_flow = rental_income - total_outflow
        
        # Update Equity (Value - Remaining Debt)
        self.equity = self.value - self.mortgage.principal
        
        return {
            'net_cash_flow': net_cash_flow,
            'interest_paid': interest,
            'principal_paid': principal,
            'appreciation': appreciation
        }