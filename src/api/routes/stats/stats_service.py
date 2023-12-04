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
    profit: float

    def to_json(self):
        return {
            "type": self.type,
            "value": self.value,
            "trades": list(map(lambda trade: trade.to_json(), self.trades)),
            "profit": self.profit
        }


@dataclass
class MonthDict:
    type: str
    value: int
    days: list[DayDict]
    profit: float

    def to_json(self):
        return {
            "type": self.type,
            "value": self.value,
            "days": list(map(lambda day: day.to_json(), self.days)),
            "profit": self.profit
        }


@dataclass
class YearDict:
    type: str
    value: int
    months: list[MonthDict]
    profit: float

    def to_json(self):
        return {
            "type": self.type,
            "value": self.value,
            "months": list(map(lambda month: month.to_json(), self.months)),
            "profit": self.profit
        }


@dataclass
class LosingMonths:
    count: int
    profit: float
    months: list[MonthDict]

    def to_json(self):
        return {
            "inRow": self.count,
            "profit": self.profit,
            "months": list(map(lambda month: month.to_json(), self.months)),
        }


@dataclass
class Analytic:
    totalTrades: int
    losingMonths: list[LosingMonths]

    def to_json(self):
        return {
            "totalTrades": self.totalTrades,
            "losingMonths": list(map(lambda losingMonth: losingMonth.to_json(),  self.losingMonths))
        }


@dataclass
class HandleRouteReturnType:
    years: list[YearDict]
    analytics: Analytic

    def to_json(self):
        return {
            "years": list(map(lambda year: year.to_json(), self.years)),
            "analytics": self.analytics.to_json()
        }


@dataclass
class StatsService:
    def handle_route(self) -> str:
        trades = TradeModel.findAll()
        yearDict = []
        analytic = Analytic(totalTrades=len(trades),
                            losingMonths=[])
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
                    type='year', value=opened_at.year, months=[], profit=0)
                yearDict.append(existingYear)

            for month in existingYear.months:
                if month != None and month.value == opened_at.month:
                    existingMonth = month
                    break
            if existingMonth is None:
                existingMonth = MonthDict(
                    type='month', value=opened_at.month, days=[], profit=0)
                existingYear.months.append(existingMonth)

            for day in existingMonth.days:
                if day != None and day.value == opened_at.day:
                    existingDay = day
                    break
            if existingDay is None:
                existingDay = DayDict(
                    type='day', value=opened_at.day, trades=[trade], profit=0)
                existingMonth.days.append(existingDay)
            else:
                existingDay.trades.append(trade)

            existingDay.profit += trade.profit
            existingMonth.profit += trade.profit
            existingYear.profit += trade.profit

        currentLosing = []
        for year in yearDict:
            for month in year.months:
                if (month.profit < 0):
                    if (len(currentLosing) >= 1 and currentLosing[-1].value + 1 != month.value and (month.value != 1 or currentLosing[-1].value != 12)):
                        losingMonths = LosingMonths(count=len(currentLosing),
                                                    profit=sum(
                                                        map(lambda month: month.profit, currentLosing)),
                                                    months=currentLosing)
                        analytic.losingMonths.append(losingMonths)
                        currentLosing = [month]

                    if (len(currentLosing) == 0 or (len(currentLosing) >= 1 and currentLosing[-1].value + 1 == month.value) or (len(currentLosing) >= 1 and month.value == 1 and currentLosing[-1].value == 12)):
                        currentLosing.append(month)
        if (len(currentLosing) > 0):
            losingMonths = LosingMonths(count=len(currentLosing),
                                        profit=sum(
                                            map(lambda month: month.profit, currentLosing)),
                                        months=currentLosing)
            analytic.losingMonths.append(losingMonths)

        return json.dumps(HandleRouteReturnType(
            years=list(yearDict),
            analytics=analytic
        ).to_json())
