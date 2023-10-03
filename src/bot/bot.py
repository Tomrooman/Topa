import sys  # NOQA
import os  # NOQA
parent_dir = os.path.dirname(os.path.realpath(__file__))  # NOQA
sys.path.append(parent_dir + '/..')  # NOQA
from models.trade_model import TradeModel, TradeType
import pandas as pd
from candle import Candle, create_from_csv_line
from indicators import get_rsi
from pymongo import MongoClient
from config.config_service import ConfigService
from datetime import datetime, timezone
from dateutil import relativedelta


configService = ConfigService()
client = MongoClient(host=configService.get_database_host(),
                     username=configService.get_database_user(),
                     password=configService.get_database_password(),
                     authSource=configService.get_database_name(),
                     authMechanism=configService.get_database_auth_mechanism(),
                     port=configService.get_database_port(),)
database = client[configService.get_database_name()]

FEES = 0.000035  # 0.0035%
CANDLES_HISTORY_LENGTH = 50
BUY_TAKE_PROFIT_PERCENTAGE = 0.004
BUY_STOP_LOSS_PERCENTAGE = 0.002
SELL_TAKE_PROFIT_PERCENTAGE = 0.004
SELL_STOP_LOSS_PERCENTAGE = 0.002

# Sydney is open from 9:00 to 18:00 am UTC
# Tokyo is open from 0:00 to 9:00 UTC
# London is open from 7:00 to 16:00 UTC
# New York is open from 13:00 to 22:00 UTC


