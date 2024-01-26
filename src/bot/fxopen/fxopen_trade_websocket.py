from typing import Literal
import json
import websocket
from threading import Thread


class FxOpenTradeWebsocket():
    websocket_trade_url = ''

    def __init__(self, environment: Literal['prod', 'demo']):
        if (environment == 'prod'):
            self.websocket_trade_url = 'wss://ttlivewebapi.fxopen.net:3001'
        elif (environment == 'demo'):
            self.websocket_trade_url = 'wss://ttdemowebapi.soft-fx.com:2087'
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

    def on_open_trade_connection(self, ws):
        print('opened trade connection')

    def init_websocket(self):
        ws = websocket.WebSocketApp(self.websocket_trade_url,  # type: ignore
                                    on_open=self.on_open_trade_connection,
                                    on_message=self.on_message,
                                    on_error=self.on_error,
                                    on_close=self.on_close)
        Thread(target=ws.run_forever).start()
