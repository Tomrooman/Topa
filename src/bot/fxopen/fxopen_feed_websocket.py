from typing import Any, Literal
import json
import websocket
from threading import Thread
from config.config_service import ConfigService
from bot.fxopen.fxopen_api import Periodicity
from bot.candle import Candle
from .fxopen_websocket_manager import FxOpenWebsocketManager


class FxOpenFeedWebsocket(FxOpenWebsocketManager):
    id = 'Topa-feed'
    websocket_feed_url = ''
    configService = ConfigService()
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

    def convert_candle_update_to_candle(self, candle_update: dict, close: float):
        return Candle(symbol=candle_update['SymbolAlias'], start_timestamp=candle_update['Time'], open=candle_update['Open'],
                      high=candle_update['High'], low=candle_update['Low'], close=close)

    def on_message(self, ws, message):
        parsed_message = json.loads(message)
        print("received feed message:", parsed_message)
        if (parsed_message['Response'] == 'FeedBarUpdate'):
            result = parsed_message['Result']
            updates = result['Updates']
            candle_5min_update = next((
                x for x in updates if x.Periodicity == "M5"), None)
            candle_30min_update = next((
                x for x in updates if x.Periodicity == "M30"), None)
            candle_1h_update = next(
                (x for x in updates if x.Periodicity == "H1"), None)
            candle_4h_update = next(
                (x for x in updates if x.Periodicity == "H4"), None)

            if (candle_30min_update is not None):
                self.botService.handle_new_candle_from_websocket(
                    'M30', self.convert_candle_update_to_candle(candle_30min_update, result['AskClose']))
            if (candle_1h_update is not None):
                self.botService.handle_new_candle_from_websocket(
                    'H1', self.convert_candle_update_to_candle(candle_1h_update, result['AskClose']))
            if (candle_4h_update is not None):
                self.botService.handle_new_candle_from_websocket(
                    'H4', self.convert_candle_update_to_candle(candle_4h_update, result['AskClose']))
            #  check 5min at last to trigger test strategy function with all candles updated
            if (candle_5min_update is not None):
                self.botService.handle_new_candle_from_websocket(
                    'M5', self.convert_candle_update_to_candle(candle_5min_update, result['AskClose']))

    def on_error(self, ws, error):
        print('feed error:', error)

    def on_close(self, ws, close_status_code, close_msg):
        print("### closed ###")

    def on_open(self, ws):
        print("Opened feed connection")
        self.send_auth_message(ws, self.id)

        self.candle_subscribe_message(ws, ['M5', 'M30', 'H1', 'H4'])

    def candle_subscribe_message(self, ws, periodicityList: list[Periodicity]):
        ws.send(json.dumps({
                "Id": self.id,
                "Request": "BarFeedSubscribe",
                "Params":
                {
                    "Subscribe":
                    [{
                        "Symbol": 'EURUSD',
                        "BarParams": [{
                            "Periodicity": periodicity,
                            "PriceType": 'Ask'
                        } for periodicity in periodicityList]

                    }]
                }
                }))

    def init_websocket(self, websocket_url: str, enableTrace: bool) -> None:
        websocket.enableTrace(enableTrace)
        ws = websocket.WebSocketApp(websocket_url,  # type: ignore
                                    on_open=self.on_open,
                                    on_message=self.on_message,
                                    on_error=self.on_error,
                                    on_close=self.on_close)
        Thread(target=ws.run_forever).start()
