from abc import ABC, abstractmethod
from dataclasses import dataclass

# --- 1. CONFIGURATION ---
@dataclass
class SimulationConfig:
    inflation_rate: float = 0.03
    marginal_tax_rate: float = 0.37    # For negative gearing refunds
    capital_gains_tax_discount: float = 0.50
    stamp_duty_rate: float = 0.04      # approx 4% of property value
    closing_costs: float = 3000        # Conveyancing, misc fees

# --- 2. DATA STRUCTURES ---
@dataclass
class Mortgage:
    principal: float
    interest_rate: float
    term_years: int
    offset_balance: float = 0.0

    def calculate_annual_payment(self):
        # Standard Amortization Formula
        r = self.interest_rate
        n = self.term_years
        if r == 0: return self.principal / n
        numerator = r * (1 + r)**n
        denominator = (1 + r)**n - 1
        return self.principal * (numerator / denominator)

    def pay_year(self):
        """Returns (interest_paid, principal_paid, total_payment)"""
        if self.principal <= 0:
            return 0, 0, 0
            
        annual_payment = self.calculate_annual_payment()
        
        # Interest is calculated on (Principal - Offset)
        effective_principal = max(0, self.principal - self.offset_balance)
        interest_component = effective_principal * self.interest_rate
        
        # The rest goes to principal
        principal_component = annual_payment - interest_component
        
        # Handle end of loan logic
        if principal_component > self.principal:
            principal_component = self.principal
            annual_payment = interest_component + principal_component

        self.principal -= principal_component
        return interest_component, principal_component, annual_payment

# --- 3. BASE CLASS ---
class Investment(ABC):
    def __init__(self, name, initial_value, config: SimulationConfig):
        self.name = name
        self.value = initial_value
        self.config = config
        self.history = []

    @abstractmethod
    def calculate_annual_return(self):
        pass

    @abstractmethod
    def apply_costs(self):
        pass
    
    def log_status(self, year, extra_data=None):
        data = {'year': year, 'value': self.value}
        if extra_data:
            data.update(extra_data)
        self.history.append(data)

class ETFInvestment(Investment):
    def __init__(self, name, initial_cash, annual_return, mer_fee, config):
        super().__init__(name, initial_cash, config)
        self.rate = annual_return
        self.mer = mer_fee

    def invest_cash(self, amount):
        """Inject 'opportunity cost' capital."""
        self.value += amount

    def calculate_annual_return(self):
        growth = self.value * self.rate
        self.value += growth
        return growth

    def apply_costs(self):
        cost = self.value * self.mer
        self.value -= cost
        return cost

class LeveragedProperty(Investment):
    def __init__(self, name, purchase_price, growth_rate, rental_yield, expenses, mortgage: Mortgage, config):
        super().__init__(name, purchase_price, config)
        self.growth_rate = growth_rate
        self.rental_yield = rental_yield
        self.expenses = expenses
        self.mortgage = mortgage
        # Track equity separately: Value - Debt + Offset Cash
        self.equity = purchase_price - mortgage.principal 

    def calculate_annual_return(self):
        # 1. Capital Growth (Compounding on total asset value)
        appreciation = self.value * self.growth_rate
        self.value += appreciation
        return appreciation

    def apply_costs(self):
        # 1. Calculate Rent (Rent grows with asset value)
        rental_income = self.value * self.rental_yield
        
        # 2. Expenses (Expenses grow with inflation)
        # We assume expenses increase by inflation relative to the *start* of the sim, 
        # or simplify and just inflate current expenses. Let's inflate current.
        self.expenses *= (1 + self.config.inflation_rate)
        
        # 3. Mortgage
        interest, principal, mortgage_payment = self.mortgage.pay_year()
        
        # 4. Tax Logic (Negative Gearing)
        # Taxable Loss = Rent - Interest - Expenses (Principal is NOT tax deductible)
        taxable_income = rental_income - interest - self.expenses
        
        tax_refund = 0
        tax_paid = 0
        
        if taxable_income < 0:
            # We lost money on paper -> Get tax refund
            tax_refund = abs(taxable_income) * self.config.marginal_tax_rate
        else:
            # We made profit -> Pay tax
            tax_paid = taxable_income * self.config.marginal_tax_rate

        # 5. Cash Flow Calculation
        # Actual cash in/out = Rent + Refund - Expenses - MortgagePayment - TaxPaid
        net_cash_flow = rental_income + tax_refund - self.expenses - mortgage_payment - tax_paid

        # 6. Handling the Cash Flow
        if net_cash_flow > 0:
            # POSITIVE: Put it in the offset account to save interest next year
            self.mortgage.offset_balance += net_cash_flow
            out_of_pocket = 0
        else:
            # NEGATIVE: The investor had to pay this from their salary
            out_of_pocket = abs(net_cash_flow)

        # Recalculate Equity (Asset + Offset - Debt)
        self.equity = self.value + self.mortgage.offset_balance - self.mortgage.principal
        
        return out_of_pocket  # This is the number needed for the ETF comparison