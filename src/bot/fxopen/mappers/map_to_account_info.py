from dataclasses import dataclass
from typing import Any, Literal


@dataclass
class AccountInfo:
    balance: float
    equity: float


@dataclass
class FxOpenGetAccountResponse:
    Id: int
    AccountingType: Literal['Gross' 'Net' 'Cash']
    Name: str
    FirstName: str
    LastName: str
    Phone: str
    Country: str
    State: str
    City: str
    Address: str
    ZipCode: str
    SocialSecurityNumber: str
    Email: str
    Comment: str
    Registered: int  # timestamp
    Modified: int  # timestamp
    IsArchived: bool
    IsBlocked: bool
    IsReadonly: bool
    IsValid: bool
    IsWebApiEnabled: bool
    Leverage: int
    Balance: float
    BalanceCurrency: str
    Profit: float
    Commission: float
    AgentCommission: float
    Swap: float
    Rebate: float
    Equity: float
    Margin: float
    MarginLevel: float
    MarginCallLevel: int
    StopOutLevel: int
    ReportCurrency: str
    TokenCommissionCurrency: str
    TokenCommissionCurrencyDiscount: float
    IsTokenCommissionEnabled: bool
    MaxOverdraftAmount: float
    OverdraftCurrency: str
    UsedOverdraftAmount: float
    Throttling: Any
    IsLongOnly: bool

    def __getitem__(self, key):
        return getattr(self, key)


def map_to_account_info(account: FxOpenGetAccountResponse) -> AccountInfo:
    return AccountInfo(
        balance=account['Balance'],
        equity=account['Equity']
    )
