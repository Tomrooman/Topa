from typing import Any, Literal
import json
import websocket
from threading import Thread
from config.config_service import ConfigService
from .fxopen_websocket_manager import FxOpenWebsocketManager


class FxOpenTradeWebsocket(FxOpenWebsocketManager):
    id = 'Topa-trade'
    websocket_trade_url = ''
    configService = ConfigService()
    ws: websocket.WebSocketApp  # type: ignore
    botService: Any

    def __init__(self, environment: Literal['prod', 'demo'], botService: Any):
        if (environment == 'prod'):
            self.websocket_trade_url = 'wss://ttlivewebapi.fxopen.net:3001'
            self.id += '-prod'
        elif (environment == 'demo'):
            self.websocket_trade_url = 'wss://ttdemowebapi.soft-fx.com:2087'
            self.id += '-demo'
        else:
            raise Exception('Invalid environment')
        self.botService = botService
        self.init_websocket(
            websocket_url=self.websocket_trade_url, enableTrace=False)

    def on_message(self, ws, message):
        print("received trade message:", message)

        if (message['Response'] == 'ExecutionReport'):
            print('execution report')
            if (message["Result"]["Event"] == 'Canceled'):
                print('trade canceled')

        if (message['Response'] == 'TradeCreate'):
            print('trade create')

    def on_error(self, ws, error):
        print(error)

    def on_close(self, ws, close_status_code, close_msg):
        print("### closed ###")

    def on_open(self, ws):
        print('opened trade connection')
        self.send_auth_message(ws, self.id)

    def trades_subscribe_message(self):
        self.ws.send(json.dumps({
            "Id": self.id,
            "Request": "Trades",
        }))

    def init_websocket(self, websocket_url: str, enableTrace: bool) -> None:
        websocket.enableTrace(enableTrace)
        self.ws = websocket.WebSocketApp(websocket_url,  # type: ignore
                                         on_open=self.on_open,
                                         on_message=self.on_message,
                                         on_error=self.on_error,
                                         on_close=self.on_close)
        Thread(target=self.ws.run_forever).start()
