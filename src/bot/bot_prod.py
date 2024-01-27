from datetime import datetime, timezone
import sys  # NOQA
import os

from bson import ObjectId  # NOQA
parent_dir = os.path.dirname(os.path.realpath(__file__))  # NOQA
sys.path.append(parent_dir + '/..')  # NOQA
from typing import Literal
from bot.candle import Candle
from bot.fxopen.fxopen_trade_websocket import FxOpenTradeWebsocket
from bot.fxopen.fxopen_feed_websocket import FxOpenFeedWebsocket
from bot.bot_manager import BotManager
from bot.fxopen.fxopen_api import FxOpenApi, Periodicity
from database.models.trade_model import TradeModel
from config.config_service import ConfigService
import time


class BotProd(BotManager):
    configService = ConfigService()
    fxopenApi: FxOpenApi
    environment: Literal['demo', 'prod'] = 'demo'

    def __init__(self):
        environment_arg = sys.argv[1]
        if (environment_arg == 'prod'):
            self.environment = 'prod'
        elif (environment_arg == 'demo'):
            self.environment = 'demo'
        else:
            raise Exception('Invalid environment')

        self.fxopenApi = FxOpenApi(self.environment)

    def start(self):
        print(f'test {self.environment}')
        self.set_candles_list()
        self.set_all_rsi()
        trade = TradeModel.findLast()

        # if (trade is not None):
        # self.refresh_trade(trade)

        # current_candle, current_candle_start_date, current_candle_close_date = self.get_current_candle_with_start_and_close_date()
        # self.set_current_hour_from_current_candle(current_candle)
        # self.refresh_balance()

        # trade_websocket = FxOpenTradeWebsocket(self.environment, self)
        FxOpenFeedWebsocket(self.environment, self)

        # trade_websocket.trades_subscribe_message()

        # self.test_strategy()

    def test_strategy(self):
        print('process strategy')
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

    def handle_new_candle_from_websocket(self, periodicity: Periodicity, candle: Candle):
        if (periodicity == 'M5'):
            last_candle = self.candles_5min_list[-1]
            if (last_candle.start_timestamp != candle.start_timestamp):
                self.candles_5min_list.append(candle)
                if (len(self.candles_5min_list) > self.CANDLES_HISTORY_LENGTH):
                    del self.candles_5min_list[0]
            self.set_all_rsi()
            self.test_strategy()

        if (periodicity == 'M30'):
            last_candle = self.candles_30min_list[-1]
            if (last_candle.start_timestamp != candle.start_timestamp):
                self.candles_30min_list.append(candle)
                if (len(self.candles_30min_list) > self.CANDLES_HISTORY_LENGTH):
                    del self.candles_30min_list[0]

        if (periodicity == 'H1'):
            last_candle = self.candles_1h_list[-1]
            if (last_candle.start_timestamp != candle.start_timestamp):
                self.candles_1h_list.append(candle)
                if (len(self.candles_1h_list) > self.CANDLES_HISTORY_LENGTH):
                    del self.candles_1h_list[0]

        if (periodicity == 'H4'):
            last_candle = self.candles_4h_list[-1]
            if (last_candle.start_timestamp != candle.start_timestamp):
                self.candles_4h_list.append(candle)
                if (len(self.candles_4h_list) > self.CANDLES_HISTORY_LENGTH):
                    del self.candles_4h_list[0]

    def refresh_balance(self):
        account_info = self.fxopenApi.get_account_info()
        self.balance = account_info.balance
        print({
            "balance": self.balance,
        })

    def refresh_trade(self, trade: TradeModel):
        self.trade._id = trade._id
        fxopen_trade = self.fxopenApi.get_trade_by_id(trade.fxopen_id)
        self.trade.is_closed = fxopen_trade.is_closed
        self.trade.price = fxopen_trade.price
        self.trade.position_value = fxopen_trade.position_value
        self.trade.take_profit = fxopen_trade.take_profit
        self.trade.stop_loss = fxopen_trade.stop_loss
        self.trade.type = fxopen_trade.type
        self.trade.close = fxopen_trade.close
        self.trade.profit = fxopen_trade.profit
        self.trade.fxopen_id = fxopen_trade.fxopen_id
        self.trade.opened_at = fxopen_trade.opened_at
        self.trade.closed_at = fxopen_trade.closed_at
        self.trade.save()
        print('refreshed trade : ', self.trade)

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


if __name__ == '__main__':
    BotProd().start()
