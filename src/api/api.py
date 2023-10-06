import sys  # NOQA
import os
parent_dir = os.path.dirname(os.path.realpath(__file__))  # NOQA
sys.path.append(parent_dir + '/..')  # NOQA
from gevent.pywsgi import WSGIServer
from flask import Flask
from flask_cors import CORS
from routes.candle.candle_controller import blueprint as candles_blueprint
from routes.days_list.days_list_controller import blueprint as days_list_blueprint


app = Flask(__name__)
app.register_blueprint(candles_blueprint)
app.register_blueprint(days_list_blueprint)
CORS(app)


if __name__ == '__main__':
    # Production
    http_server = WSGIServer(('', 5000), app)
    http_server.serve_forever()
