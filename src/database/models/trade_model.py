from dataclasses import dataclass
from typing import Literal

from bson import ObjectId
from database.instance import MongoDB


TABLE_NAME = 'trades'

TradeTypeValues = Literal['Buy', 'Sell']
DeviseValues = Literal['EURUSD', 'BTCUSD']


class DeviseType:
    EURUSD = 'EURUSD'
    BTCUSD = 'BTCUSD'
    value: DeviseValues

    def __init__(self, devise: str):
        if devise != self.EURUSD and devise != self.BTCUSD:
            raise Exception(
                'Invalid devise {devise}, must be either {self.EURUSD} or {self.BTCUSD}')
        self.value = devise


class TradeType:
    BUY = 'Buy'
    SELL = 'Sell'
    value: TradeTypeValues

    def __init__(self, type: TradeTypeValues):
        if type != self.BUY and type != self.SELL:
            raise Exception(
                'Invalid trade type {type}, must be either {self.BUY} or {self.SELL}')
        self.value = type


@dataclass
class TradeModel:
    _id: ObjectId
    is_closed: bool
    price: float
    status: Literal['New', 'Calculated', 'Filled', 'Canceled', 'Rejected',
                    'Expired', 'PartiallyFilled', 'Activated', 'Executing', 'Invalid']
    devise: DeviseValues
    position_value: str
    take_profit: float
    stop_loss: float
    type: TradeType
    close: float
    profit: str
    comission: float
    fxopen_id: str
    opened_at_timestamp: int
    opened_at: str
    closed_at: str

    @staticmethod
    def findTradesByDate(start_date: str, end_date: str):
        return list(map(lambda trade: TradeModel(
            _id=trade['_id'],
            is_closed=trade['is_closed'],
            price=trade['price'],
            status=trade['status'],
            devise=trade['devise'],
            position_value=trade['position_value'],
            take_profit=trade['take_profit'],
            stop_loss=trade['stop_loss'],
            type=TradeType(trade['type']),
            close=trade['close'],
            profit=trade['profit'],
            comission=trade['comission'],
            fxopen_id=trade['fxopen_id'],
            opened_at_timestamp=trade['opened_at_timestamp'],
            opened_at=trade['opened_at'],
            closed_at=trade['closed_at']
        ), list(MongoDB.database[TABLE_NAME].find({'opened_at': {'$gte': start_date, '$lt': end_date}}))))

    @staticmethod
    def findAll():
        return list(map(lambda trade: TradeModel(
            _id=trade['_id'],
            is_closed=trade['is_closed'],
            price=trade['price'],
            status=trade['status'],
            devise=trade['devise'],
            position_value=trade['position_value'],
            take_profit=trade['take_profit'],
            stop_loss=trade['stop_loss'],
            type=TradeType(trade['type']),
            close=trade['close'],
            profit=trade['profit'],
            comission=trade['comission'],
            fxopen_id=trade['fxopen_id'],
            opened_at_timestamp=trade['opened_at_timestamp'],
            opened_at=trade['opened_at'],
            closed_at=trade['closed_at']
        ), list(MongoDB.database[TABLE_NAME].find())))

    @staticmethod
    def findLast(type: TradeTypeValues | None, devise: DeviseValues | None):
        if (devise != None and type != None):
            tradeList = list(MongoDB.database[TABLE_NAME].find(
                {'devise': devise, 'type': type}).sort('opened_at', -1).limit(1))
        elif (devise == None and type != None):
            tradeList = list(MongoDB.database[TABLE_NAME].find(
                {'type': type}).sort('opened_at', -1).limit(1))
        elif (devise != None and type == None):
            tradeList = list(MongoDB.database[TABLE_NAME].find(
                {'devise': devise}).sort('opened_at', -1).limit(1))
        else:
            tradeList = list(MongoDB.database[TABLE_NAME].find().sort(
                'opened_at', -1).limit(1))

        if (len(tradeList) == 0):
            return None

        trade = tradeList[0]

        return TradeModel(
            _id=trade['_id'],
            is_closed=trade['is_closed'],
            price=trade['price'],
            status=trade['status'],
            devise=trade['devise'],
            position_value=trade['position_value'],
            take_profit=trade['take_profit'],
            stop_loss=trade['stop_loss'],
            type=TradeType(trade['type']),
            close=trade['close'],
            profit=trade['profit'],
            comission=trade['comission'],
            fxopen_id=trade['fxopen_id'],
            opened_at_timestamp=trade['opened_at_timestamp'],
            opened_at=trade['opened_at'],
            closed_at=trade['closed_at']
        )

    @staticmethod
    def drop_table():
        MongoDB.database[TABLE_NAME].drop()

    def to_json(self, for_database: bool = False):
        return {
            "_id": self._id if for_database == True else str(self._id),
            'is_closed': self.is_closed,
            'price': self.price,
            'status': self.status,
            'devise': self.devise,
            'position_value': self.position_value,
            'take_profit': self.take_profit,
            'stop_loss': self.stop_loss,
            'type': self.type.value,
            'close': self.close,
            'profit': self.profit,
            'comission': self.comission,
            'fxopen_id': self.fxopen_id,
            'opened_at_timestamp': self.opened_at_timestamp,
            'opened_at': self.opened_at,
            'closed_at': self.closed_at
        }

    def save(self):
        MongoDB.database[TABLE_NAME].update_one({'_id': self._id}, {
            "$set": self.to_json(True)}, upsert=True)
