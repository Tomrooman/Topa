import base64
from datetime import datetime, timezone
import hmac
import hashlib
import requests
import json
from typing import Literal
from config.config_service import ConfigService
from bot.fxopen.mappers.candles_mapper import map_to_candles_list

Periodicity = Literal[
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


class FxOpenApi():
    api_url = None
    configService = ConfigService()

    def __init__(self, environment: str):
        if (environment == 'prod'):
            self.api_url = 'https://ttlivewebapi.fxopen.net:8443/api/v2'
        elif (environment == 'demo'):
            self.api_url = 'https://ttdemowebapi.fxopen.net:8443/api/v2'
        else:
            raise Exception('Invalid environment')

    def get_candles(self, timeframe: Periodicity, count: int):
        if (count > 999):
            raise Exception('Count must be less than 1000')

        timestamp = round(datetime.now(tz=timezone.utc).timestamp() * 1000)
        url = f'/quotehistory/EURUSD/{timeframe}/bars/ask?count={-(count + 1)}&timestamp={timestamp}'
        data = ''
        # Last candle in the response is open
        response = self.api_request('GET', url, timestamp, data)
        # So remove it because we need closed candles
        del response['Bars'][-1]
        return map_to_candles_list(response)

    def api_request(self, method: Literal['GET', 'POST', 'PUT', 'DELETE'], url: str, timestamp: int, data: str | None, is_auth_required=True):
        if (self.api_url == None):
            raise Exception('Api url is not set')

        call_url = self.api_url + url

        if (is_auth_required == True):
            signature = f'{timestamp}{self.configService.get_web_api_id()}{self.configService.get_web_api_key()}{method}{call_url}{data}'
            base64HmacSignature = base64.b64encode(hmac.new(
                key=self.configService.get_web_api_secret().encode(),
                msg=signature.encode(),
                digestmod=hashlib.sha256
            ).digest()).decode()
            authorization = f"HMAC {self.configService.get_web_api_id()}:{self.configService.get_web_api_key()}:{timestamp}:{base64HmacSignature}"
            response = requests.request(method, call_url, headers={
                "Content-type": "application/json", "Accept": "application/json", "Accept-encoding": "gzip, deflate", "Authorization": authorization}, data=data)
        else:
            response = requests.request(method, call_url, headers={
                "Content-type": "application/json", "Accept": "application/json", "Accept-encoding": "gzip, deflate"}, data=data)

        try:
            response_data = response.json()
        except:
            raise Exception(response.text)

        return response_data
