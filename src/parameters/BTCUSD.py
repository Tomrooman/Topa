from dataclasses import dataclass
from typing import Any


@dataclass
class Parameters_BTCUSD():
    parameters = {
        "FEES": 0.002,  # 0.2%
        "LEVERAGE": 2,
        "DIGITS": 2,
        "MIN_LOT_SIZE": 0.01,
        "CANDLES_HISTORY_LENGTH": 12 * 12,  # 12 hours => 12 * HOURS
        "MIN_BUY_TAKE_PROFIT_PERCENTAGE": 0.008,
        "MIN_SELL_TAKE_PROFIT_PERCENTAGE": 0.008,
        "MAX_BUY_TAKE_PROFIT_PERCENTAGE": 0.03,
        "MAX_SELL_TAKE_PROFIT_PERCENTAGE": 0.03,
        "START_TRADE_HOUR": 1,
        "END_TRADE_HOUR": 19,
        "START_CUSTOM_CLOSE_HOUR": 20,
        "END_CUSTOM_CLOSE_HOUR": 21
    }
    rsi_periods = {
        "rsi_5min": 11,
        "rsi_5min_fast": 3,
        "rsi_30min": 7,
        "rsi_1h": 3,
        "rsi_4h": 3
    }

    def buy_trigger(self, min_rsi: float, botManager: Any):
        return min_rsi == botManager.rsi_5min_fast.value \
            and botManager.rsi_5min_fast.value <= 20 \
            and botManager.rsi_30min.value < botManager.rsi_1h.value

    def sell_trigger(self, max_rsi: float, botManager: Any):
        return max_rsi == botManager.rsi_5min_fast.value \
            and botManager.rsi_5min_fast.value >= 80 \
            and botManager.rsi_30min.value > botManager.rsi_1h.value

    def buy_take_position(self, botManager: Any):
        return botManager.rsi_5min_fast.value >= 20

    def sell_take_position(self, botManager: Any):
        return botManager.rsi_5min_fast.value <= 80
