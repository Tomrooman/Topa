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
from database.models.trade_model import DeviseType, TradeModel, TradeType, TradeTypeValues
from config.config_service import ConfigService
from logger.logger_service import LoggerService


class BotProd(BotManager):
    configService = ConfigService()
    loggerService = LoggerService()
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

        devise = "EURUSD" if len(sys.argv) < 3 else sys.argv[2]
        self.devise = DeviseType(devise).value
        self.setTradesDevise(self.devise)
        self.fxopenApi = FxOpenApi(self.environment)

    def start(self):
        self.loggerService.log(f'start {self.environment} {self.devise}')
        self.startup_data(True)

        trade_websocket_shared_functions = BotServiceSharedTradeFunctions(
            # handle_canceled_trade_from_websocket=self.handle_canceled_trade_from_websocket,
            handle_closed_trade=self.handle_closed_trade,
            startup_data=self.startup_data
        )
        FxOpenTradeWebsocket(
            self.environment, trade_websocket_shared_functions)

        feed_websocket_shared_functions = BotServiceSharedFeedFunctions(
            handle_new_candle_from_websocket=self.handle_new_candle_from_websocket,
            startup_data=self.startup_data
        )
        FxOpenFeedWebsocket(self.environment, feed_websocket_shared_functions)

    def startup_data(self, startup=False):
        self.loggerService.log(f'startup data {self.environment}')
        self.set_candles_list()
        self.set_all_rsi()
        self.refresh_trades()
        self.refresh_balance()
        if (startup == False):
            self.test_strategy()

    def test_strategy(self):
        self.set_all_rsi()
        self.loggerService.log('process strategy')

        for trade in [self.trade_buy, self.trade_sell]:
            if (trade.is_closed == False):
                custom_close = self.check_for_custom_close()
                if (custom_close == 'close_profit'):
                    self.loggerService.log('check close_profit')
                    self.check_close_in_profit(trade.type)
                if (custom_close == 'force_close'):
                    self.loggerService.log('check force_close')
                    self.fxopenApi.close_trade(trade.fxopen_id)

        position = self.check_strategy()
        if (position == 'Idle'):
            self.loggerService.log(
                f'trade buy is open: {not self.trade_buy.is_closed}')
            self.loggerService.log(
                f'trade sell is open: {not self.trade_sell.is_closed}')
            self.loggerService.log(f'buy triggered: {self.buy_triggered}')
            self.loggerService.log(f'sell triggered: {self.sell_triggered}')
            return

        if (position == TradeType.BUY and self.trade_buy.is_closed == False):
            return
        if (position == TradeType.SELL and self.trade_sell.is_closed == False):
            return

        if (position == TradeType.SELL and self.trade_buy.is_closed == False):
            self.fxopenApi.close_trade(self.trade_buy.fxopen_id)
            return

        if (position == TradeType.BUY and self.trade_sell.is_closed == False):
            self.fxopenApi.close_trade(self.trade_sell.fxopen_id)
            return

        position_value = self.get_position_value()
        new_trade_id = ObjectId()
        if (position == TradeType.BUY):
            fxopen_trade = self.fxopenApi.create_trade(
                devise=self.devise, side=position, amount=position_value, stop_loss=self.trade_buy.stop_loss, take_profit=self.trade_buy.take_profit, comment=new_trade_id)
            self.trade_buy = fxopen_trade
            self.indicators_buy._id = ObjectId()
            self.indicators_buy.type = self.trade_buy.type
            self.indicators_buy.trade_id = new_trade_id
            self.indicators_buy.save()
            self.trade_buy.save()
        elif (position == TradeType.SELL):
            fxopen_trade = self.fxopenApi.create_trade(
                devise=self.devise, side=position, amount=position_value, stop_loss=self.trade_sell.stop_loss, take_profit=self.trade_sell.take_profit, comment=new_trade_id)
            self.trade_sell = fxopen_trade
            self.indicators_sell._id = ObjectId()
            self.indicators_sell.type = self.trade_sell.type
            self.indicators_sell.trade_id = new_trade_id
            self.indicators_sell.save()
            self.trade_sell.save()

        self.loggerService.log(
            f'trade buy is open: {not self.trade_buy.is_closed}')
        self.loggerService.log(
            f'trade sell is open: {not self.trade_sell.is_closed}')
        self.loggerService.log(f'buy triggered: {self.buy_triggered}')
        self.loggerService.log(f'sell triggered: {self.sell_triggered}')

    def check_close_in_profit(self, type: TradeType):
        last_candle = self.get_last_candle()
        if (type.value == TradeType.SELL and last_candle.close <= self.trade_sell.price):
            self.fxopenApi.close_trade(self.trade_sell.fxopen_id)
        elif (type.value == TradeType.BUY and last_candle.close >= self.trade_buy.price):
            self.fxopenApi.close_trade(self.trade_buy.fxopen_id)

    def handle_new_candle_from_websocket(self, periodicity: Periodicity, candle: Candle):
        if (periodicity == 'M5'):
            last_candle = self.candles_5min_list[-1]
            if (last_candle.start_timestamp != candle.start_timestamp):
                self.candles_5min_list.append(candle)
                if (len(self.candles_5min_list) > self.CANDLES_HISTORY_LENGTH):
                    del self.candles_5min_list[0]
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

    # def handle_canceled_trade_from_websocket(self, fxopen_id: str):
    #     self.trade.is_closed = True
    #     self.trade.status = 'Canceled'
    #     self.trade.save()

    def handle_closed_trade(self, type: TradeTypeValues, trade_profit: float, close_price: float, comission: float, closed_at_timestamp: int):
        if (type == TradeType.BUY):
            self.trade_buy.is_closed = True
            self.trade_buy.closed_at = datetime.fromtimestamp(
                closed_at_timestamp / 1000, tz=timezone.utc).isoformat()
            self.trade_buy.profit = str(trade_profit)
            self.indicators_buy.profit = str(trade_profit)
            self.trade_buy.close = close_price
            self.trade_buy.comission = comission
            self.trade_buy.save()
            self.indicators_buy.save()
        elif (type == TradeType.SELL):
            self.trade_sell.is_closed = True
            self.trade_sell.closed_at = datetime.fromtimestamp(
                closed_at_timestamp / 1000, tz=timezone.utc).isoformat()
            self.trade_sell.profit = str(trade_profit)
            self.indicators_sell.profit = str(trade_profit)
            self.trade_sell.close = close_price
            self.trade_sell.comission = comission
            self.trade_sell.save()
            self.indicators_sell.save()
        self.refresh_balance()

    def refresh_balance(self):
        account_info = self.fxopenApi.get_account_info()
        self.balance = account_info.balance
        self.loggerService.log(f"refreshed balance: {self.balance}")

    def refresh_trades(self):
        trade_buy = TradeModel.findLast(TradeType.BUY, self.devise)
        trade_sell = TradeModel.findLast(TradeType.SELL, self.devise)
        for trade in [trade_buy, trade_sell]:
            if (trade is not None and trade.fxopen_id != ''):
                fxopen_trade = self.fxopenApi.get_trade_by_id(trade.fxopen_id)
                if (fxopen_trade is not None):
                    self.loggerService.log(
                        f'fx open trade : {fxopen_trade.to_json()}')
                if (trade.type.value == TradeType.BUY):
                    self.trade_buy = fxopen_trade if fxopen_trade != None else trade
                    self.trade_buy.is_closed = True if fxopen_trade == None else fxopen_trade.is_closed
                    self.trade_buy.close = trade.close if fxopen_trade == None else fxopen_trade.close
                    self.trade_buy.profit = trade.profit if fxopen_trade == None else fxopen_trade.profit
                    self.trade_buy.closed_at = trade.closed_at if fxopen_trade == None else fxopen_trade.closed_at
                    self.trade_buy.comission = trade.comission if fxopen_trade == None else fxopen_trade.comission
                    self.trade_buy.save()
                    self.loggerService.log(
                        f'refreshed BUY trade: {self.trade_buy.to_json()}')
                if (trade.type.value == TradeType.SELL):
                    self.trade_sell = fxopen_trade if fxopen_trade != None else trade
                    self.trade_sell.is_closed = True if fxopen_trade == None else fxopen_trade.is_closed
                    self.trade_sell.close = trade.close if fxopen_trade == None else fxopen_trade.close
                    self.trade_sell.profit = trade.profit if fxopen_trade == None else fxopen_trade.profit
                    self.trade_sell.closed_at = trade.closed_at if fxopen_trade == None else fxopen_trade.closed_at
                    self.trade_sell.comission = trade.comission if fxopen_trade == None else fxopen_trade.comission
                    self.trade_sell.save()
                    self.loggerService.log(
                        f'refreshed SELL trade: {self.trade_sell.to_json()}')

    def set_candles_list(self):
        self.candles_5min_list = self.fxopenApi.get_candles(
            'M5', self.CANDLES_HISTORY_LENGTH)
        self.candles_30min_list = self.fxopenApi.get_candles(
            'M30', self.rsi_30min.period + 1)
        self.candles_1h_list = self.fxopenApi.get_candles(
            'H1', self.rsi_1h.period + 1)
        self.candles_4h_list = self.fxopenApi.get_candles(
            'H4', self.rsi_4h.period + 1)

        self.loggerService.log(
            f'5min candle list length: {len(self.candles_5min_list)}')
        self.loggerService.log(
            f'30min candle list length: {len(self.candles_30min_list)}')
        self.loggerService.log(
            f'1h candle list length: {len(self.candles_1h_list)}')
        self.loggerService.log(
            f'4h candle list length: {len(self.candles_4h_list)}')


if __name__ == '__main__':
    BotProd().start()
