from dotenv import dotenv_values
from gevent.pywsgi import WSGIServer
from flask import Flask
import sys
import os
from flask_cors import CORS, cross_origin
parent_dir = os.path.dirname(os.path.realpath(__file__))
sys.path.append(parent_dir + '/..')
from utils.format_csv_line import format_csv_line  # NOQA

config = dotenv_values(".env")
app = Flask(__name__)
CORS(app)


@app.get("/candles")
def hello_world():
    candles = []
    index = 0
    with open("data/daily/2001/01/02.csv", "rb") as text_file:
        for line in text_file:
            index += 1
            if (index > 1):
                formatted_line = format_csv_line(line)
                candles.append(formatted_line)
    return candles


if __name__ == '__main__':
    # Production
    http_server = WSGIServer(('', 5000), app)
    http_server.serve_forever()
