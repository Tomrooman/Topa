import sys  # NOQA
import os  # NOQA
parent_dir = os.path.dirname(os.path.realpath(__file__))  # NOQA
sys.path.append(parent_dir + '/..')  # NOQA
import datetime
from bot.candle import Candle, create_from_csv_line


def get_candles_with_previous_days(year: str, month: str, day: str, timeframe: str, previous_days: int) -> list[Candle]:
    date = datetime.datetime(
        year=int(year), month=int(month), day=int(day), tzinfo=datetime.timezone.utc)
    days = datetime.timedelta(days=previous_days)
    date = date - days
    candles = []

    for i in range(previous_days + 1):
        file_path = f"data/daily/{timeframe}/{date.year}/{f'0{date.month}' if len(str(date.month)) == 1 else date.month}/{f'0{date.day}' if len(str(date.day)) == 1 else date.day}.csv"
        if (os.path.isfile(file_path) == True):
            with open(file_path, "rb") as text_file:
                index = 0
                for line in text_file:
                    index += 1
                    if (index > 1):
                        formatted_line = create_from_csv_line(
                            line.decode('utf-8').split(','))
                        candles.append(formatted_line)
        days = datetime.timedelta(days=1)
        date = date + days
    return candles
