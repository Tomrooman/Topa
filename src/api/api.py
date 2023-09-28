from datetime import datetime
import sys  # NOQA
import os  # NOQA
parent_dir = os.path.dirname(os.path.realpath(__file__))  # NOQA
sys.path.append(parent_dir + '/..')  # NOQA
from dotenv import dotenv_values
from gevent.pywsgi import WSGIServer
from flask import Flask, request
from bot.candle import Candle  # NOQA
from flask_cors import CORS
from utils.get_candles_with_previous_days import get_candles_with_previous_days


config = dotenv_values(".env")
app = Flask(__name__)
CORS(app)


def keep_today_candles(year: str, month: str, day: str, candle: Candle):
    date = datetime.fromtimestamp(candle.start_timestamp / 1000)
    date_month = f'0{date.month}' if len(
        str(date.month)) == 1 else str(date.month)
    date_day = f'0{date.day}' if len(str(date.day)) == 1 else str(date.day)
    return str(date.year) == year and date_month == month and date_day == day


@app.get("/candles")
def candles():
    year = request.args.get('year')
    month = request.args.get('month')
    day = request.args.get('day')
    candles: list[Candle] = []
    if (year != None and month != None and day != None):
        candles = get_candles_with_previous_days(
            year, month, day, "5min", 1)
        candles = list(filter(lambda candle: keep_today_candles(
            year, month, day, candle), candles))
    return candles


@app.get("/daysList")
def days_list():
    base_path = "data/daily/5min"
    yearsWithMonthsAndDays = []
    for year in sorted(os.listdir(base_path)):
        yearsWithMonthsAndDays.append({"value": year, "months": []})
        for month in sorted(os.listdir(base_path + "/" + year)):
            yearsWithMonthsAndDays[-1]["months"].append(
                {"value": month, "days": []})
            for day in sorted(os.listdir(base_path + "/" + year + "/" + month)):
                yearsWithMonthsAndDays[-1]["months"][-1]["days"].append(
                    {"value": day})

    return yearsWithMonthsAndDays


if __name__ == '__main__':
    # Production
    http_server = WSGIServer(('', 5000), app)
    http_server.serve_forever()
