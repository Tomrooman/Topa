import datetime
import os


def main():
    converted_file_path = 'data/BTCUSD_30min.csv'
    candle = {}
    candles_tick_list = []
    minutes = 0
    file1 = open(converted_file_path, "w")
    file1.write(
        'Symbol, Timeframe, Start timestamp, Start date, Open, High, Low, Close\n')
    file1.close()

    for f in sorted(os.listdir('data/crypto')):
        print(f)
        with open(f'data/crypto/{f}', mode='rb') as csv_file:
            lines_count = 0
            for row in csv_file:
                line = row.decode('utf-8').split(',')
                if lines_count == 0:
                    print(f'Column names are {", ".join(line)}')
                else:
                    date = datetime.datetime.fromtimestamp(
                        int(line[0]) / 1000, tz=datetime.timezone.utc)
                    day = date.day
                    hours = date.hour
                    minutes = date.minute
                    if (len(candles_tick_list) != 0):
                        first_candle_minutes = candles_tick_list[0]["minute"]
                        first_candle_hours = candles_tick_list[0]["hours"]
                        first_candle_day = candles_tick_list[0]["day"]
                        if ((first_candle_minutes < 30 and minutes >= 30) or (first_candle_minutes >= 30 and minutes < 30) or first_candle_hours != hours or first_candle_day != day):
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
                                f'BTCUSD, 30min, {candle["start_timestamp"]}, {candle["start_formatted_date"]}, {candle["open"]}, {candle["high"]}, {candle["low"]}, {candle["close"]}' + '\n')
                            file1.close()
                            candles_tick_list = []
                    candles_tick_list.append({
                        "start_timestamp": int(date.timestamp() * 1000),
                        "start_formatted_date": date.strftime("%Y-%m-%d %H:%M:%S"),
                        "open": float(line[1]),
                        "high": float(line[2]),
                        "low": float(line[3]),
                        "close": float(line[4]),
                        "hours": hours,
                        "minute": minutes,
                        "day": day,
                    })
                lines_count += 1
                # print(f'\rProcessed {lines_count} lines.')
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
        f'BTCUSD, 30min, {candle["start_timestamp"]}, {candle["start_formatted_date"]}, {candle["open"]}, {candle["high"]}, {candle["low"]}, {candle["close"]}' + '\n')
    file1.close()
    print('Done!')


if __name__ == '__main__':
    main()
