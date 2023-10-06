from bot.candle import Candle
import datetime
from dataclasses import dataclass
from database.models.trade_model import TradeModel
from utils.get_candles_with_previous_days import get_candles_with_previous_days
from bot.indicators import get_rsi
from flask import request
import json


@dataclass
class RsiData:
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


def keep_today_rsi(year: str, month: str, day: str, rsiData: RsiData):
    date = datetime.datetime.fromtimestamp(
        rsiData.start_timestamp / 1000, tz=datetime.timezone.utc)
    date_month = f'0{date.month}' if len(
        str(date.month)) == 1 else str(date.month)
    date_day = f'0{date.day}' if len(str(date.day)) == 1 else str(date.day)
    return str(date.year) == year and date_month == month and date_day == day


def aggregate_rsi_with_timestamp(candles_list: list[Candle]) -> list[RsiData]:
    rsi_list: list[RsiData] = []
    temp_candles: list[Candle] = []
    for candle in candles_list:
        temp_candles.append(candle)
        rsi = get_rsi(temp_candles, 14)
        if (len(rsi) != 0):
            rsi_list.append(RsiData(
                rsi=rsi[-1],
                start_timestamp=temp_candles[-1].start_timestamp
            ))
    return rsi_list


@dataclass
class RsiDict:
    five_min: list[RsiData]
    thirty_min: list[RsiData]
    one_hour: list[RsiData]
    four_hours: list[RsiData]

    def to_json(self):
        return {
            "five_min": list(map(lambda rsi: rsi.to_json(), self.five_min)),
            "thirty_min": list(map(lambda rsi: rsi.to_json(), self.thirty_min)),
            "one_hour": list(map(lambda rsi: rsi.to_json(), self.one_hour)),
            "four_hours": list(map(lambda rsi: rsi.to_json(), self.four_hours))
        }


@dataclass
class HandleRouteReturnType:
    candles: list[Candle]
    rsi: RsiDict
    trades: list[TradeModel]

    def to_json(self):
        return {
            "candles": list(map(lambda candle: candle.to_json(), self.candles)),
            "rsi": self.rsi.to_json(),
            "trades": list(map(lambda trade: trade.to_json(), self.trades))
        }


@dataclass
class CandleService:
    def handle_route(self) -> str:
        year = request.args.get('year')
        month = request.args.get('month')
        day = request.args.get('day')
        today_candles: list[Candle] = []
        today_rsi_5min: list[RsiData] = []
        today_rsi_30min: list[RsiData] = []
        today_rsi_1h: list[RsiData] = []
        today_rsi_4h: list[RsiData] = []
        trades: list[TradeModel] = []

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
            start_date = datetime.datetime(
                year=int(year), month=int(month), day=int(day), hour=0, minute=0, second=0, tzinfo=datetime.timezone.utc)
            days = datetime.timedelta(days=1)
            end_date = start_date + days
            trades = TradeModel.findTradesByDate(
                start_date.isoformat(), end_date.isoformat())
        return json.dumps(HandleRouteReturnType(
            candles=today_candles,
            rsi=RsiDict(
                five_min=today_rsi_5min,
                thirty_min=today_rsi_30min,
                one_hour=today_rsi_1h,
                four_hours=today_rsi_4h
            ),
            trades=trades
        ).to_json())
