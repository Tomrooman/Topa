COLUMN_NAMES = {
    'Symbol': 0, 'Timeframe': 1, 'Start timestamp': 2, 'Start date': 3, 'Open': 4, 'High': 5, 'Low': 6, 'Close': 7
}


def format_csv_line(line: bytes):
    splitted_line = line.decode('utf-8').split(',')
    # formatted_date = datetime.datetime.fromtimestamp(
    #     int(splitted_line[COLUMN_NAMES['Start timestamp']]) / 1000).strftime("%Y-%m-%d %H:%M:%S")
    return {
        'symbol': splitted_line[COLUMN_NAMES['Symbol']],
        'start_timestamp': int(splitted_line[COLUMN_NAMES['Start timestamp']]),
        'start_date': splitted_line[COLUMN_NAMES['Start date']],
        'open': float(splitted_line[COLUMN_NAMES['Open']]),
        'high': float(splitted_line[COLUMN_NAMES['High']]),
        'low': float(splitted_line[COLUMN_NAMES['Low']]),
        'close': float(splitted_line[COLUMN_NAMES['Close']])
    }
