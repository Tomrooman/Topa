from dataclasses import dataclass
import math
from typing import Literal
from bson import ObjectId
from database.models.trade_model import TradeModel, TradeType
from candle import Candle
from indicators import get_rsi
from datetime import datetime, timezone

# Sydney is open from 9:00 to 18:00 am UTC
# Tokyo is open from 0:00 to 9:00 UTC
# London is open from 7:00 to 16:00 UTC
# New York is open from 13:00 to 22:00 UTC


@dataclass
class RsiData:
    value: float
    period: int


class BotManager:
    FEES = 0.000035  # 0.0035%
    LEVERAGE = 5
    CANDLES_HISTORY_LENGTH = 50
    MIN_BUY_TAKE_PROFIT_PERCENTAGE = 0.001
    MIN_SELL_TAKE_PROFIT_PERCENTAGE = 0.001
    MAX_BUY_TAKE_PROFIT_PERCENTAGE = 0.0045
    MAX_SELL_TAKE_PROFIT_PERCENTAGE = 0.0045
    MAX_LOSS_PERCENTAGE = 0.0015

    balance: float = 2000
    max_balance: float = balance
    max_drawdown: float = 0
    current_drawdown: float = 0
    trade = TradeModel(_id=ObjectId(), is_closed=True, price=0, position_value=0, status='New',
                       take_profit=0, stop_loss=0, type=TradeType('buy'), close=0, profit=0, fxopen_id='', opened_at='', opened_at_timestamp=0, closed_at='')
    rsi_5min = RsiData(value=0, period=14)
    rsi_5min_fast = RsiData(value=0, period=7)
    rsi_30min = RsiData(value=0, period=14)
    rsi_1h = RsiData(value=0, period=14)
    rsi_4h = RsiData(value=0, period=7)

    candles_5min_list: list[Candle] = []
    candles_30min_list: list[Candle] = []
    candles_1h_list: list[Candle] = []
    candles_4h_list: list[Candle] = []

    def get_last_candle(self):
        return self.candles_5min_list[-1]

    def get_close_date_from_candle(self, candle: Candle):
        return datetime.fromtimestamp(
            (candle.start_timestamp + (1000 * 60 * 5)) / 1000, tz=timezone.utc)

    def check_strategy(self) -> Literal['Buy', 'Sell', 'Idle']:
        current_candle = self.get_last_candle()
        position = self.get_position_with_tp_and_sl(current_candle)
        closed_hour = self.get_close_date_from_candle(current_candle).hour
        if (closed_hour >= 7 and closed_hour <= 19):
            if (
                position is not None and position['position'] == 'Buy'
            ):
                return 'Buy'
            if (position is not None and position['position'] == 'Sell'):
                return 'Sell'
        return 'Idle'

    def check_for_custom_close(self) -> Literal['close_profit', 'force_close'] | None:
        last_candle = self.get_last_candle()
        closed_hour = self.get_close_date_from_candle(last_candle).hour
        if (closed_hour >= 20 and closed_hour < 21):
            return 'close_profit'
        if (closed_hour >= 21 or closed_hour < 7):
            return 'force_close'

    def get_position_with_tp_and_sl(self, current_candle: Candle) -> dict | None:
        max_rsi = max(self.rsi_5min_fast.value, self.rsi_5min.value, self.rsi_30min.value,
                      self.rsi_1h.value, self.rsi_4h.value)
        min_rsi = min(self.rsi_5min_fast.value, self.rsi_5min.value, self.rsi_30min.value,
                      self.rsi_1h.value, self.rsi_4h.value)
        previous_candles = self.candles_5min_list[-self.CANDLES_HISTORY_LENGTH:]
        if ((self.rsi_5min_fast.value <= 15 and self.rsi_5min.value <= 25 and self.rsi_30min.value <= 40 and self.rsi_1h.value <= 40 and self.rsi_1h.value < self.rsi_4h.value) or
                (min_rsi == self.rsi_5min.value and self.rsi_30min.value < self.rsi_4h.value and self.rsi_1h.value < self.rsi_4h.value)):  # BUY
            return self.get_buy_take_profit_and_stop_loss(current_candle, previous_candles)
        if ((self.rsi_5min_fast.value >= 85 and self.rsi_5min.value >= 75 and self.rsi_30min.value >= 60 and self.rsi_1h.value >= 60 and self.rsi_1h.value > self.rsi_4h.value) or
                ((max_rsi == self.rsi_5min.value and self.rsi_30min.value >
                  self.rsi_4h.value and self.rsi_1h.value > self.rsi_4h.value))
                ):  # SELL
            return self.get_sell_take_profit_and_stop_loss(current_candle, previous_candles)

    def get_buy_take_profit_and_stop_loss(self, current_candle: Candle, previous_candles: list[Candle]) -> dict | None:
        higher_previous_price = max(
            [candle.high for candle in previous_candles])
        max_take_profit_price = current_candle.close + \
            (current_candle.close * self.MAX_BUY_TAKE_PROFIT_PERCENTAGE)
        min_stop_loss_price = current_candle.close - \
            (current_candle.close * self.MAX_LOSS_PERCENTAGE)
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
            if (self.trade.stop_loss < min_stop_loss_price):
                self.trade.stop_loss = min_stop_loss_price
            return {'position': 'Buy', "profit_percentage": profit_percentage}
        if (higher_previous_price >= max_take_profit_price):
            self.trade.take_profit = max_take_profit_price
            self.trade.stop_loss = min_stop_loss_price
            return {'position': 'Buy', "profit_percentage": profit_percentage}

    def get_sell_take_profit_and_stop_loss(self, current_candle: Candle, previous_candles: list[Candle]) -> dict | None:
        lower_previous_price = min(
            [candle.low for candle in previous_candles])
        min_take_profit_price = current_candle.close - \
            (current_candle.close * self.MAX_SELL_TAKE_PROFIT_PERCENTAGE)
        max_stop_loss_price = current_candle.close + \
            (current_candle.close * self.MAX_LOSS_PERCENTAGE)
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
            if (self.trade.stop_loss > max_stop_loss_price):
                self.trade.stop_loss = max_stop_loss_price
            return {'position': 'Sell', "profit_percentage": profit_percentage}
        if (lower_previous_price <= min_take_profit_price):
            self.trade.take_profit = min_take_profit_price
            self.trade.stop_loss = max_stop_loss_price
            return {'position': 'Sell', "profit_percentage": profit_percentage}

    def get_position_value(self) -> int:
        lot_price = 100000
        min_lot_size = 0.01
        min_trade_price = lot_price * min_lot_size

        if (self.balance < min_trade_price):
            raise Exception(
                f'No enough balance to open a trade {self.balance}')

        return int(math.floor(((self.balance * self.LEVERAGE) / min_trade_price)) * min_trade_price)

    def set_drawdown(self):
        if (self.balance > self.max_balance):
            self.max_balance = self.balance
        self.current_drawdown = round(
            ((self.max_balance - self.balance) / self.max_balance) * 100, 4)
        if (self.current_drawdown > self.max_drawdown):
            self.max_drawdown = self.current_drawdown

    def set_all_rsi(self):
        rsi_5min_local = get_rsi(self.candles_5min_list, self.rsi_5min.period)
        rsi_5min_fast_local = get_rsi(
            self.candles_5min_list, self.rsi_5min_fast.period)
        rsi_30min_local = get_rsi(
            self.candles_30min_list, self.rsi_30min.period)
        rsi_1h_local = get_rsi(self.candles_1h_list, self.rsi_1h.period)
        rsi_4h_local = get_rsi(self.candles_4h_list, self.rsi_4h.period)
        if (len(rsi_5min_local) > 0):
            self.rsi_5min.value = rsi_5min_local[-1]
            self.rsi_5min_fast.value = rsi_5min_fast_local[-1]
        if (len(rsi_30min_local) > 0):
            self.rsi_30min.value = rsi_30min_local[-1]
        if (len(rsi_1h_local) > 0):
            self.rsi_1h.value = rsi_1h_local[-1]
        if (len(rsi_4h_local) > 0):
            self.rsi_4h.value = rsi_4h_local[-1]
