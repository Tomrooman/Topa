from typing import Any, Literal
import json
import websocket
from threading import Thread
from config.config_service import ConfigService
from bot.fxopen.fxopen_api import Periodicity
from .fxopen_websocket_manager import FxOpenWebsocketManager


class FxOpenFeedWebsocket(FxOpenWebsocketManager):
    id = 'Topa-feed'
    websocket_feed_url = ''
    configService = ConfigService()
    ws: websocket.WebSocketApp  # type: ignore
    botService: Any

    def __init__(self, environment: Literal['prod', 'demo'], botService: Any):
        if (environment == 'prod'):
            self.websocket_feed_url = 'wss://ttlivewebapi.fxopen.net:3000'
            self.id += '-prod'
        elif (environment == 'demo'):
            self.websocket_feed_url = 'wss://ttdemowebapi.soft-fx.com:2083'
            self.id += '-demo'
        else:
            raise Exception('Invalid environment')

        self.botService = botService
        self.init_websocket(
            websocket_url=self.websocket_feed_url, enableTrace=False)

    def on_message(self, ws, message):
        print("received feed message:", message)
        if (message['Response'] == 'FeedBarUpdate'):
            print('bar update')
            # add candle on websocket if candle closed with periodicity

    def on_error(self, ws, error):
        print(error)

    def on_close(self, ws, close_status_code, close_msg):
        print("### closed ###")

    def on_open(self, ws):
        print("Opened feed connection")
        self.send_auth_message(ws, self.id)

    def candle_subscribe_message(self, periodicity: Periodicity):
        self.ws.send(json.dumps({
            "Id": self.id,
            "Request": "BarFeedSubscribe",
            "Params":
            {
                "Subscribe":
                [{
                    "Symbol": 'EURUSD',
                    "BarParams":
                    [{
                        "Periodicity": periodicity,
                        "PriceType": 'Ask'
                    }]
                }]
            }
        }))

    def init_websocket(self, websocket_url: str, enableTrace: bool) -> None:
        websocket.enableTrace(enableTrace)
        self.ws = websocket.WebSocketApp(websocket_url,  # type: ignore
                                         on_open=self.on_open,
                                         on_message=self.on_message,
                                         on_error=self.on_error,
                                         on_close=self.on_close)
        Thread(target=self.ws.run_forever).start()
