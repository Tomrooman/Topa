from dotenv import dotenv_values
from gevent.pywsgi import WSGIServer
from flask import Flask, request
import sys
import os
from flask_cors import CORS
parent_dir = os.path.dirname(os.path.realpath(__file__))
sys.path.append(parent_dir + '/..')
from utils.create_candle_from_csv_line import create_candle_from_csv_line  # NOQA

config = dotenv_values(".env")
app = Flask(__name__)
CORS(app)


@app.get("/candles")
def candles():
    year = request.args.get('year')
    month = request.args.get('month')
    day = request.args.get('day')
    candles = []
    index = 0
    with open(f"data/daily/{year}/{month}/{day}.csv", "rb") as text_file:
        for line in text_file:
            index += 1
            if (index > 1):
                formatted_line = create_candle_from_csv_line(line)
                candles.append(formatted_line)
    return candles


@app.get("/daysList")
def daysList():
    yearsWithMonthsAndDays = []
    for year in sorted(os.listdir("data/daily")):
        yearsWithMonthsAndDays.append({"value": year, "months": []})
        for month in sorted(os.listdir("data/daily/" + year)):
            yearsWithMonthsAndDays[-1]["months"].append(
                {"value": month, "days": []})
            for day in sorted(os.listdir("data/daily/" + year + "/" + month)):
                yearsWithMonthsAndDays[-1]["months"][-1]["days"].append(
                    {"value": day})

    return yearsWithMonthsAndDays


if __name__ == '__main__':
    # Production
    http_server = WSGIServer(('', 5000), app)
    http_server.serve_forever()
