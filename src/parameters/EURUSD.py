from dataclasses import dataclass
from typing import Any


@dataclass
class Parameters_EURUSD():
    parameters = {
        "FEES": 0.000035,  # 0.0035%
        "LEVERAGE": 5,
        "DIGITS": 5,
        "MIN_LOT_SIZE": 0.01,
        "CANDLES_HISTORY_LENGTH": 12 * 6,  # 6 hours => 12 * HOURS
        "MIN_BUY_TAKE_PROFIT_PERCENTAGE": 0.001,
        "MIN_SELL_TAKE_PROFIT_PERCENTAGE": 0.001,
        "MAX_BUY_TAKE_PROFIT_PERCENTAGE": 0.002,
        "MAX_SELL_TAKE_PROFIT_PERCENTAGE": 0.002,
        "STOP_LOSS_PERCENTAGE_FROM_TP": 0.25,
        "START_TRADE_HOUR": 1,
        "END_TRADE_HOUR": 18,
        "START_CUSTOM_CLOSE_HOUR": 19,
        "END_CUSTOM_CLOSE_HOUR": 20
    }
    rsi_periods = {
        "rsi_5min": 9,
        "rsi_5min_fast": 5,
        "rsi_30min": 11,
        "rsi_1h": 5,
        "rsi_4h": 3
    }

    def buy_trigger(self, min_rsi: float, botManager: Any, current_price: float):
        return botManager.sma_5min_20 > current_price \
            and botManager.sma_5min_50 > current_price \
            and botManager.rsi_5min_fast.value <= botManager.rsi_1h.value \
            and botManager.rsi_1h.value > botManager.rsi_4h.value
        # and botManager.sma_5min_20 > botManager.sma_5min_50 \
        # and botManager.rsi_1h.value >= 70 \
        # and botManager.rsi_4h.value >= 70

    def sell_trigger(self, max_rsi: float, botManager: Any, current_price: float):
        return botManager.sma_5min_20 < current_price \
            and botManager.sma_5min_50 < current_price \
            and botManager.rsi_5min_fast.value >= botManager.rsi_1h.value \
            and botManager.rsi_1h.value < botManager.rsi_4h.value
        # and botManager.sma_5min_20 < botManager.sma_5min_50 \
        #     and botManager.rsi_1h.value <= 30 \
        #     and botManager.rsi_4h.value <= 30

    def buy_take_position(self, botManager: Any, current_price: float):
        return botManager.rsi_5min_fast.value >= botManager.rsi_1h.value and botManager.sma_5min_50 < current_price

    def sell_take_position(self, botManager: Any, current_price: float):
        return botManager.rsi_5min_fast.value <= botManager.rsi_1h.value and botManager.sma_5min_50 > current_price
