from dataclasses import dataclass

COLUMN_NAMES = {
    'Symbol': 0, 'Timeframe': 1, 'Start timestamp': 2, 'Start date': 3, 'Open': 4, 'High': 5, 'Low': 6, 'Close': 7
}


@dataclass
class Candle:
    symbol: str
    start_timestamp: int
    open: float
    high: float
    low: float
    close: float

    def to_json(self):
        return {
            "symbol": self.symbol,
            "start_timestamp": self.start_timestamp,
            "open": self.open,
            "high": self.high,
            "low": self.low,
            "close": self.close
        }


def create_from_csv_line(line: list[str]) -> Candle:
    # formatted_date = datetime.datetime.fromtimestamp(
    #     int(splitted_line[COLUMN_NAMES['Start timestamp']]) / 1000).strftime("%Y-%m-%d %H:%M:%S")
    return Candle(
        symbol=line[COLUMN_NAMES['Symbol']].strip(),
        start_timestamp=int(line[COLUMN_NAMES['Start timestamp']]),
        open=float(line[COLUMN_NAMES['Open']]),
        high=float(line[COLUMN_NAMES['High']]),
        low=float(line[COLUMN_NAMES['Low']]),
        close=float(line[COLUMN_NAMES['Close']])
    )
