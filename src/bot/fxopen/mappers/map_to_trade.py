from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Literal

from bson import ObjectId
from database.models.trade_model import TradeModel, TradeType


@dataclass
class FxOpenGetTradeByIdResponse:
    Id: int
    ClientId: str
    AccountId: int
    Type: Literal['Market']
    InitialType: Literal['Market']
    Side: Literal['Buy' 'Sell']
    Status: Literal['New', 'Calculated', 'Filled', 'Canceled', 'Rejected', 'Expired',
                    'PartiallyFilled', 'Activated', 'Executing', 'Invalid']  # 'New' received
    Symbol: str
    SymbolPrecision: int
    StopPrice: float
    Price: float
    CurrentPrice: float
    InitialAmount: int
    RemainingAmount: int
    FilledAmount: int
    MaxVisibleAmount: int
    StopLoss: float
    TakeProfit: float
    Margin: float
    Profit: float
    Commission: float
    AgentCommission: float
    Swap: float
    ImmediateOrCancel: bool
    MarketWithSlippage: bool
    FillOrKill: bool
    OneCancelsTheOther: bool
    Created: int  # Timestamp
    Expired: int  # Timestamp
    Modified: int  # Timestamp
    Filled: int  # Timestamp
    PositionCreated: int  # Timestamp
    Comment: str
    ClientApp: str
    Slippage: float
    Rebate: float
    RelatedTradeId: int
    ContingentOrder: bool
    TriggerType: str
    TriggerTime: int
    OrderIdTriggeredBy: int

    def __getitem__(self, key):
        return getattr(self, key)


def map_to_trade(trade: FxOpenGetTradeByIdResponse) -> TradeModel:
    print('received trade by id : ', trade)
    created_timestamp = trade['Created']
    created_date = datetime.fromtimestamp(
        created_timestamp / 1000, tz=timezone.utc).isoformat()
    remaining_amount = trade['RemainingAmount']
    status = trade['Status']
    is_closed = False
    closed_at = ''
    if (remaining_amount == 0 or status == 'Canceled' or status == 'Rejected' or status == 'Expired' or status == 'Invalid'):
        is_closed = True
        closed_at = datetime.fromtimestamp(
            trade['Modified'] / 1000, tz=timezone.utc).isoformat()
    return TradeModel(
        _id=trade["Comment"], status=status,
        is_closed=is_closed, price=trade['Price'], position_value=trade['InitialAmount'],
        take_profit=trade['TakeProfit'], stop_loss=trade['StopLoss'], type=TradeType(trade['Side']), close=0, profit=trade['Profit'], fxopen_id=trade['Id'], opened_at_timestamp=created_timestamp, opened_at=created_date, closed_at=closed_at
    )