class Bot:
    balance = 1000
    trade = TradeModel(is_available=True, price=0,
                       take_profit=0, stop_loss=0, type=TradeType('buy'), close=0, profit=0)
    rsi_5min = 0
    rsi_30min = 0
    rsi_1h = 0
    rsi_4h = 0

    candles_5min_list = []
    candles_30min_list = []
    candles_1h_list = []
    candles_4h_list = []

    open_file_5min = pd.read_csv(
        "data/formatted/EURUSD_5min.csv", chunksize=1)
    open_file_30min = pd.read_csv(
        "data/formatted/EURUSD_30min.csv", chunksize=1)
    open_file_1h = pd.read_csv("data/formatted/EURUSD_1h.csv", chunksize=1)
    open_file_4h = pd.read_csv("data/formatted/EURUSD_4h.csv", chunksize=1)

    def start(self):
        self.check_database_authorization()

        # Drop trades table
        self.trade.drop_table(database)

        candle_5min = create_from_csv_line(
            self.open_file_5min.get_chunk().values[0])
        self.candles_30min_list.append(create_from_csv_line(
            self.open_file_30min.get_chunk().values[0]))
        self.candles_1h_list.append(create_from_csv_line(
            self.open_file_1h.get_chunk().values[0]))
        self.candles_4h_list.append(create_from_csv_line(
            self.open_file_4h.get_chunk().values[0]))

        while (candle_5min != None):
            print(candle_5min)
            print('Balance:', self.balance)
            print('Trade available:', self.trade.is_available)
            candle_5min = self.set_candles_list(candle_5min)
            if (len(self.candles_5min_list) >= 14 and len(self.candles_30min_list) >= 14 and len(self.candles_1h_list) >= 14 and len(self.candles_4h_list) >= 14):
                self.set_all_rsi()
            if (self.rsi_5min != 0 and self.rsi_30min != 0 and self.rsi_1h != 0 and self.rsi_4h != 0):
                self.test_strategy()
            print('----------')

    def test_strategy(self):
        current_candle = self.candles_5min_list[-1]
        last_candle_5min_start_date = datetime.fromtimestamp(
            current_candle.start_timestamp / 1000, tz=timezone.utc)
        current_hour = last_candle_5min_start_date.hour
        if (self.trade.is_available == False):
            self.check_to_close_trade(current_candle)
            return
        if (current_hour >= 7 and current_hour <= 20):
            if (self.rsi_5min < 30 and self.rsi_30min < 40 and self.rsi_1h < 50 and self.rsi_1h < self.rsi_4h):
                print('## Buy ##')
                self.trade.is_available = False
                self.trade.price = current_candle.close
                self.trade.take_profit = current_candle.close + \
                    (current_candle.close * BUY_TAKE_PROFIT_PERCENTAGE)
                self.trade.stop_loss = current_candle.close - \
                    (current_candle.close * BUY_STOP_LOSS_PERCENTAGE)
                self.trade.type = TradeType('buy')
            if (self.rsi_5min > 70 and self.rsi_30min > 60 and self.rsi_1h > 50 and self.rsi_1h > self.rsi_4h):
                print('## Sell ##')
                self.trade.is_available = False
                self.trade.price = current_candle.close
                self.trade.take_profit = current_candle.close - \
                    (current_candle.close * SELL_TAKE_PROFIT_PERCENTAGE)
                self.trade.stop_loss = current_candle.close + \
                    (current_candle.close * SELL_STOP_LOSS_PERCENTAGE)
                self.trade.type = TradeType('sell')
            if (self.trade.is_available == False):
                print(f'type: {self.trade.type.value}')
                print(f'price: {self.trade.price}')
                print(f'take_profit: {self.trade.take_profit}')
                print(f'stop_loss: {self.trade.stop_loss}')
                print(f'balance: {self.balance}')

    def check_to_close_trade(self, current_candle: Candle):
        fees_amount = self.balance * FEES * 2
        if ((self.trade.type.value == 'sell' and current_candle.close >= self.trade.stop_loss) or (self.trade.type.value == 'buy' and current_candle.close <= self.trade.stop_loss)):
            diff_price_amount = abs(self.trade.stop_loss - self.trade.price)
            loss_amount = self.balance * (diff_price_amount / self.trade.price)
            self.balance -= loss_amount + fees_amount
            self.trade.close = self.trade.stop_loss
            self.trade.profit = -loss_amount
            # Save into database
            self.trade.insert_into_database(database)
            self.trade.is_available = True
        if ((self.trade.type.value == 'sell' and current_candle.close <= self.trade.take_profit) or (self.trade.type.value == 'buy' and current_candle.close >= self.trade.take_profit)):
            diff_price_amount = abs(self.trade.take_profit - self.trade.price)
            profit_amount = self.balance * \
                (diff_price_amount / self.trade.price)
            self.balance += profit_amount - fees_amount
            self.trade.close = self.trade.take_profit
            self.trade.profit = profit_amount
            # Save into database
            self.trade.insert_into_database(database)
            self.trade.is_available = True

    # Will throw error if authentication failed
    def check_database_authorization(self):
        database.list_collection_names()

    def set_candles_list(self, candle_5min: Candle) -> Candle:
        if (len(self.candles_5min_list) != 0):
            last_candle_5min_start_date = datetime.fromtimestamp(
                self.candles_5min_list[-1].start_timestamp / 1000, tz=timezone.utc)
            current_candle_5min_start_date = datetime.fromtimestamp(
                candle_5min.start_timestamp / 1000, tz=timezone.utc)
            difference = relativedelta.relativedelta(
                current_candle_5min_start_date, last_candle_5min_start_date)
            if (difference.minutes > 10):
                print('## Difference minutes too high, drop all candles list ##')
                self.candles_5min_list = []
                self.candles_30min_list = []
                self.candles_1h_list = []
                self.candles_4h_list = []
                self.rsi_5min = 0
                self.rsi_30min = 0
                self.rsi_1h = 0
                self.rsi_4h = 0
            if (current_candle_5min_start_date.minute == 0 or current_candle_5min_start_date.minute == 30):
                self.candles_30min_list.append(create_from_csv_line(
                    self.open_file_30min.get_chunk().values[0]))
            if (current_candle_5min_start_date.hour != last_candle_5min_start_date.hour):
                self.candles_1h_list.append(create_from_csv_line(
                    self.open_file_1h.get_chunk().values[0]))
            if (current_candle_5min_start_date.hour != last_candle_5min_start_date.hour and (current_candle_5min_start_date.hour % 4 == 0 or current_candle_5min_start_date.hour == 0)):
                self.candles_4h_list.append(create_from_csv_line(
                    self.open_file_4h.get_chunk().values[0]))
        self.candles_5min_list.append(candle_5min)
        if (len(self.candles_5min_list) > CANDLES_HISTORY_LENGTH):
            del self.candles_5min_list[0]
        if (len(self.candles_30min_list) > CANDLES_HISTORY_LENGTH):
            del self.candles_30min_list[0]
        if (len(self.candles_1h_list) > CANDLES_HISTORY_LENGTH):
            del self.candles_1h_list[0]
        if (len(self.candles_4h_list) > CANDLES_HISTORY_LENGTH):
            del self.candles_4h_list[0]
        return create_from_csv_line(
            self.open_file_5min.get_chunk().values[0])

    def set_all_rsi(self):
        rsi_5min_local = get_rsi(self.candles_5min_list, 14)
        rsi_30min_local = get_rsi(self.candles_30min_list, 14)
        rsi_1h_local = get_rsi(self.candles_1h_list, 14)
        rsi_4h_local = get_rsi(self.candles_4h_list, 14)
        if (len(rsi_5min_local) > 0):
            self.rsi_5min = rsi_5min_local[-1]
        if (len(rsi_30min_local) > 0):
            self.rsi_30min = rsi_30min_local[-1]
        if (len(rsi_1h_local) > 0):
            self.rsi_1h = rsi_1h_local[-1]
        if (len(rsi_4h_local) > 0):
            self.rsi_4h = rsi_4h_local[-1]


if __name__ == '__main__':
    Bot().start()
