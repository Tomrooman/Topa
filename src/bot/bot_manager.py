import math
import sys  # NOQA
import os
parent_dir = os.path.dirname(os.path.realpath(__file__))  # NOQA
sys.path.append(parent_dir + '/..')  # NOQA
from database.models.trade_model import TradeModel, TradeType
from candle import Candle
from indicators import get_rsi
from datetime import datetime, timezone

# Sydney is open from 9:00 to 18:00 am UTC
# Tokyo is open from 0:00 to 9:00 UTC
# London is open from 7:00 to 16:00 UTC
# New York is open from 13:00 to 22:00 UTC


class BotManager:
    FEES = 0.000035  # 0.0035%
    CANDLES_HISTORY_LENGTH = 50
    MIN_BUY_TAKE_PROFIT_PERCENTAGE = 0.001
    MIN_SELL_TAKE_PROFIT_PERCENTAGE = 0.001
    MAX_BUY_TAKE_PROFIT_PERCENTAGE = 0.003
    MAX_SELL_TAKE_PROFIT_PERCENTAGE = 0.003

    balance = 2000
    max_balance = balance
    max_drawdown = 0
    current_drawdown = 0
    current_hour = 0
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

    def get_current_candle_with_start_and_close_date(self):
        current_candle = self.candles_5min_list[-1]
        current_candle_sart_date = datetime.fromtimestamp(
            current_candle.start_timestamp / 1000, tz=timezone.utc)
        current_candle_close_date = datetime.fromtimestamp(
            (current_candle.start_timestamp + (1000 * 60 * 5)) / 1000, tz=timezone.utc)
        return current_candle, current_candle_sart_date, current_candle_close_date

    def set_current_hour_from_current_candle(self, current_candle: Candle):
        current_candle_sart_date = datetime.fromtimestamp(
            current_candle.start_timestamp / 1000, tz=timezone.utc)
        self.current_hour = current_candle_sart_date.hour

    def check_strategy(self, current_candle: Candle) -> str:
        position = self.get_position_with_tp_and_sl(current_candle)
        if (self.current_hour >= 7 and self.current_hour <= 19):
            if (
                position is not None and position['position'] == 'BUY'
            ):
                return 'BUY'
            if (position is not None and position['position'] == 'SELL'):
                return 'SELL'
            # if (position is not None):
                # print(f'type: {self.trade.type.value}')
                # print(f'price: {self.trade.price}')
                # print(f'take_profit: {self.trade.take_profit}')
                # print(f'stop_loss: {self.trade.stop_loss}')
                # print(f'balance: {self.balance}')
                # print(f'profit percentage: {position["profit_percentage"]}')
        return 'IDLE'

    def check_for_custom_close(self, close_date: datetime) -> str | None:
        if (close_date.hour >= 20 and close_date.hour < 21):
            return 'close_profit'
        if (close_date.hour >= 21 or close_date.hour < 7):
            return 'force_close'

    # {position: 'BUY' | 'SELL', profit_percentage: float} | None
    def get_position_with_tp_and_sl(self, current_candle: Candle):
        max_rsi = max(self.rsi_5min, self.rsi_30min, self.rsi_1h, self.rsi_4h)
        min_rsi = min(self.rsi_5min, self.rsi_30min, self.rsi_1h, self.rsi_4h)
        previous_candles = self.candles_5min_list[-self.CANDLES_HISTORY_LENGTH:]
        if ((self.rsi_5min <= 25 and self.rsi_30min <= 40 and self.rsi_1h <= 40 and self.rsi_1h < self.rsi_4h) or
                (min_rsi == self.rsi_5min and self.rsi_5min <=
                 30 and self.rsi_30min < self.rsi_4h and self.rsi_1h < self.rsi_4h)):  # BUY
            higher_previous_price = max(
                [candle.high for candle in previous_candles])
            max_take_profit_price = current_candle.close + \
                (current_candle.close * self.MAX_BUY_TAKE_PROFIT_PERCENTAGE)
            if (higher_previous_price <= current_candle.close):
                return
            profit_percentage = 1/(current_candle.close /
                                   (higher_previous_price - current_candle.close))
            if (profit_percentage < self.MIN_BUY_TAKE_PROFIT_PERCENTAGE):
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
                (current_candle.close * self.MAX_SELL_TAKE_PROFIT_PERCENTAGE)
            if (lower_previous_price >= current_candle.close):
                return
            profit_percentage = 1 / (current_candle.close /
                                     (current_candle.close - lower_previous_price))
            if (profit_percentage < self.MIN_SELL_TAKE_PROFIT_PERCENTAGE):
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

    def set_all_rsi(self):
        rsi_5min_local = get_rsi(self.candles_5min_list, 14)
        rsi_30min_local = get_rsi(self.candles_30min_list, 14)
        rsi_1h_local = get_rsi(self.candles_1h_list, 14)
        rsi_4h_local = get_rsi(self.candles_4h_list, 7)
        if (len(rsi_5min_local) > 0):
            self.rsi_5min = rsi_5min_local[-1]
        if (len(rsi_30min_local) > 0):
            self.rsi_30min = rsi_30min_local[-1]
        if (len(rsi_1h_local) > 0):
            self.rsi_1h = rsi_1h_local[-1]
        if (len(rsi_4h_local) > 0):
            self.rsi_4h = rsi_4h_local[-1]
