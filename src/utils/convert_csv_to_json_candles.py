import csv
import datetime
import json


def main():
    converted_file_path = 'data/EURUSD_5min.csv'
    candle = {}
    candles_tick_list = []
    minutes = 0

    file1 = open(converted_file_path, "w")
    file1.write(
        'Symbol, Timeframe, Start timestamp, Start date, Open, High, Low, Close\n')
    file1.close()

    with open('data/EURUSD_historical_1min.csv', mode='r') as csv_file:
        csv_reader = list(csv.DictReader(csv_file))
        line_count = 0
        csv_lines_count = len(csv_reader)
        for row in csv_reader:
            if line_count == 0:
                print(f'Column names are {", ".join(row)}')
            else:
                # print(
                #     f'\t{row["<YYYYMMDD>"]} {row["<TIME_UTC>"]} {row["<OPEN>"]} {row["<HIGH>"]} {row["<LOW>"]} {row["<CLOSE>"]}')
                year = row["<YYYYMMDD>"][0:4]
                month = row["<YYYYMMDD>"][4:6]
                day = row["<YYYYMMDD>"][6:8]
                hours = row["<TIME_UTC>"][0:2]
                minutes = int(row["<TIME_UTC>"][2:4])
                date = datetime.datetime(
                    year=int(year), month=int(month), day=int(day), hour=int(hours), minute=int(minutes), second=0)
                if (len(candles_tick_list) != 0):
                    last_candle_last_minute_character = int(
                        str(candles_tick_list[-1]["minute"])[-1:])
                    last_minute_character = int(str(minutes)[-1:])
                    if ((last_candle_last_minute_character < 5 and last_minute_character >= 5) or (last_candle_last_minute_character >= 5 and last_minute_character < 5) or abs(candles_tick_list[-1]["minute"] - minutes) >= 5):
                        candle = {
                            "start_timestamp": candles_tick_list[0]["start_timestamp"],
                            "start_formatted_date": candles_tick_list[0]["start_formatted_date"],
                            "open": candles_tick_list[0]["open"],
                            "high": max(candles_tick_list, key=lambda x: x['high'])['high'],
                            "low": min(candles_tick_list, key=lambda x: x['low'])['low'],
                            "close": candles_tick_list[-1]["close"]
                        }
                        file1 = open(converted_file_path, "a")
                        file1.write(
                            f'EURUSD, 5min, {candle["start_timestamp"]}, {candle["start_formatted_date"]}, {candle["open"]}, {candle["high"]}, {candle["low"]}, {candle["close"]}' + '\n')
                        file1.close()
                        candles_tick_list = []
                candles_tick_list.append({
                    "start_timestamp": int(date.timestamp() * 1000),
                    "start_formatted_date": date.strftime("%Y-%m-%d %H:%M:%S"),
                    "open": float(row["<OPEN>"]),
                    "high": float(row["<HIGH>"]),
                    "low": float(row["<LOW>"]),
                    "close": float(row["<CLOSE>"]),
                    "minute": minutes,
                })
            line_count += 1
            print(f'\rProcessed {line_count}/{csv_lines_count} lines.')
        print(f'Processed {line_count} lines.')
    if (len(candles_tick_list) != 0):
        candle = {
            "start_timestamp": candles_tick_list[0]["start_timestamp"],
            "start_formatted_date": candles_tick_list[0]["start_formatted_date"],
            "open": candles_tick_list[0]["open"],
            "high": max(candles_tick_list, key=lambda x: x['high'])['high'],
            "low": min(candles_tick_list, key=lambda x: x['low'])['low'],
            "close": candles_tick_list[-1]["close"]
        }
    file1 = open(converted_file_path, "a")
    file1.write(
        f'EURUSD, 5min, {candle["start_timestamp"]}, {candle["start_formatted_date"]}, {candle["open"]}, {candle["high"]}, {candle["low"]}, {candle["close"]}' + '\n')
    file1.close()
    print('Done!')


if __name__ == '__main__':
    main()
