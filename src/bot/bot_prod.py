import base64
from datetime import datetime, timezone
from dateutil import relativedelta
import pandas as pd
import curses
import json
import sys  # NOQA
import os  # NOQA
parent_dir = os.path.dirname(os.path.realpath(__file__))  # NOQA
sys.path.append(parent_dir + '/..')  # NOQA
from bot.bot_manager import BotManager
import requests
from database.models.trade_model import TradeModel
from bot.candle import Candle, create_from_csv_line
from config.config_service import ConfigService
import hmac
import hashlib

periodicity = [
    "D1",
    "H1",
    "H4",
    "M1",
    "M15",
    "M30",
    "M5",
    "MN1",
    "S1",
    "S10",
    "W1"
]


class BotProd(BotManager):
    configService = ConfigService()

    def start(self):
        environment = sys.argv[1]
        if (environment == 'prod'):
            self.api_url = 'https://ttlivewebapi.fxopen.net:8443/api/v2'
        elif (environment == 'demo'):
            self.api_url = 'https://ttdemowebapi.fxopen.net:8443/api/v2'
        else:
            raise Exception('Invalid environment')
        print('test prod')
        self.get_candles()

    def get_candles(self):
        method = 'GET'
        count = 4 * 7 * 12  # 4_hour * 4_hour_rsi * 5_min_in_hour
        data = ''
        timestamp = round(datetime.now(tz=timezone.utc).timestamp() * 1000)
        url = f'/quotehistory/EURUSD/M5/bars/ask?count={-count}&timestamp={timestamp}'
        call_url = self.api_url + url
        signature = f'{timestamp}{self.configService.get_web_api_id()}{self.configService.get_web_api_key()}{method}{call_url}{data}'
        base64HmacSignature = base64.b64encode(hmac.new(
            key=self.configService.get_web_api_secret().encode(),
            msg=signature.encode(),
            digestmod=hashlib.sha256
        ).digest()).decode()
        authorization = f"HMAC {self.configService.get_web_api_id()}:{self.configService.get_web_api_key()}:{timestamp}:{base64HmacSignature}"
        response = requests.get(call_url, headers={
                                "Content-type": "application/json", "Accept": "application/json", "Accept-encoding": "gzip, deflate", "Authorization": authorization})
        try:
            response_data = response.json()
        except:
            response_data = response.text
        print(response_data)


if __name__ == '__main__':
    BotProd().start()
