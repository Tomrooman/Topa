import datetime
from dataclasses import dataclass
from database.models.trade_model import TradeModel
import json


@dataclass
class DayDict:
    type: str
    value: int
    trades: list[TradeModel]
    profit: float
    percentage_from_balance: float

    def to_json(self):
        return {
            "type": self.type,
            "value": self.value,
            "trades": list(map(lambda trade: trade.to_json(), self.trades)),
            "profit": self.profit,
            "percentage_from_balance": self.percentage_from_balance
        }


@dataclass
class MonthDict:
    type: str
    value: int
    days: list[DayDict]
    profit: float
    percentage_from_balance: float

    def to_json(self):
        return {
            "type": self.type,
            "value": self.value,
            "days": list(map(lambda day: day.to_json(), self.days)),
            "profit": self.profit,
            "percentage_from_balance": self.percentage_from_balance
        }


@dataclass
class YearDict:
    type: str
    value: int
    months: list[MonthDict]
    profit: float
    percentage_from_balance: float

    def to_json(self):
        return {
            "type": self.type,
            "value": self.value,
            "months": list(map(lambda month: month.to_json(), self.months)),
            "profit": self.profit,
            "percentage_from_balance": self.percentage_from_balance
        }


@dataclass
class LosingMonths:
    count: int
    profit: float
    months: list[MonthDict]
    percentage_from_balance: float

    def to_json(self):
        return {
            "inRow": self.count,
            "profit": self.profit,
            "months": list(map(lambda month: month.to_json(), self.months)),
            "percentage_from_balance": self.percentage_from_balance
        }


@dataclass
class TimeToComeback:
    losingMonthsCount: int

    def to_json(self):
        return {
            "losingMonthsCount": self.losingMonthsCount
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
    timeToComeback: list[TimeToComeback]

    def to_json(self):
        return {
            "years": list(map(lambda year: year.to_json(), self.years)),
            "analytics": self.analytics.to_json(),
            "timeToComeback": list(map(lambda timeToComeback: timeToComeback.to_json(), self.timeToComeback))
        }


@dataclass
class StatsService:
    def group_trades_by_days_months_years(self, trades: list[TradeModel]) -> list[YearDict]:
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
                    type='year', value=opened_at.year, months=[], profit=0, percentage_from_balance=0)
                yearDict.append(existingYear)

            for month in existingYear.months:
                if month != None and month.value == opened_at.month:
                    existingMonth = month
                    break
            if existingMonth is None:
                existingMonth = MonthDict(
                    type='month', value=opened_at.month, days=[], profit=0, percentage_from_balance=0)
                existingYear.months.append(existingMonth)

            for day in existingMonth.days:
                if day != None and day.value == opened_at.day:
                    existingDay = day
                    break
            if existingDay is None:
                existingDay = DayDict(
                    type='day', value=opened_at.day, trades=[trade], profit=0, percentage_from_balance=0)
                existingMonth.days.append(existingDay)
            else:
                existingDay.trades.append(trade)
            existingDay.profit += trade.profit
            existingMonth.profit += trade.profit
            existingYear.profit += trade.profit

        return yearDict

    def calcul_stats(self, trades: list[TradeModel], yearDict: list[YearDict]):
        analytic = Analytic(totalTrades=len(trades),
                            losingMonths=[])
        current_balance_year = 2000
        current_balance_month = 2000
        current_balance_day = 2000
        currentLoss = 0
        timeToComeback: list[TimeToComeback] = []
        currentTimeToComeback = None
        currentLosing = []
        for year in yearDict:
            for month in year.months:

                for day in month.days:
                    day.percentage_from_balance = round(
                        (day.profit / current_balance_day) * 100, 4)
                    current_balance_day += day.profit

                month.percentage_from_balance = round(
                    (month.profit / current_balance_month) * 100, 4)
                current_balance_month += month.profit

                if (month.profit < 0):
                    currentLoss += month.profit
                    if (len(currentLosing) >= 1 and currentLosing[-1].value + 1 != month.value and (month.value != 1 or currentLosing[-1].value != 12)):
                        losing_months_profit = sum(
                            map(lambda month: month.profit, currentLosing))
                        losing_months_percentage = sum(
                            map(lambda month: month.percentage_from_balance, currentLosing))
                        losingMonths = LosingMonths(count=len(currentLosing),
                                                    profit=losing_months_profit,
                                                    months=currentLosing,
                                                    percentage_from_balance=losing_months_percentage
                                                    )
                        analytic.losingMonths.append(losingMonths)
                        currentLosing = [month]

                    if (len(currentLosing) == 0 or (len(currentLosing) >= 1 and currentLosing[-1].value + 1 == month.value) or (len(currentLosing) >= 1 and month.value == 1 and currentLosing[-1].value == 12)):
                        currentLosing.append(month)
                if (currentLoss < 0 and month.profit > 0):
                    currentLoss += month.profit
                if (currentLoss < 0):
                    if (currentTimeToComeback is None):
                        currentTimeToComeback = TimeToComeback(
                            losingMonthsCount=0)
                    currentTimeToComeback.losingMonthsCount += 1
                if (currentLoss > 0):
                    if (currentTimeToComeback is not None):
                        timeToComeback.append(currentTimeToComeback)
                        currentTimeToComeback = None
                    currentLoss = 0

            year.percentage_from_balance = round(
                (year.profit / current_balance_year) * 100, 4)
            current_balance_year += year.profit

        if (len(currentLosing) > 0):
            losing_months_profit = sum(
                map(lambda month: month.profit, currentLosing))
            losing_months_percentage = sum(
                map(lambda month: month.percentage_from_balance, currentLosing))
            losingMonths = LosingMonths(count=len(currentLosing),
                                        profit=losing_months_profit,
                                        months=currentLosing, percentage_from_balance=losing_months_percentage)
            analytic.losingMonths.append(losingMonths)
            if (currentTimeToComeback is not None):
                timeToComeback.append(currentTimeToComeback)

        return {"analytic": analytic, "timeToComeback": timeToComeback}

    def handle_route(self) -> str:
        trades = TradeModel.findAll()
        yearDict = self.group_trades_by_days_months_years(trades)
        stats = self.calcul_stats(trades, yearDict)

        return json.dumps(HandleRouteReturnType(
            years=list(yearDict),
            analytics=stats['analytic'],
            timeToComeback=list(stats['timeToComeback'])
        ).to_json())
