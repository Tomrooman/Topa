import requests
from typing import Sequence
from dataclasses import dataclass
import datetime
from utils.format_csv_line import format_csv_line
from dotenv import dotenv_values

config = dotenv_values(".env")

# Historical data in UTC time zone

# Europe : de 09h00 à 18h00
# New-York (qui se chevauche avec Londres) : de 14h00 à 23h00
# Tokyo : de 00h00 à 09h00


@dataclass
class Candle:
    symbol: str
    start_timestamp: int
    start_date: str
    open: float
    high: float
    low: float
    close: float


def main():
    candles = []
    index = 0
    with open("data/formatted/EURUSD_5min.csv", "rb") as text_file:
        for line in text_file:
            index += 1
            if (index > 1):
                candles.append(format_csv_line(line))
                if (len(candles) > 50):
                    del candles[0]
                test_strategy(candles)
                return


def test_strategy(candles: Sequence[Candle]):
    print(candles)


if __name__ == '__main__':
    main()
