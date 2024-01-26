import sys  # NOQA
import os  # NOQA
parent_dir = os.path.dirname(os.path.realpath(__file__))  # NOQA
sys.path.append(parent_dir)  # NOQA
from candle import Candle
from talipp.indicators import RSI


def get_rsi(candles: list[Candle], period: int) -> list[float]:
    if (len(candles) < period + 1):
        return []
    candles_close = list(map(lambda candle: candle.close, candles))
    candles_rsi: list[float] = list(
        RSI(input_values=candles_close, period=period))
    return candles_rsi
