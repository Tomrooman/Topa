from datetime import datetime, timezone
import sys  # NOQA
import os  # NOQA
parent_dir = os.path.dirname(os.path.realpath(__file__))  # NOQA
sys.path.append(parent_dir + '/..')  # NOQA
from bot.fxopen.fxopen_api import FxOpenApi, Periodicity
from database.models.trade_model import DeviseType, DeviseValues, TradeModel, TradeType, TradeTypeValues


class HistoricalCandles():
    fxopenApi: FxOpenApi
    devise: DeviseValues = DeviseType('EURUSD').value

    def __init__(self):
        self.fxopenApi = FxOpenApi('demo')
        self.get_candles()

    def get_candles(self):
        limit_date = datetime(
            year=2024, month=3, day=1, hour=0, minute=0, second=0, tzinfo=timezone.utc)
        converted_file_path = 'data/month_debug/fx_open_candles_EURUSD.csv'
        file1 = open(converted_file_path, "w")
        file1.write(
            '<TICKER>,<DTYYYYMMDD>,<TIME>,<OPEN>,<HIGH>,<LOW>,<CLOSE>,<VOL>\n')
        file1.close()
        self.fxopenApi.get_candles(
            self.devise, 'M5', 999, True, 1, limit_date, converted_file_path)


HistoricalCandles()
