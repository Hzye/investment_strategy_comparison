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
    
    def __post_init__(self):
        # Calculate FIXED annual payment once (standard P&I)
        r = self.interest_rate
        n = self.term_years
        self.annual_payment = self.principal * (r * (1 + r)**n) / ((1 + r)**n - 1)

    def pay_year(self):
        if self.principal <= 0:
            return 0, 0, 0
            
        interest_for_year = self.principal * self.interest_rate
        principal_for_year = self.annual_payment - interest_for_year
        
        # Prevent negative balance
        if principal_for_year > self.principal:
            principal_for_year = self.principal
            
        self.principal -= principal_for_year
        return interest_for_year, principal_for_year, self.annual_payment

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
            # 1. Rent (4% yield on CURRENT value)
            rental_income = self.value * self.rental_yield
            
            # 2. Mortgage Step
            interest, principal_paid, total_mortgage_payment = self.mortgage.pay_year()

            self.total_mortgage_payment = total_mortgage_payment
            
            # 3. Expenses (Maintenance/Rates)
            # Assuming expenses are approx 1% of property value per year
            current_expenses = self.expenses * (1 + self.config.inflation_rate)
            self.expenses = current_expenses 
            
            # 4. Taxable Position (For Negative Gearing)
            taxable_profit_loss = rental_income - interest - current_expenses
            
            tax_impact = 0
            if taxable_profit_loss < 0:
                # Tax Refund (Negative Gearing)
                tax_impact = abs(taxable_profit_loss) * self.config.marginal_tax_rate
            else:
                # Tax Paid on Profit
                tax_impact = -(taxable_profit_loss * self.config.marginal_tax_rate)

            # 5. Net Cash Flow
            # (Income + Refund) - (Mortgage + Expenses)
            net_cash_flow = (rental_income + tax_impact) - (total_mortgage_payment + current_expenses)
            
            # 6. Update Equity: Current Value minus what is left on the loan
            self.equity = self.value - self.mortgage.principal
            
            # Return out_of_pocket (only the negative part)
            return abs(net_cash_flow) if net_cash_flow < 0 else 0