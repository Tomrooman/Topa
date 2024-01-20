import math
import sys  # NOQA
import os  # NOQA
parent_dir = os.path.dirname(os.path.realpath(__file__))  # NOQA
sys.path.append(parent_dir + '/..')  # NOQA
from database.models.trade_model import TradeModel, TradeType
import pandas as pd
from candle import Candle, create_from_csv_line
from indicators import get_rsi
from datetime import datetime, timezone
from dateutil import relativedelta

FEES = 0.000035  # 0.0035%
CANDLES_HISTORY_LENGTH = 50
# BUY_TAKE_PROFIT_PERCENTAGE = 0.004
# BUY_STOP_LOSS_PERCENTAGE = 0.002
# SELL_TAKE_PROFIT_PERCENTAGE = 0.004
# SELL_STOP_LOSS_PERCENTAGE = 0.002
MIN_BUY_TAKE_PROFIT_PERCENTAGE = 0.0005
MIN_SELL_TAKE_PROFIT_PERCENTAGE = 0.0005
MAX_BUY_TAKE_PROFIT_PERCENTAGE = 0.002
MAX_SELL_TAKE_PROFIT_PERCENTAGE = 0.002

# Sydney is open from 9:00 to 18:00 am UTC
# Tokyo is open from 0:00 to 9:00 UTC
# London is open from 7:00 to 16:00 UTC
# New York is open from 13:00 to 22:00 UTC


