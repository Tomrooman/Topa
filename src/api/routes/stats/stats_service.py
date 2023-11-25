import datetime
from dataclasses import dataclass
from database.models.trade_model import TradeModel
from flask import request
import json


@dataclass
class DayDict:
    type: str
    value: int
    trades: list[TradeModel]

    def to_json(self):
        return {
            "type": self.type,
            "value": self.value,
            "trades": list(map(lambda trade: trade.to_json(), self.trades))
        }


@dataclass
class MonthDict:
    type: str
    value: int
    days: list[DayDict]

    def to_json(self):
        return {
            "type": self.type,
            "value": self.value,
            "days": list(map(lambda day: day.to_json(), self.days))
        }


@dataclass
class YearDict:
    type: str
    value: int
    months: list[MonthDict]

    def to_json(self):
        return {
            "type": self.type,
            "value": self.value,
            "months": list(map(lambda month: month.to_json(), self.months))
        }


@dataclass
class HandleRouteReturnType:
    years: list[YearDict]

    def to_json(self):
        return list(map(lambda year: year.to_json(), self.years))


@dataclass
class StatsService:
    def handle_route(self) -> str:
        trades = TradeModel.findAll()
        yearDict = []
        for trade in trades:
            opened_at = datetime.datetime.strptime(
                trade.opened_at, "%Y-%m-%dT%H:%M:%S+00:00")
            existingDay = None
            existingMonth = None
            existingYear = None
            for year in yearDict:
                if year != None and year.value == opened_at.year:
                    existingYear = year
                    break
            if existingYear is None:
                existingYear = YearDict(
                    type='year', value=opened_at.year, months=[])
                yearDict.append(existingYear)

            for month in existingYear.months:
                if month != None and month.value == opened_at.month:
                    existingMonth = month
                    break
            if existingMonth is None:
                existingMonth = MonthDict(
                    type='month', value=opened_at.month, days=[])
                existingYear.months.append(existingMonth)

            for day in existingMonth.days:
                if day != None and day.value == opened_at.day:
                    existingDay = day
                    break
            if existingDay is None:
                existingDay = DayDict(
                    type='day', value=opened_at.day, trades=[trade])
                existingMonth.days.append(existingDay)
            else:
                existingDay.trades.append(trade)

        return json.dumps(HandleRouteReturnType(
            years=list(yearDict)
        ).to_json())
