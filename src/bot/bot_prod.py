from datetime import datetime, timezone
from dateutil import relativedelta
from bson import ObjectId
import sys  # NOQA
import os  # NOQA
parent_dir = os.path.dirname(os.path.realpath(__file__))  # NOQA
sys.path.append(parent_dir + '/..')  # NOQA
from typing import Literal
from bot.candle import Candle
from bot.fxopen.fxopen_trade_websocket import BotServiceSharedTradeFunctions, FxOpenTradeWebsocket
from bot.fxopen.fxopen_feed_websocket import BotServiceSharedFeedFunctions, FxOpenFeedWebsocket
from bot.bot_manager import BotManager
from bot.fxopen.fxopen_api import FxOpenApi, Periodicity
from database.models.trade_model import TradeModel
from config.config_service import ConfigService


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
        print(f'start {self.environment}')
        self.startup_data()

        trade_websocket_shared_functions = BotServiceSharedTradeFunctions(
            handle_canceled_trade_from_websocket=self.handle_canceled_trade_from_websocket,
            handle_closed_trade=self.handle_closed_trade,
            handle_filled_trade_from_websocket=self.handle_filled_trade_from_websocket
        )
        FxOpenTradeWebsocket(
            self.environment, trade_websocket_shared_functions)

        feed_websocket_shared_functions = BotServiceSharedFeedFunctions(
            handle_new_candle_from_websocket=self.handle_new_candle_from_websocket,
            startup_data=self.startup_data
        )
        FxOpenFeedWebsocket(self.environment, feed_websocket_shared_functions)

        # TEMP TO REMOVE TO TEST TRADE
        current_candle = self.get_last_candle()
        previous_candles = self.candles_5min_list[-self.CANDLES_HISTORY_LENGTH:]
        higher_previous_price = max(
            [candle.high for candle in previous_candles])
        self.trade.take_profit = higher_previous_price
        self.trade.stop_loss = current_candle.close - \
            ((higher_previous_price - current_candle.close) / 2)
        position_value = self.get_position_value()
        fxopen_trade_id = self.fxopenApi.create_trade(
            side='Buy', amount=position_value, stop_loss=self.trade.stop_loss, take_profit=self.trade.take_profit, comment=self.trade._id)

        current_timestamp = round(datetime.now(
            tz=timezone.utc).timestamp() * 1000)
        self.trade._id = ObjectId()
        self.trade.position_value = position_value
        self.trade.fxopen_id = fxopen_trade_id
        self.trade.opened_at = datetime.fromtimestamp(
            current_timestamp / 1000, tz=timezone.utc).isoformat()
        self.trade.opened_at_timestamp = current_timestamp
        self.trade.closed_at = ''
        self.trade.is_closed = False
        self.trade.is_confirmed = False
        self.trade.save()
        # TEMP TO REMOVE TO TEST TRADE

    def startup_data(self):
        print(f'startup data {self.environment}')
        self.set_candles_list()
        self.set_all_rsi()
        self.refresh_trade()
        self.refresh_balance()

    def test_strategy(self):
        self.set_all_rsi()
        print('process strategy')

        if (self.trade.is_closed == False and self.trade.is_confirmed == False):
            trade_start_date = datetime.fromtimestamp(
                self.trade.opened_at_timestamp / 1000, tz=timezone.utc)
            now_date = datetime.now(tz=timezone.utc)
            difference = relativedelta.relativedelta(
                trade_start_date, now_date)

            if (difference.minutes < 1):
                return

            self.refresh_trade()

        if (self.trade.is_closed == False and self.trade.is_confirmed == True):
            custom_close = self.check_for_custom_close()
            if (custom_close == 'close_profit'):
                self.check_close_in_profit()
                self.handle_closed_trade()
                print('close_profit')
            if (custom_close == 'force_close'):
                print('force_close')
                self.fxopenApi.close_trade(self.trade.fxopen_id)
                self.handle_closed_trade()
            return

        if (self.trade.is_closed == False and self.trade.is_confirmed == True):
            position = self.check_strategy()

            if (position == 'Idle'):
                return

            position_value = self.get_position_value()
            self.trade._id = ObjectId()
            fxopen_trade_id = self.fxopenApi.create_trade(
                side=position, amount=position_value, stop_loss=self.trade.stop_loss, take_profit=self.trade.take_profit, comment=self.trade._id)
            current_timestamp = round(datetime.now(
                tz=timezone.utc).timestamp() * 1000)
            self.trade.position_value = position_value
            self.trade.fxopen_id = fxopen_trade_id
            self.trade.opened_at = datetime.fromtimestamp(
                current_timestamp / 1000, tz=timezone.utc).isoformat()
            self.trade.opened_at_timestamp = current_timestamp
            self.trade.closed_at = ''
            self.trade.is_closed = False
            self.trade.is_confirmed = False
            self.trade.save()

    def check_close_in_profit(self):
        last_candle = self.get_last_candle()
        if ((self.trade.type.value == 'sell' and last_candle.close <= self.trade.price) or (self.trade.type.value == 'buy' and last_candle.close >= self.trade.price)):
            self.fxopenApi.close_trade(self.trade.fxopen_id)

    def handle_new_candle_from_websocket(self, periodicity: Periodicity, candle: Candle):
        if (periodicity == 'M5'):
            last_candle = self.candles_5min_list[-1]
            if (last_candle.start_timestamp != candle.start_timestamp):
                self.candles_5min_list.append(candle)
                if (len(self.candles_5min_list) > self.CANDLES_HISTORY_LENGTH):
                    del self.candles_5min_list[0]
            # self.test_strategy()

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

    def handle_canceled_trade_from_websocket(self, fxopen_id: str):
        self.fxopenApi.close_trade(fxopen_id)
        self.trade.is_closed = True
        self.trade.is_confirmed = True
        self.trade.status = 'Canceled'
        self.trade.save()

    def handle_filled_trade_from_websocket(self):
        self.trade.is_closed = False
        self.trade.is_confirmed = True
        self.trade.status = 'Filled'
        self.trade.save()

    def handle_closed_trade(self):
        self.refresh_trade()
        self.refresh_balance()

    def refresh_balance(self):
        account_info = self.fxopenApi.get_account_info()
        self.balance = account_info.balance
        print({
            "refreshed balance": self.balance,
        })

    def refresh_trade(self):
        trade = TradeModel.findLast()
        if (trade is not None and trade.fxopen_id != ''):
            self.trade._id = trade._id
            fxopen_trade = self.fxopenApi.get_trade_by_id(trade.fxopen_id)
            self.trade.is_closed = fxopen_trade.is_closed
            self.trade.price = fxopen_trade.price
            self.trade.position_value = fxopen_trade.position_value
            self.trade.take_profit = fxopen_trade.take_profit
            self.trade.stop_loss = fxopen_trade.stop_loss
            self.trade.status = fxopen_trade.status
            self.trade.is_confirmed = fxopen_trade.is_confirmed
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
