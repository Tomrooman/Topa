import base64
from datetime import datetime, timezone
import hmac
import hashlib
from bson import ObjectId
import requests
import json
from typing import Any, Literal
from config.config_service import ConfigService
from .mappers.map_to_candles_list import map_to_candles_list
from .mappers.map_to_trade import map_to_trade
from .mappers.map_to_account_info import map_to_account_info
from logger.logger_service import LoggerService

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
    loggerService = LoggerService()

    def __init__(self, environment: Literal['prod', 'demo']):
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
        response = self.api_request(
            method='GET', url=url, data=data, is_auth_required=True)
        # So remove it because we need closed candles
        del response['Bars'][-1]
        return map_to_candles_list(response)

    def get_trade_by_id(self, trade_id: str):
        url = f'/trade/{trade_id}'
        data = ''
        response = self.api_request(
            method='GET', url=url, data=data, is_auth_required=True)

        if ("Message" in response):  # Not found, probably closed
            return None

        return map_to_trade(response)

    # https://ttdemowebapi.fxopen.net:8443/api/doc/index#!/54132Trades32information32and32operations/Trade_Post
    def create_trade(self, side: Literal['Buy', 'Sell'], amount: int, stop_loss: float, take_profit: float, comment: ObjectId):
        url = '/trade'
        data = json.dumps({
            "Symbol": "EURUSD",
            "Amount": amount,
            "Side": side,
            "Type": "Market",
            "StopLoss": round(stop_loss, 5),
            "TakeProfit": round(take_profit, 5),
            "Comment": str(comment)
        })
        self.loggerService.log('call api to create trade')
        response = self.api_request(
            method='POST', url=url, data=data, is_auth_required=True)
        self.loggerService.log(f'create trade api response: {response}')
        try:
            return map_to_trade(response)
        except Exception as e:
            self.loggerService.log(f"server message: {response['Message']}")
            raise e

    def close_trade(self, trade_id: str):
        url = '/trade'
        data = json.dumps({
            "Type": "Close",
            "Id": trade_id,
        })
        self.api_request(
            method='DELETE', url=url, data=data, is_auth_required=True)

    def get_account_info(self):
        url = f'/account'
        data = ''
        response = self.api_request(
            method='GET', url=url, data=data, is_auth_required=True)
        return map_to_account_info(response)

    def api_request(self, method: Literal['GET', 'POST', 'PUT', 'DELETE'], url: str, data: str | None, is_auth_required=True):
        if (self.api_url == None):
            raise Exception('Api url is not set')

        call_url = self.api_url + url

        if (is_auth_required == True):
            timestamp = round(datetime.now(tz=timezone.utc).timestamp() * 1000)
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

        response_data: Any = None
        if (method != 'DELETE'):
            try:
                response_data = response.json()
            except:
                raise Exception(response.text)

        return response_data
