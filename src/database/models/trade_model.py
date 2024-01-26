from dataclasses import dataclass
from database.instance import MongoDB


TABLE_NAME = 'trades'


class TradeType:
    BUY = 'buy'
    SELL = 'sell'
    value: str

    def __init__(self, type: str):
        if type != self.BUY and type != self.SELL:
            raise Exception(
                'Invalid trade type {type}, must be either {self.BUY} or {self.SELL}')
        self.value = type


@dataclass
class TradeModel:
    is_closed: bool
    price: float
    position_value: float
    take_profit: float
    stop_loss: float
    type: TradeType
    close: float
    profit: float
    fxopen_id: str
    opened_at: str
    closed_at: str

    @staticmethod
    def findTradesByDate(start_date: str, end_date: str):
        return list(map(lambda trade: TradeModel(
            is_closed=trade['is_closed'],
            price=trade['price'],
            position_value=trade['position_value'],
            take_profit=trade['take_profit'],
            stop_loss=trade['stop_loss'],
            type=TradeType(trade['type']),
            close=trade['close'],
            profit=trade['profit'],
            fxopen_id=trade['fxopen_id'],
            opened_at=trade['opened_at'],
            closed_at=trade['closed_at']
        ), list(MongoDB.database[TABLE_NAME].find({'opened_at': {'$gte': start_date, '$lt': end_date}}))))

    @staticmethod
    def findAll():
        return list(map(lambda trade: TradeModel(
            is_closed=trade['is_closed'],
            price=trade['price'],
            position_value=trade['position_value'],
            take_profit=trade['take_profit'],
            stop_loss=trade['stop_loss'],
            type=TradeType(trade['type']),
            close=trade['close'],
            profit=trade['profit'],
            fxopen_id=trade['fxopen_id'],
            opened_at=trade['opened_at'],
            closed_at=trade['closed_at']
        ), list(MongoDB.database[TABLE_NAME].find())))

    @staticmethod
    def findLast():
        return list(map(lambda trade: TradeModel(
            is_closed=trade['is_closed'],
            price=trade['price'],
            position_value=trade['position_value'],
            take_profit=trade['take_profit'],
            stop_loss=trade['stop_loss'],
            type=TradeType(trade['type']),
            close=trade['close'],
            profit=trade['profit'],
            fxopen_id=trade['fxopen_id'],
            opened_at=trade['opened_at'],
            closed_at=trade['closed_at']
        ), list(MongoDB.database[TABLE_NAME].find().sort('opened_at', -1).limit(1))))[0]

    @staticmethod
    def drop_table():
        MongoDB.database[TABLE_NAME].drop()

    def to_json(self):
        return {
            'is_closed': self.is_closed,
            'price': self.price,
            'position_value': self.position_value,
            'take_profit': self.take_profit,
            'stop_loss': self.stop_loss,
            'type': self.type.value,
            'close': self.close,
            'profit': self.profit,
            'fxopen_id': self.fxopen_id,
            'opened_at': self.opened_at,
            'closed_at': self.closed_at
        }

    def insert_into_database(self):
        MongoDB.database[TABLE_NAME].insert_one(self.to_json())
