from dataclasses import dataclass

from bson import ObjectId
from database.instance import MongoDB
from database.models.trade_model import TradeType


TABLE_NAME = 'indicators'


@dataclass
class IndicatorsModel:
    _id: ObjectId
    trade_id: ObjectId
    type: TradeType
    profit: str
    rsi_5min: float
    rsi_5min_fast: float
    rsi_30min: float
    rsi_1h: float
    rsi_4h: float

    @staticmethod
    def drop_table():
        MongoDB.database[TABLE_NAME].drop()

    def to_json(self, for_database: bool = False):
        return {
            "_id": self._id if for_database == True else str(self._id),
            'trade_id': self.trade_id if for_database == True else str(self.trade_id),
            'type': self.type.value,
            'profit': self.profit,
            'rsi_5min': self.rsi_5min,
            'rsi_5min_fast': self.rsi_5min_fast,
            'rsi_30min': self.rsi_30min,
            'rsi_1h': self.rsi_1h,
            'rsi_4h': self.rsi_4h,
        }

    def save(self):
        MongoDB.database[TABLE_NAME].update_one({'_id': self._id}, {
            "$set": self.to_json(True)}, upsert=True)
