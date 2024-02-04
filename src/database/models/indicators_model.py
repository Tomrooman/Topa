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
    profit: float
    rsi_5_min: float
    rsi_5_min_fast: float
    rsi_30_min: float
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
            'rsi_5_min': self.rsi_5_min,
            'rsi_5_min_fast': self.rsi_5_min_fast,
            'rsi_30_min': self.rsi_30_min,
            'rsi_1h': self.rsi_1h,
            'rsi_4h': self.rsi_4h,
        }

    def save(self):
        MongoDB.database[TABLE_NAME].update_one({'_id': self._id}, {
            "$set": self.to_json(True)}, upsert=True)
