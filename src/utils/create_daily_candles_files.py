import os
import sys
parent_dir = os.path.dirname(os.path.realpath(__file__))
sys.path.append(parent_dir + '/..')
from bot.candle import COLUMN_NAMES  # NOQA


def main():
    file_path = 'data/daily/4h'
    candles = []
    previous_day = ''
    year = ''
    month = ''
    day = ''

    with open('data/formatted/EURUSD_4h.csv', mode='rb') as csv_file:
        line_count = 0
        for row in csv_file:
            line = row.decode('utf-8').split(',')
            if line_count == 0:
                print(f'Column names are {", ".join(line)}')
            else:
                year = line[COLUMN_NAMES["Start date"]][1:5]
                month = line[COLUMN_NAMES["Start date"]][6:8]
                day = line[COLUMN_NAMES["Start date"]][9:11]
                if (previous_day != '' and previous_day != day):
                    create_daily_candles_file(
                        file_path, year, month, previous_day, candles)
                    candles = []
                candles.append(','.join(line))
                previous_day = day
            line_count += 1
            print(f'\rProcessed {line_count} lines.')
    create_daily_candles_file(file_path, year, month, previous_day, candles)


def create_daily_candles_file(file_path: str, year: str, month: str, previous_day: str, candles: list[str]):
    if (os.path.isdir(file_path) == False):
        os.mkdir(file_path)
    if (os.path.isdir(file_path + f'/{year}') == False):
        os.mkdir(file_path + f'/{year}')
    if (os.path.isdir(file_path + f'/{year}/{month}') == False):
        os.mkdir(file_path + f'/{year}/{month}')

    file1 = open(
        file_path + f'/{year}/{month}/{previous_day}.csv', "w")
    file1.write(
        'Symbol, Timeframe, Start timestamp, Start date, Open, High, Low, Close\n')
    file1.close()
    file1 = open(
        file_path + f'/{year}/{month}/{previous_day}.csv', "a")
    file1.write(''.join(candles))
    file1.close()


if __name__ == '__main__':
    main()
