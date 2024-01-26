import sys  # NOQA
import os  # NOQA
parent_dir = os.path.dirname(os.path.realpath(__file__))  # NOQA
sys.path.append(parent_dir + '/..')  # NOQA
from bot.fxopen.fxopen_trade_websocket import FxOpenTradeWebsocket
from bot.fxopen.fxopen_feed_websocket import FxOpenFeedWebsocket
from bot.bot_manager import BotManager
from bot.fxopen.fxopen_api import FxOpenApi
from database.models.trade_model import TradeModel
from config.config_service import ConfigService
import time


class BotProd(BotManager):
    configService = ConfigService()
    fxopenApi: FxOpenApi

    def __init__(self):
        environment = sys.argv[1]
        self.fxopenApi = FxOpenApi(environment)

    def start(self):
        print('test prod')
        FxOpenTradeWebsocket('demo')
        FxOpenFeedWebsocket('demo')
        # self.set_candles_list()
        # self.set_all_rsi()
        # current_candle, current_candle_start_date, current_candle_close_date = self.get_current_candle_with_start_and_close_date()
        # self.set_current_hour_from_current_candle(current_candle)
        # self.trade = TradeModel.findLast()

        # if (self.trade.is_closed == False):
        #     custom_close = self.check_for_custom_close(
        #         current_candle_close_date)
        #     if (custom_close == 'close_profit'):
        #         print('close_profit')
        #     if (custom_close == 'force_close'):
        #         print('force_close')

        # position = self.check_strategy(current_candle)

        # if (position == 'IDLE'):
        #     return

        # # self.take_position(position, current_candle, current_candle_start_date)

        # print(f'current hour: {self.current_hour}')
        # print(f'current candle start date: {current_candle_start_date}')
        # print(f'current candle close date: {current_candle_close_date}')

    # def take_position(self, side: str, current_candle: Candle, opened_at: datetime):
    #     self.trade.is_closed = False
    #     self.trade.price = current_candle.close
    #     self.trade.opened_at = opened_at.isoformat()
    #     self.trade.type = TradeType(side.lower())
    #     self.trade.position_value = self.get_position_value()

    def set_candles_list(self):
        self.candles_5min_list = self.fxopenApi.get_candles(
            'M5', self.CANDLES_HISTORY_LENGTH)
        self.candles_30min_list = self.fxopenApi.get_candles(
            'M30', self.rsi_30min.period + 1)
        self.candles_1h_list = self.fxopenApi.get_candles(
            'H1', self.rsi_1h.period + 1)
        self.candles_4h_list = self.fxopenApi.get_candles(
            'H4', self.rsi_4h.period + 1)

        print(f'5min candle list length: {len(self.candles_5min_list)}')
        print(f'30min candle list length: {len(self.candles_30min_list)}')
        print(f'1h candle list length: {len(self.candles_1h_list)}')
        print(f'4h candle list length: {len(self.candles_4h_list)}')
        print({
            "rsi_5min": self.rsi_5min.value,
            "rsi_30min": self.rsi_30min.value,
            "rsi_1h": self.rsi_1h.value,
            "rsi_4h": self.rsi_4h.value
        })


if __name__ == '__main__':
    BotProd().start()
