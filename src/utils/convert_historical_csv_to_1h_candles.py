import datetime


def main():
    converted_file_path = 'data/EURUSD_1h.csv'
    candle = {}
    candles_tick_list = []
    minutes = 0
    file1 = open(converted_file_path, "w")
    file1.write(
        'Symbol, Timeframe, Start timestamp, Start date, Open, High, Low, Close\n')
    file1.close()
    with open('data/EURUSD_historical_1min.csv', mode='rb') as csv_file:
        lines_count = 0
        for row in csv_file:
            line = row.decode('utf-8').split(',')
            if lines_count == 0:
                print(f'Column names are {", ".join(line)}')
            else:
                year = line[1][0:4]
                month = line[1][4:6]
                day = line[1][6:8]
                hours = line[2][0:2]
                minutes = int(line[2][2:4])
                date = datetime.datetime(
                    year=int(year), month=int(month), day=int(day), hour=int(hours), minute=int(minutes), second=0, tzinfo=datetime.timezone.utc)
                if (len(candles_tick_list) != 0):
                    last_candle_hours = candles_tick_list[-1]["hours"]
                    if (last_candle_hours != hours):
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
                            f'EURUSD, 1h, {candle["start_timestamp"]}, {candle["start_formatted_date"]}, {candle["open"]}, {candle["high"]}, {candle["low"]}, {candle["close"]}' + '\n')
                        file1.close()
                        candles_tick_list = []
                candles_tick_list.append({
                    "start_timestamp": int(date.timestamp() * 1000),
                    "start_formatted_date": date.strftime("%Y-%m-%d %H:%M:%S"),
                    "open": float(line[3]),
                    "high": float(line[4]),
                    "low": float(line[5]),
                    "close": float(line[6]),
                    "hours": hours,
                    "minute": minutes,
                })
            lines_count += 1
            print(f'\rProcessed {lines_count} lines.')
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
        f'EURUSD, 1h, {candle["start_timestamp"]}, {candle["start_formatted_date"]}, {candle["open"]}, {candle["high"]}, {candle["low"]}, {candle["close"]}' + '\n')
    file1.close()
    print('Done!')


if __name__ == '__main__':
    main()
