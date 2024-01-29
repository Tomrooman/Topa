from dataclasses import dataclass
from typing import Any, Callable, Literal
import json
import websocket
from threading import Thread
from config.config_service import ConfigService
from .fxopen_websocket_manager import FxOpenWebsocketManager


@dataclass
class BotServiceSharedTradeFunctions:
    handle_canceled_trade_from_websocket: Callable[[str], None]
    handle_closed_trade: Callable[[float, float, int], None]


class FxOpenTradeWebsocket(FxOpenWebsocketManager):
    id = 'Topa-trade'
    websocket_trade_url = ''
    configService = ConfigService()
    ws: websocket.WebSocketApp  # type: ignore
    botService: Any

    def __init__(self, environment: Literal['prod', 'demo'], botService: BotServiceSharedTradeFunctions):
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
        parsed_message = json.loads(message)
        if (parsed_message['Response'] == 'TradeSessionInfo'):
            return

        print("received trade message:", parsed_message)

        if (parsed_message['Response'] == 'ExecutionReport'):
            if (parsed_message["Result"]["Event"] == 'Canceled'):
                print('trade canceled')
                self.botService.handle_canceled_trade_from_websocket(
                    parsed_message["Result"]["Trade"]["Id"])

            if ("Profit" in parsed_message["Result"] and parsed_message["Result"]["Event"] == 'Filled'):
                print('trade closed')
                self.botService.handle_closed_trade(
                    parsed_message["Result"]["Profit"]["Value"], parsed_message["Result"]["Trade"]["Price"], parsed_message["Result"]["Trade"]["Modified"])

    def on_error(self, ws, error):
        print('trade error:', error)

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
