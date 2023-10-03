from dataclasses import dataclass

from pymongo import database


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
    table_name = TABLE_NAME
    is_available: bool
    price: float
    take_profit: float
    stop_loss: float
    type: TradeType
    close: float
    profit: float

    def drop_table(self, database: database.Database):
        database[self.table_name].drop()

    def to_json(self):
        return {
            'is_available': self.is_available,
            'price': self.price,
            'take_profit': self.take_profit,
            'stop_loss': self.stop_loss,
            'type': self.type.value,
            'close': self.close,
            'profit': self.profit
        }

    def insert_into_database(self, database: database.Database):
        database[self.table_name].insert_one(self.to_json())
