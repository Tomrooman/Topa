from typing import Literal
import json
import websocket
from threading import Thread


class FxOpenFeedWebsocket():
    websocket_feed_url = ''

    def __init__(self, environment: Literal['prod', 'demo']):
        if (environment == 'prod'):
            self.websocket_feed_url = 'wss://ttlivewebapi.fxopen.net:3000'
        elif (environment == 'demo'):
            self.websocket_feed_url = 'wss://ttdemowebapi.soft-fx.com:2083'
        else:
            raise Exception('Invalid environment')

        websocket.enableTrace(False)
        self.init_websocket()

    def on_message(self, ws, message):
        print(message)

    def on_error(self, ws, error):
        print(error)

    def on_close(self, ws, close_status_code, close_msg):
        print("### closed ###")

    def on_open(self, ws):
        print("Opened feed connection")
        ws.send(json.dumps({
            "Id": "123",
            "Request": "BarFeedSubscribe",
            "Params":
            {
                "Subscribe":
                [{
                    "Symbol": 'EURUSD',
                    "BarParams":
                    [{
                        "Periodicity": "M5",
                        "PriceType": "Ask"
                    }]
                }]
            }
        }))

    def init_websocket(self):
        ws = websocket.WebSocketApp(self.websocket_feed_url,  # type: ignore
                                    on_open=self.on_open,
                                    on_message=self.on_message,
                                    on_error=self.on_error,
                                    on_close=self.on_close)
        Thread(target=ws.run_forever).start()
