import base64
from datetime import datetime, timezone
import hmac
import hashlib
from typing import Literal
import json
import websocket
from threading import Thread
from config.config_service import ConfigService


class FxOpenFeedWebsocket():
    id = 'Topa-feed'
    websocket_feed_url = ''
    configService = ConfigService()

    def __init__(self, environment: Literal['prod', 'demo']):
        if (environment == 'prod'):
            self.websocket_feed_url = 'wss://ttlivewebapi.fxopen.net:3000'
        elif (environment == 'demo'):
            self.websocket_feed_url = 'wss://ttdemowebapi.soft-fx.com:2083'
        else:
            raise Exception('Invalid environment')

        websocket.enableTrace(False)
        self.init_websocket()

    def send_auth_message(self, ws):
        print('sending feed auth message')
        timestamp = round(datetime.now(tz=timezone.utc).timestamp() * 1000)
        signature = f'{timestamp}{self.configService.get_web_api_id()}{self.configService.get_web_api_key()}'
        base64HmacSignature = base64.b64encode(hmac.new(
            key=self.configService.get_web_api_secret().encode(),
            msg=signature.encode(),
            digestmod=hashlib.sha256
        ).digest()).decode()
        ws.send(json.dumps({
            "Id": self.id,
            "Request": "Login",
            "Params": {
                "AuthType": "HMAC",
                "WebApiId":  self.configService.get_web_api_id(),
                "WebApiKey": self.configService.get_web_api_key(),
                "Timestamp": timestamp,
                "Signature": base64HmacSignature,
                "DeviceId":  "123",
                "AppSessionId":  "123"
            }
        }))

    def on_message(self, ws, message):
        print("received feed message:", message)

    def on_error(self, ws, error):
        print(error)

    def on_close(self, ws, close_status_code, close_msg):
        print("### closed ###")

    def on_open(self, ws):
        print("Opened feed connection")
        self.send_auth_message(ws)

    def init_websocket(self):
        ws = websocket.WebSocketApp(self.websocket_feed_url,  # type: ignore
                                    on_open=self.on_open,
                                    on_message=self.on_message,
                                    on_error=self.on_error,
                                    on_close=self.on_close)
        Thread(target=ws.run_forever).start()
