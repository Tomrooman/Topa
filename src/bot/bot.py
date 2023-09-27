from dotenv import dotenv_values
from typing import Sequence
import pandas as pd
from talipp.indicators import RSI
from candle import COLUMN_NAMES, Candle, create_from_csv_line  # NOQA

config = dotenv_values(".env")

FEES_PERCENTAGE = 0.0035
CANDLES_HISTORY_LENGTH = 50

# Historical data downloaded in UTC time zone
# Session times in UTC +1/2 time zone
# Europe : de 09h00 à 18h00
# New-York (qui se chevauche avec Londres) : de 14h00 à 22h00
# Tokyo : de 00h00 à 09h00


def main():
    candles = []
    index = 0
    open_file = pd.read_csv("data/formatted/EURUSD_5min.csv", chunksize=1)
    print(create_from_csv_line(open_file.get_chunk().values[0]))
    print(create_from_csv_line(open_file.get_chunk().values[0]))
    # for chunk in open_file:
    #     print(create_from_csv_line(chunk.values[0]))
    #     index += 1
    #     if (index == 15):
    #         return

    # with open("data/formatted/EURUSD_5min.csv", "rb") as text_file:
    #     for line in text_file:
    #         index += 1
    #         if (index > 1):
    #             candles.append(create_from_csv_line(line))
    #             if (len(candles) > CANDLES_HISTORY_LENGTH):
    #                 del candles[0]
    #             test_strategy(candles)
    #         if (index > 20):
    #             return


def get_rsi(candles: Sequence[Candle], period: int):
    if (len(candles) < period + 1):
        return None
    candles_close = list(map(lambda candle: candle.close, candles))
    candles_rsi = RSI(input_values=candles_close, period=period)
    return candles_rsi


def test_strategy(candles: Sequence[Candle]):
    rsi = get_rsi(candles, 14)
    if (rsi == None):
        return
    print(rsi)


if __name__ == '__main__':
    main()