class Bot:
    balance = 2000
    max_balance = balance
    max_drawdown = 0
    current_drawdown = 0
    trade = TradeModel(is_available=True, price=0, position_value=0,
                       take_profit=0, stop_loss=0, type=TradeType('buy'), close=0, profit=0, opened_at='', closed_at='')
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

    f = open("data/diff_to_high.txt", "w")
    f.write("")
    f.close()

    def start(self):
        # Drop trades table
        TradeModel.drop_table()

        candle_5min = create_from_csv_line(
            self.open_file_5min.get_chunk().values[0])
        self.candles_30min_list.append(create_from_csv_line(
            self.open_file_30min.get_chunk().values[0]))
        self.candles_1h_list.append(create_from_csv_line(
            self.open_file_1h.get_chunk().values[0]))
        self.candles_4h_list.append(create_from_csv_line(
            self.open_file_4h.get_chunk().values[0]))

        while (candle_5min != None):
            print(candle_5min.start_date)
            print('Balance:', self.balance)
            print('Trade available:', self.trade.is_available)
            print('Max balance:', self.max_balance)
            print(
                f'Current drawdown: {self.current_drawdown}% - {self.max_balance * (self.current_drawdown / 100)}')
            print(
                f'Max drawdown: {self.max_drawdown}%')
            candle_5min = self.set_candles_list(candle_5min)
            if (len(self.candles_5min_list) >= 14 and len(self.candles_30min_list) >= 14 and len(self.candles_1h_list) >= 14 and len(self.candles_4h_list) >= 14):
                self.set_all_rsi()
            if (self.rsi_5min != 0 and self.rsi_30min != 0 and self.rsi_1h != 0 and self.rsi_4h != 0):
                self.test_strategy()
            print('----------')

    def test_strategy(self):
        current_candle = self.candles_5min_list[-1]
        current_candle_sart_date = datetime.fromtimestamp(
            current_candle.start_timestamp / 1000, tz=timezone.utc)
        current_candle_close_date = datetime.fromtimestamp(
            (current_candle.start_timestamp + (1000 * 60 * 5)) / 1000, tz=timezone.utc)
        current_hour = current_candle_sart_date.hour
        if (self.trade.is_available == False):
            self.check_to_close_trade(
                current_candle, current_candle_close_date)
            return
        max_rsi = max(self.rsi_5min, self.rsi_30min, self.rsi_1h, self.rsi_4h)
        min_rsi = min(self.rsi_5min, self.rsi_30min, self.rsi_1h, self.rsi_4h)
        position = self.get_position_with_tp_and_sl(
            min_rsi, max_rsi, current_candle)
        if (current_hour >= 7 and current_hour <= 20):
            if (
                position is not None and position['position'] == 'BUY'
            ):
                print('## Buy ##')
                self.trade.is_available = False
                self.trade.price = current_candle.close
                # self.trade.take_profit = current_candle.close + \
                #     (current_candle.close * BUY_TAKE_PROFIT_PERCENTAGE)
                # self.trade.stop_loss = current_candle.close - \
                #     (current_candle.close * BUY_STOP_LOSS_PERCENTAGE)
                self.trade.opened_at = current_candle_sart_date.isoformat()
                self.trade.type = TradeType('buy')
                self.trade.position_value = self.get_position_value()
            if (position is not None and position['position'] == 'SELL'):
                print('## Sell ##')
                self.trade.is_available = False
                self.trade.price = current_candle.close
                # self.trade.take_profit = current_candle.close - \
                #     (current_candle.close * SELL_TAKE_PROFIT_PERCENTAGE)
                # self.trade.stop_loss = current_candle.close + \
                #     (current_candle.close * SELL_STOP_LOSS_PERCENTAGE)
                self.trade.opened_at = current_candle_sart_date.isoformat()
                self.trade.type = TradeType('sell')
                self.trade.position_value = self.get_position_value()
            if (position is not None):
                print(f'type: {self.trade.type.value}')
                print(f'price: {self.trade.price}')
                print(f'take_profit: {self.trade.take_profit}')
                print(f'stop_loss: {self.trade.stop_loss}')
                # print(f'balance: {self.balance}')
                print(f'profit percentage: {position["profit_percentage"]}')

    def get_position_with_tp_and_sl(self, min_rsi, max_rsi, current_candle):
        previous_candles = self.candles_5min_list[-CANDLES_HISTORY_LENGTH:]
        if ((self.rsi_5min <= 25 and self.rsi_30min <= 40 and self.rsi_1h <= 40 and self.rsi_1h < self.rsi_4h) or
                (min_rsi == self.rsi_5min and self.rsi_5min <=
                 30 and self.rsi_30min < self.rsi_4h and self.rsi_1h < self.rsi_4h)):  # BUY
            higher_previous_price = max(
                [candle.high for candle in previous_candles])
            max_take_profit_price = current_candle.close + \
                (current_candle.close * MAX_BUY_TAKE_PROFIT_PERCENTAGE)
            if (higher_previous_price <= current_candle.close):
                return
            profit_percentage = 1/(current_candle.close /
                                   (higher_previous_price - current_candle.close))
            if (profit_percentage < MIN_BUY_TAKE_PROFIT_PERCENTAGE):
                return
            if (higher_previous_price < max_take_profit_price):
                self.trade.take_profit = higher_previous_price
                self.trade.stop_loss = current_candle.close - \
                    ((higher_previous_price - current_candle.close) / 2)
                return {'position': 'BUY', "profit_percentage": profit_percentage}
            if (higher_previous_price >= max_take_profit_price):
                self.trade.take_profit = max_take_profit_price
                self.trade.stop_loss = current_candle.close - \
                    ((max_take_profit_price - current_candle.close) / 2)
                return {'position': 'BUY', "profit_percentage": profit_percentage}
        if ((self.rsi_5min >= 75 and self.rsi_30min >= 60 and self.rsi_1h >= 60 and self.rsi_1h > self.rsi_4h) or
            ((max_rsi == self.rsi_5min and self.rsi_5min >=
                      70 and self.rsi_30min > self.rsi_4h and self.rsi_1h > self.rsi_4h))
            ):  # SELL
            lower_previous_price = min(
                [candle.low for candle in previous_candles])
            min_take_profit_price = current_candle.close - \
                (current_candle.close * MAX_SELL_TAKE_PROFIT_PERCENTAGE)
            if (lower_previous_price >= current_candle.close):
                return
            profit_percentage = 1 / (current_candle.close /
                                     (current_candle.close - lower_previous_price))
            if (profit_percentage < MIN_SELL_TAKE_PROFIT_PERCENTAGE):
                return
            if (lower_previous_price > min_take_profit_price):
                self.trade.take_profit = lower_previous_price
                self.trade.stop_loss = current_candle.close + \
                    ((current_candle.close - lower_previous_price) / 2)
                return {'position': 'SELL', "profit_percentage": profit_percentage}
            if (lower_previous_price <= min_take_profit_price):
                self.trade.take_profit = min_take_profit_price
                self.trade.stop_loss = current_candle.close + \
                    ((current_candle.close - min_take_profit_price) / 2)
                return {'position': 'SELL', "profit_percentage": profit_percentage}

    def get_position_value(self) -> int:
        lot_price = 100000
        min_lot_size = 0.01
        min_trade_price = lot_price * min_lot_size

        if (self.balance < min_trade_price):
            raise Exception(
                f'No enough balance to open a trade {self.balance}')

        return int(math.floor(self.balance / min_trade_price) * min_trade_price)

    def check_to_close_trade(self, current_candle: Candle, current_candle_close_date: datetime):
        fees_amount = self.trade.position_value * FEES * 2
        if (current_candle_close_date.hour >= 22 or current_candle_close_date.hour < 7):  # Close trade at 22:00
            diff_price_amount = abs(current_candle.close - self.trade.price)
            trade_profit = self.trade.position_value * \
                (diff_price_amount / self.trade.price)
            if ((self.trade.type.value == 'sell' and current_candle.close <= self.trade.price) or (self.trade.type.value == 'buy' and current_candle.close >= self.trade.price)):
                self.balance += trade_profit - fees_amount
                self.trade.profit = trade_profit
            if ((self.trade.type.value == 'sell' and current_candle.close >= self.trade.price) or (self.trade.type.value == 'buy' and current_candle.close <= self.trade.price)):
                self.balance -= trade_profit + fees_amount
                self.trade.profit = -trade_profit
            self.trade.close = current_candle.close
            self.trade.closed_at = current_candle_close_date.isoformat()
            # Save into database
            self.trade.insert_into_database()
            self.trade.is_available = True
            self.set_drawdown()
        if ((self.trade.type.value == 'sell' and current_candle.close >= self.trade.stop_loss) or (self.trade.type.value == 'buy' and current_candle.close <= self.trade.stop_loss)):
            diff_price_amount = abs(self.trade.stop_loss - self.trade.price)
            loss_amount = self.trade.position_value * \
                (diff_price_amount / self.trade.price)
            self.balance -= loss_amount + fees_amount
            self.trade.close = self.trade.stop_loss
            self.trade.profit = -loss_amount
            self.trade.closed_at = current_candle_close_date.isoformat()
            # Save into database
            self.trade.insert_into_database()
            self.trade.is_available = True
            self.set_drawdown()
        if ((self.trade.type.value == 'sell' and current_candle.close <= self.trade.take_profit) or (self.trade.type.value == 'buy' and current_candle.close >= self.trade.take_profit)):
            diff_price_amount = abs(self.trade.take_profit - self.trade.price)
            profit_amount = self.trade.position_value * \
                (diff_price_amount / self.trade.price)
            self.balance += profit_amount - fees_amount
            self.trade.close = self.trade.take_profit
            self.trade.profit = profit_amount
            self.trade.closed_at = current_candle_close_date.isoformat()
            # Save into database
            self.trade.insert_into_database()
            self.trade.is_available = True
            self.set_drawdown()

    def set_drawdown(self):
        if (self.balance > self.max_balance):
            self.max_balance = self.balance
        self.current_drawdown = round(
            ((self.max_balance - self.balance) / self.max_balance) * 100, 4)
        if (self.current_drawdown > self.max_drawdown):
            self.max_drawdown = self.current_drawdown
        # print('Max balance:', self.max_balance)
        # print('Current drawdown:', current_drawdown)
        # print('Max drawdown:', self.max_drawdown)

    def set_candles_list(self, candle_5min: Candle) -> Candle:
        if (len(self.candles_5min_list) != 0):
            last_candle_5min_start_date = datetime.fromtimestamp(
                self.candles_5min_list[-1].start_timestamp / 1000, tz=timezone.utc)
            current_candle_5min_start_date = datetime.fromtimestamp(
                candle_5min.start_timestamp / 1000, tz=timezone.utc)
            difference = relativedelta.relativedelta(
                current_candle_5min_start_date, last_candle_5min_start_date)
            if (difference.minutes > 10 and current_candle_5min_start_date.hour != 23 and current_candle_5min_start_date.minute != 40 and current_candle_5min_start_date.hour != 0):
                print('## Difference minutes too high, drop all candles list ##')
                f = open("data/diff_to_high.txt", "a")
                f.write(
                    f"Difference minutes too high, drop all candles list\n{last_candle_5min_start_date.isoformat()}\n{current_candle_5min_start_date.isoformat()}\n\n")
                f.close()
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
