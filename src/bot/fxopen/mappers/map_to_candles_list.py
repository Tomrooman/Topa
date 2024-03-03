from dataclasses import dataclass
from bot.candle import Candle


@dataclass
class FxOpenCandle:
    Volume: int
    Close: float
    Low: float
    High: float
    Open: float
    Timestamp: int


@dataclass
class FxOpenGetCandlesResponse:
    Bars: list[FxOpenCandle]
    Symbol: str
    AvailableFrom: int
    AvailableTo: int
    LastTickId: str  # Datetime
    To: int
    From: int

    def __getitem__(self, key):
        return getattr(self, key)


def map_to_candles_list(candles: FxOpenGetCandlesResponse) -> list[Candle]:
    return list(map(lambda candle: Candle(
        symbol=candles['Symbol'],
        start_timestamp=candle['Timestamp'],
        open=candle['Open'],
        high=candle['High'],
        low=candle['Low'],
        close=candle['Close']
    ), candles['Bars']))
