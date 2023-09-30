from bot.candle import Candle
import datetime
from dataclasses import dataclass
from utils.get_candles_with_previous_days import get_candles_with_previous_days
from bot.indicators import get_rsi
from flask import request
import json


@dataclass
class RSI_data:
    rsi: int
    start_timestamp: int

    def to_json(self):
        return {
            "rsi": self.rsi,
            "start_timestamp": self.start_timestamp
        }


def keep_today_candles(year: str, month: str, day: str, candle: Candle):
    date = datetime.datetime.fromtimestamp(
        candle.start_timestamp / 1000, tz=datetime.timezone.utc)
    date_month = f'0{date.month}' if len(
        str(date.month)) == 1 else str(date.month)
    date_day = f'0{date.day}' if len(str(date.day)) == 1 else str(date.day)
    return str(date.year) == year and date_month == month and date_day == day


def keep_today_rsi(year: str, month: str, day: str, rsi_data: RSI_data):
    date = datetime.datetime.fromtimestamp(
        rsi_data.start_timestamp / 1000, tz=datetime.timezone.utc)
    date_month = f'0{date.month}' if len(
        str(date.month)) == 1 else str(date.month)
    date_day = f'0{date.day}' if len(str(date.day)) == 1 else str(date.day)
    return str(date.year) == year and date_month == month and date_day == day


def aggregate_rsi_with_timestamp(candles_list: list[Candle]) -> list[RSI_data]:
    rsi_list: list[RSI_data] = []
    temp_candles: list[Candle] = []
    for candle in candles_list:
        temp_candles.append(candle)
        rsi = get_rsi(temp_candles, 14)
        if (len(rsi) != 0):
            rsi_list.append(RSI_data(
                rsi=rsi[-1],
                start_timestamp=temp_candles[-1].start_timestamp
            ))
    return rsi_list


@dataclass
class RSI_dict:
    five_min: list[RSI_data]
    thirty_min: list[RSI_data]
    one_hour: list[RSI_data]
    four_hours: list[RSI_data]

    def to_json(self):
        return {
            "five_min": list(map(lambda rsi: rsi.to_json(), self.five_min)),
            "thirty_min": list(map(lambda rsi: rsi.to_json(), self.thirty_min)),
            "one_hour": list(map(lambda rsi: rsi.to_json(), self.one_hour)),
            "four_hours": list(map(lambda rsi: rsi.to_json(), self.four_hours))
        }


@dataclass
class Handle_route_return_type:
    candles: list[Candle]
    rsi: RSI_dict

    def to_json(self):
        return {
            "candles": list(map(lambda candle: candle.to_json(), self.candles)),
            "rsi": self.rsi.to_json()
        }


@dataclass
class Candle_service:
    def handle_route(self) -> str:
        year = request.args.get('year')
        month = request.args.get('month')
        day = request.args.get('day')
        today_candles: list[Candle] = []
        today_rsi_5min: list[RSI_data] = []
        today_rsi_30min: list[RSI_data] = []
        today_rsi_1h: list[RSI_data] = []
        today_rsi_4h: list[RSI_data] = []

        if (year != None and month != None and day != None):
            candles_5min = get_candles_with_previous_days(
                year, month, day, "5min", 1)
            candles_30min = get_candles_with_previous_days(
                year, month, day, "30min", 2)
            candles_1h = get_candles_with_previous_days(
                year, month, day, "1h", 2)
            candles_4h = get_candles_with_previous_days(
                year, month, day, "4h", 5)
            rsi_5min = aggregate_rsi_with_timestamp(candles_5min)
            rsi_30min = aggregate_rsi_with_timestamp(candles_30min)
            rsi_1h = aggregate_rsi_with_timestamp(candles_1h)
            rsi_4h = aggregate_rsi_with_timestamp(candles_4h)
            today_candles = list(filter(lambda candle: keep_today_candles(
                year, month, day, candle), candles_5min))
            today_rsi_5min = list(filter(lambda rsi: keep_today_rsi(
                year, month, day, rsi), rsi_5min))
            today_rsi_30min = list(filter(lambda rsi: keep_today_rsi(
                year, month, day, rsi), rsi_30min))
            today_rsi_1h = list(filter(lambda rsi: keep_today_rsi(
                year, month, day, rsi), rsi_1h))
            today_rsi_4h = list(filter(lambda rsi: keep_today_rsi(
                year, month, day, rsi), rsi_4h))
        return json.dumps(Handle_route_return_type(
            candles=today_candles,
            rsi=RSI_dict(
                five_min=today_rsi_5min,
                thirty_min=today_rsi_30min,
                one_hour=today_rsi_1h,
                four_hours=today_rsi_4h
            )
        ).to_json())
