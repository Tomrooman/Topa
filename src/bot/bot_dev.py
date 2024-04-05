from ast import Raise
from datetime import datetime, timezone
from bson import ObjectId
import pandas as pd
import json
import curses
import sys  # NOQA
import os  # NOQA
parent_dir = os.path.dirname(os.path.realpath(__file__))  # NOQA
sys.path.append(parent_dir + '/..')  # NOQA
from bot.bot_manager import BotManager
from database.models.trade_model import DeviseType, TradeModel, TradeType, TradeTypeValues
from database.models.indicators_model import IndicatorsModel
from bot.candle import Candle, create_from_csv_line
from api.routes.stats.stats_service import StatsService
from logger.logger_service import LoggerService


class BotDev(BotManager):
    loggerService = LoggerService()
    stdscr = curses.initscr()
    opened_both_side_count = 0

    last_candle_5min_minute = 0
    last_candle_5min_hour = 0
    last_candle_5min_day = 0

    candle_5min_start_date = None
    candle_30min_start_date = None
    candle_1h_start_date = None
    candle_4h_start_date = None

    def start(self):
        devise = "EURUSD" if len(sys.argv) < 2 else sys.argv[1]
        devise = DeviseType(devise).value
        self.setDevise(devise)
        self.open_file_5min = pd.read_csv(
            f"data/month_debug/{devise}_5min.csv", chunksize=1)
        self.open_file_30min = pd.read_csv(
            f"data/month_debug/{devise}_30min.csv", chunksize=1)
        self.open_file_1h = pd.read_csv(
            f"data/month_debug/{devise}_1h.csv", chunksize=1)
        self.open_file_4h = pd.read_csv(
            f"data/month_debug/{devise}_4h.csv", chunksize=1)

        f = open("data/diff_to_high.txt", "w")
        f.write("")
        f.close()

        self.stdscr.clear()
        # Drop trades table
        TradeModel.drop_table()
        IndicatorsModel.drop_table()

        candle_5min = create_from_csv_line(
            self.open_file_5min.get_chunk().values[0])
        # self.candles_30min_list.append(create_from_csv_line(
        #     self.open_file_30min.get_chunk().values[0]))
        # self.candles_1h_list.append(create_from_csv_line(
        #     self.open_file_1h.get_chunk().values[0]))
        # self.candles_4h_list.append(create_from_csv_line(
        #     self.open_file_4h.get_chunk().values[0]))

        try:
            while (candle_5min != None):
                self.candle_5min_start_date = datetime.fromtimestamp(
                    candle_5min.start_timestamp / 1000, tz=timezone.utc)
                try:
                    self.candle_30min_start_date = datetime.fromtimestamp(
                        self.candles_30min_list[-1].start_timestamp / 1000, tz=timezone.utc)
                except:
                    self.candle_30min_start_date = None

                try:
                    self.candle_1h_start_date = datetime.fromtimestamp(
                        self.candles_1h_list[-1].start_timestamp / 1000, tz=timezone.utc)
                except:
                    self.candle_1h_start_date = None

                try:
                    self.candle_4h_start_date = datetime.fromtimestamp(
                        self.candles_4h_list[-1].start_timestamp / 1000, tz=timezone.utc)
                except:
                    self.candle_4h_start_date = None

                self.stdscr.clear()
                self.stdscr.addstr(
                    0, 0, f'Candle 5m start date: {self.candle_5min_start_date}')
                self.stdscr.addstr(
                    1, 0, f'Candle 30m start date: {self.candle_30min_start_date}')
                self.stdscr.addstr(
                    2, 0, f'Candle 1h start date: {self.candle_1h_start_date}')
                self.stdscr.addstr(
                    3, 0, f'Candle 4h start date: {self.candle_4h_start_date}')
                self.stdscr.addstr(4, 0, f'Balance: {self.balance}')
                self.stdscr.addstr(
                    5, 0, f'Trade buy is open: {not self.trade_buy.is_closed}')
                self.stdscr.addstr(
                    6, 0, f'Trade sell is open: {not self.trade_sell.is_closed}')
                self.stdscr.addstr(
                    7, 0, f'Trade buy triggered: {self.buy_triggered}')
                self.stdscr.addstr(
                    8, 0, f'Trade sell triggered: {self.sell_triggered}')
                self.stdscr.addstr(
                    9, 0, f'Opened buy/sell trades at the same time: {self.opened_both_side_count}')
                self.stdscr.addstr(10, 0, f'Max balance: {self.max_balance}')
                self.stdscr.addstr(11, 0,
                                   f'Current drawdown: {self.current_drawdown}% -> {round(self.max_balance * (self.current_drawdown / 100), 4)}€')
                self.stdscr.addstr(12, 0,
                                   f'Max drawdown: {self.max_drawdown}%')
                self.stdscr.addstr(13, 0,
                                   f'Devise: {"EURUSD" if len(sys.argv) < 2 else sys.argv[1]}')
                try:
                    # if (self.candle_5min_start_date.strftime('%Y-%m-%d %H:%M:%S') == '2024-03-04 08:50:00'):
                    #     raise Exception('Stop here')
                    candle_5min = self.set_candles_list(candle_5min)
                except Exception as e:
                    candle_5min = None
                    continue
                else:
                    if (len(self.candles_5min_list) >= self.rsi_5min.period and len(self.candles_30min_list) >= self.rsi_30min.period and len(self.candles_1h_list) >= self.rsi_1h.period and len(self.candles_4h_list) >= self.rsi_4h.period):
                        self.set_all_rsi()
                    if (self.rsi_5min.value != 0 and self.rsi_30min.value != 0 and self.rsi_1h.value != 0 and self.rsi_4h.value != 0):
                        self.test_strategy()
                    self.stdscr.addstr(14, 0, '----------')
                    self.stdscr.refresh()
            curses.endwin()
            self.print_final_backtest_message()

        except KeyboardInterrupt:
            curses.endwin()
            self.print_final_backtest_message()
            pass

    def print_final_backtest_message(self):
        total_trades = TradeModel.findAll()

        self.loggerService.log('\n----- Backtest done -----', False, '\n', '')
        self.loggerService.log(
            f'rsi: {self.rsi_5min.value}, {self.rsi_30min.value}, {self.rsi_1h.value}, {self.rsi_4h.value}', False, '\n', '')
        self.loggerService.log(
            f'Candle 5m start date: {self.candle_5min_start_date}', False, '\n', '')
        self.loggerService.log(
            f'Candle 30m start date: {self.candle_30min_start_date}', False, '\n', '')
        self.loggerService.log(
            f'Candle 1h start date: {self.candle_1h_start_date}', False, '\n', '')
        self.loggerService.log(
            f'Candle 4h start date: {self.candle_4h_start_date}', False, '\n', '')
        self.loggerService.log(
            f'Total trades: {len(total_trades)}', False, '\n', '')
        self.loggerService.log(f'Balance: {self.balance}', False, '\n', '')
        self.loggerService.log(
            f'Trade buy is open: {not self.trade_buy.is_closed}', False, '\n', '')
        self.loggerService.log(
            f'Trade sell is open: {not self.trade_sell.is_closed}', False, '\n', '')
        self.loggerService.log(
            f'Trade buy triggered: {self.buy_triggered}', False, '\n', '')
        self.loggerService.log(
            f'Trade sell triggered: {self.sell_triggered}', False, '\n', '')
        self.loggerService.log(
            f'Opened buy/sell trades at the same time: {self.opened_both_side_count}', False, '\n', '')
        self.loggerService.log(
            f'Max balance: {self.max_balance}', False, '\n', '')
        self.loggerService.log(
            f'Current drawdown: {self.current_drawdown}% -> {round(self.max_balance * (self.current_drawdown / 100), 4)}€', False, '\n', '')
        self.loggerService.log(
            f'Max drawdown: {self.max_drawdown}%', False, '\n', '')
        self.loggerService.log(
            f'Devise: {self.devise}', False, '\n', ''
        )

        stats = json.loads(StatsService().handle_route())
        losing_months = stats["analytics"]["losingMonths"]
        time_to_comeback = stats["timeToComeback"]
        time_to_comback_in_row = 0
        higher_losing_months_percentage = 0
        max_losing_month_in_row = 0
        if (len(time_to_comeback) > 0):
            time_to_comback_in_row = max(
                [time["losingMonthsCount"] for time in time_to_comeback])

        if (len(losing_months) > 0):
            higher_losing_months_percentage = max(
                [abs(month["percentage_from_balance"]) for month in losing_months])

        if (len(losing_months) > 0):
            max_losing_month_in_row = max(
                [month["inRow"] for month in losing_months])
        self.loggerService.log(
            f'Losing months length: {len(losing_months)}', False, '\n', '')
        self.loggerService.log(
            f'Max losing months in a row: {max_losing_month_in_row}', False, '\n', '')
        self.loggerService.log(
            f'Higher loss in one month: {higher_losing_months_percentage}%', False, '\n', '')
        self.loggerService.log(
            f'Time to comeback length: {len(time_to_comeback)}', False, '\n', '')
        self.loggerService.log(
            f'Time to comeback in a row: {time_to_comback_in_row}', False, '\n', '')
        self.loggerService.log(
            f'Positive trades: {len(stats["positiveTrades"]["trades"])} -> {stats["positiveTrades"]["percentageOfTotalTrades"]}%', False, '\n', '')
        self.loggerService.log(
            f'Negative trades: {len(stats["negativeTrades"]["trades"])} -> {stats["negativeTrades"]["percentageOfTotalTrades"]}%', False, '\n', '')

    def set_candles_list(self, candle_5min: Candle) -> Candle:
        current_candle_5min_start_date = datetime.fromtimestamp(
            candle_5min.start_timestamp / 1000, tz=timezone.utc)
        current_candle_5min_minute = current_candle_5min_start_date.minute
        current_candle_5min_hour = current_candle_5min_start_date.hour
        current_candle_5min_day = current_candle_5min_start_date.day

        if (len(self.candles_5min_list) != 0):
            # last_candle_5min_start_date = datetime.fromtimestamp(
            #     self.candles_5min_list[-1].start_timestamp / 1000, tz=timezone.utc)
            # diff_minutes = (current_candle_5min_start_date -
            #                 last_candle_5min_start_date).total_seconds() / 60

            # if (diff_minutes > 10 and current_candle_5min_start_date.hour != 23 and current_candle_5min_start_date.hour != 0):
            #     # print('## Difference minutes too high, drop all candles list ##')
            #     if (self.trade_sell.is_closed == False):
            #         self.check_to_close_trade(
            #             self.trade_sell, self.indicators_sell, 'force_loss')

            #     if (self.trade_buy.is_closed == False):
            #         self.check_to_close_trade(
            #             self.trade_buy, self.indicators_buy, 'force_loss')

            #     f = open("data/diff_to_high.txt", "a")
            #     f.write(
            #         f"Difference minutes too high, drop all candles list\n{last_candle_5min_start_date.isoformat()}\n{current_candle_5min_start_date.isoformat()}\ndiff minutes:{diff_minutes}\n\n")
            #     f.close()
            #     self.buy_triggered = False
            #     self.sell_triggered = False
            #     self.candles_5min_list = []
            #     self.candles_30min_list = []
            #     self.rsi_5min.value = 0
            #     self.rsi_30min.value = 0
            #     if (diff_minutes >= 20):
            #         self.candles_1h_list = []
            #         self.candles_4h_list = []
            #         self.rsi_1h.value = 0
            #         self.rsi_4h.value = 0

            if ((self.last_candle_5min_minute < 30 and current_candle_5min_minute >= 30)
                or (self.last_candle_5min_minute >= 30 and current_candle_5min_minute < 30)
                or self.last_candle_5min_hour != current_candle_5min_hour
                    or self.last_candle_5min_day != current_candle_5min_day):
                self.candles_30min_list.append(create_from_csv_line(
                    self.open_file_30min.get_chunk().values[0]))

            if (current_candle_5min_hour != self.last_candle_5min_hour or current_candle_5min_day != self.last_candle_5min_day):
                self.candles_1h_list.append(create_from_csv_line(
                    self.open_file_1h.get_chunk().values[0]))

            if (((self.last_candle_5min_hour < 4 and current_candle_5min_hour >= 4)
                 or (self.last_candle_5min_hour >= 4 and self.last_candle_5min_hour < 8 and current_candle_5min_hour >= 8)
                 or (self.last_candle_5min_hour >= 8 and self.last_candle_5min_hour < 12 and current_candle_5min_hour >= 12)
                 or (self.last_candle_5min_hour >= 12 and self.last_candle_5min_hour < 16 and current_candle_5min_hour >= 16)
                 or (self.last_candle_5min_hour >= 16 and self.last_candle_5min_hour < 20 and current_candle_5min_hour >= 20)
                 or (self.last_candle_5min_hour >= 20 and current_candle_5min_hour < 20))
                    or self.last_candle_5min_day != current_candle_5min_day):
                self.candles_4h_list.append(create_from_csv_line(
                    self.open_file_4h.get_chunk().values[0]))

        self.candles_5min_list.append(candle_5min)
        self.last_candle_5min_minute = current_candle_5min_minute
        self.last_candle_5min_hour = current_candle_5min_hour
        self.last_candle_5min_day = current_candle_5min_day

        if (len(self.candles_5min_list) > self.CANDLES_HISTORY_LENGTH):
            del self.candles_5min_list[0]
        if (len(self.candles_30min_list) > self.CANDLES_HISTORY_LENGTH):
            del self.candles_30min_list[0]
        if (len(self.candles_1h_list) > self.CANDLES_HISTORY_LENGTH):
            del self.candles_1h_list[0]
        if (len(self.candles_4h_list) > self.CANDLES_HISTORY_LENGTH):
            del self.candles_4h_list[0]
        return create_from_csv_line(
            self.open_file_5min.get_chunk().values[0])

    def test_strategy(self):
        custom_close = self.check_for_custom_close()
        if (self.trade_buy.is_closed == False):
            self.check_to_close_trade(
                self.trade_buy, self.indicators_buy, custom_close)

        if (self.trade_sell.is_closed == False):
            self.check_to_close_trade(
                self.trade_sell, self.indicators_sell, custom_close)
            # return DO NOT RETURN HERE BECAUSE TRADE CAN BE CLOSED WHILE CANDLE IS NOT CLOSED

        if (len(self.candles_5min_list) < self.CANDLES_HISTORY_LENGTH):
            return

        if (self.trade_buy.is_closed == True or self.trade_sell.is_closed == True):
            position = self.check_strategy()

            if (position == 'Idle'):
                return

            if (position == TradeType.BUY and self.trade_sell.is_closed == False):
                self.check_to_close_trade(
                    self.trade_sell, self.indicators_sell, 'force_close')
                return

            if (position == TradeType.SELL and self.trade_buy.is_closed == False):
                self.check_to_close_trade(
                    self.trade_buy, self.indicators_buy, 'force_close')
                return

            if (position == TradeType.BUY and self.trade_buy.is_closed == True):
                self.take_position(TradeType.BUY)
            elif (position == TradeType.SELL and self.trade_sell.is_closed == True):
                self.take_position(TradeType.SELL)

    def take_position(self, side: TradeTypeValues):
        current_candle = self.get_last_candle()
        if (side == TradeType.BUY):
            self.trade_buy.is_closed = False
            self.trade_buy.price = current_candle.close
            self.trade_buy.opened_at = datetime.fromtimestamp(
                (current_candle.start_timestamp + (5 * 60 * 1000)) / 1000, tz=timezone.utc).isoformat()
            self.trade_buy.type = TradeType(side)
            self.trade_buy.position_value = str(self.get_position_value())
            self.indicators_buy._id = ObjectId()
            self.indicators_buy.type = self.trade_buy.type
            self.indicators_buy.trade_id = self.trade_buy._id
            self.indicators_buy.save()
            self.trade_buy.save()
        elif (side == TradeType.SELL):
            self.trade_sell.is_closed = False
            self.trade_sell.price = current_candle.close
            self.trade_sell.opened_at = datetime.fromtimestamp(
                (current_candle.start_timestamp + (5 * 60 * 1000)) / 1000, tz=timezone.utc).isoformat()
            self.trade_sell.type = TradeType(side)
            self.trade_sell.position_value = str(self.get_position_value())
            self.indicators_sell._id = ObjectId()
            self.indicators_sell.type = self.trade_sell.type
            self.indicators_sell.trade_id = self.trade_sell._id
            self.indicators_sell.save()
            self.trade_sell.save()

        if (self.trade_buy.is_closed == False and self.trade_sell.is_closed == False):
            self.opened_both_side_count += 1

    def check_to_close_trade(self, trade: TradeModel, indicators: IndicatorsModel, custom_close: str | None):
        fees_amount = int(trade.position_value) * self.FEES * 2
        trade.comission = fees_amount
        current_candle = self.get_last_candle()
        closed_date = self.get_close_date_from_candle(current_candle)
        # Loss
        if ((trade.type.value == TradeType.SELL and current_candle.high >= trade.stop_loss) or (trade.type.value == TradeType.BUY and current_candle.low <= trade.stop_loss) or custom_close == 'force_loss'):
            diff_price_amount = abs(trade.stop_loss - trade.price)
            loss_amount = int(trade.position_value) * \
                (diff_price_amount / trade.price)
            final_profit = loss_amount + fees_amount
            indicators.profit = str(-final_profit)
            self.balance -= final_profit
            trade.close = trade.stop_loss
            trade.profit = str(-final_profit)
            trade.closed_at = closed_date.isoformat()
            # Save into database
            trade.is_closed = True
            indicators.save()
            trade.save()
            trade._id = ObjectId()
            self.set_drawdown()
        # Profit
        elif ((trade.type.value == TradeType.SELL and current_candle.low <= trade.take_profit) or (trade.type.value == TradeType.BUY and current_candle.high >= trade.take_profit)):
            diff_price_amount = abs(trade.take_profit - trade.price)
            profit_amount = int(trade.position_value) * \
                (diff_price_amount / trade.price)
            final_profit = profit_amount - fees_amount
            indicators.profit = str(final_profit)
            self.balance += final_profit
            trade.close = trade.take_profit
            trade.profit = str(final_profit)
            trade.closed_at = closed_date.isoformat()
            # Save into database
            trade.is_closed = True
            indicators.save()
            trade.save()
            trade._id = ObjectId()
            self.set_drawdown()

        elif (custom_close == 'close_profit'):
            diff_price_amount = abs(current_candle.close - trade.price)
            trade_profit = int(trade.position_value) * \
                (diff_price_amount / trade.price)
            if ((trade.type.value == TradeType.SELL and current_candle.close <= trade.price) or (trade.type.value == TradeType.BUY and current_candle.close >= trade.price)):
                final_profit = trade_profit - fees_amount
                self.balance += final_profit
                indicators.profit = str(final_profit)
                trade.profit = str(final_profit)
                trade.close = current_candle.close
                trade.closed_at = closed_date.isoformat()
                # Save into database
                trade.is_closed = True
                indicators.save()
                trade.save()
                trade._id = ObjectId()
                self.set_drawdown()
        elif (custom_close == 'force_close'):
            diff_price_amount = abs(current_candle.close - trade.price)
            trade_profit = int(trade.position_value) * \
                (diff_price_amount / trade.price)
            if ((trade.type.value == TradeType.SELL and current_candle.close <= trade.price) or (trade.type.value == TradeType.BUY and current_candle.close >= trade.price)):
                final_profit = trade_profit - fees_amount
                self.balance += final_profit
                trade.profit = str(final_profit)
                indicators.profit = str(final_profit)
            if ((trade.type.value == TradeType.SELL and current_candle.close >= trade.price) or (trade.type.value == TradeType.BUY and current_candle.close <= trade.price)):
                final_profit = trade_profit + fees_amount
                self.balance -= final_profit
                trade.profit = str(-trade_profit)
                indicators.profit = str(-trade_profit)
            trade.close = current_candle.close
            trade.closed_at = closed_date.isoformat()
            # Save into database
            trade.is_closed = True
            indicators.save()
            trade.save()
            trade._id = ObjectId()
            self.set_drawdown()


if __name__ == '__main__':
    BotDev().start()
