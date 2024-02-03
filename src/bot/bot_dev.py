from datetime import datetime, timezone
from bson import ObjectId
from dateutil import relativedelta
import pandas as pd
import curses
import sys  # NOQA
import os  # NOQA
parent_dir = os.path.dirname(os.path.realpath(__file__))  # NOQA
sys.path.append(parent_dir + '/..')  # NOQA
from bot.bot_manager import BotManager
from database.models.trade_model import TradeModel, TradeType
from bot.candle import Candle, create_from_csv_line


class BotDev(BotManager):
    open_file_5min = pd.read_csv(
        "data/formatted/EURUSD_5min.csv", chunksize=1)
    open_file_30min = pd.read_csv(
        "data/formatted/EURUSD_30min.csv", chunksize=1)
    open_file_1h = pd.read_csv("data/formatted/EURUSD_1h.csv", chunksize=1)
    open_file_4h = pd.read_csv("data/formatted/EURUSD_4h.csv", chunksize=1)
    stdscr = curses.initscr()
    last_candle_processed_date = None

    def start(self):
        f = open("data/diff_to_high.txt", "w")
        f.write("")
        f.close()
        self.stdscr.clear()
        # Drop trades table
        TradeModel.drop_table()

        candle_5min = create_from_csv_line(
            self.open_file_5min.get_chunk().values[0])
        self.candles_30min_list.append(create_from_csv_line(
            self.open_file_30min.get_chunk().values[0]))
        self.candles_1h_list.append(create_from_csv_line(
            self.open_file_1h.get_chunk().values[0]))
        self.candles_4h_list.append(create_from_csv_line(
            self.open_file_4h.get_chunk().values[0]))

        try:
            while (candle_5min != None):
                candle_5min_start_date = datetime.fromtimestamp(
                    candle_5min.start_timestamp / 1000, tz=timezone.utc)
                self.stdscr.clear()
                self.stdscr.addstr(
                    0, 0, f'Candle start date: {candle_5min_start_date}')
                self.stdscr.addstr(1, 0, f'Balance: {self.balance}')
                self.stdscr.addstr(
                    2, 0, f'Trade is closed: {self.trade.is_closed}')
                self.stdscr.addstr(3, 0, f'Max balance: {self.max_balance}')
                self.stdscr.addstr(4, 0,
                                   f'Current drawdown: {self.current_drawdown}% -> {round(self.max_balance * (self.current_drawdown / 100), 4)}€')
                self.stdscr.addstr(5, 0,
                                   f'Max drawdown: {self.max_drawdown}%')
                try:
                    candle_5min = self.set_candles_list(candle_5min)
                    self.last_candle_processed_date = candle_5min_start_date
                except Exception as e:
                    candle_5min = None
                    continue
                else:
                    if (len(self.candles_5min_list) >= 14 and len(self.candles_30min_list) >= 14 and len(self.candles_1h_list) >= 14 and len(self.candles_4h_list) >= 7):
                        self.set_all_rsi()
                    if (self.rsi_5min.value != 0 and self.rsi_30min.value != 0 and self.rsi_1h.value != 0 and self.rsi_4h.value != 0):
                        self.test_strategy()
                    self.stdscr.addstr(6, 0, '----------')
                    self.stdscr.refresh()
            curses.endwin()
            print('\n----- Backtest done -----\n')
            print(f'Candle start date: {self.last_candle_processed_date}')
            print(f'Balance: {self.balance}')
            print(f'Trade is closed: {self.trade.is_closed}')
            print(f'Max balance: {self.max_balance}')
            print(
                f'Current drawdown: {self.current_drawdown}% -> {round(self.max_balance * (self.current_drawdown / 100), 4)}€')
            print(f'Max drawdown: {self.max_drawdown}%')
            print('\n')
        except KeyboardInterrupt:
            curses.endwin()
            pass

    def set_candles_list(self, candle_5min: Candle) -> Candle:
        if (len(self.candles_5min_list) != 0):
            last_candle_5min_start_date = datetime.fromtimestamp(
                self.candles_5min_list[-1].start_timestamp / 1000, tz=timezone.utc)
            current_candle_5min_start_date = datetime.fromtimestamp(
                candle_5min.start_timestamp / 1000, tz=timezone.utc)
            difference = relativedelta.relativedelta(
                current_candle_5min_start_date, last_candle_5min_start_date)
            if (difference.minutes > 10 and current_candle_5min_start_date.hour != 23 and current_candle_5min_start_date.minute != 40 and current_candle_5min_start_date.hour != 0):
                # print('## Difference minutes too high, drop all candles list ##')
                f = open("data/diff_to_high.txt", "a")
                f.write(
                    f"Difference minutes too high, drop all candles list\n{last_candle_5min_start_date.isoformat()}\n{current_candle_5min_start_date.isoformat()}\n\n")
                f.close()
                self.candles_5min_list = []
                self.candles_30min_list = []
                self.candles_1h_list = []
                self.candles_4h_list = []
                self.rsi_5min.value = 0
                self.rsi_30min.value = 0
                self.rsi_1h.value = 0
                self.rsi_4h.value = 0
            if (current_candle_5min_start_date.minute == 0 or current_candle_5min_start_date.minute == 30):
                self.candles_30min_list.append(create_from_csv_line(
                    self.open_file_30min.get_chunk().values[0]))
            if (current_candle_5min_start_date.hour != last_candle_5min_start_date.hour):
                self.candles_1h_list.append(create_from_csv_line(
                    self.open_file_1h.get_chunk().values[0]))
            if (current_candle_5min_start_date.hour != last_candle_5min_start_date.hour and (current_candle_5min_start_date.hour % 4 == 0 or current_candle_5min_start_date.hour == 0)):
                self.candles_4h_list.append(create_from_csv_line(
                    self.open_file_4h.get_chunk().values[0]))
        self.candles_5min_list.append(candle_5min)
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
        if (self.trade.is_closed == False):
            self.check_to_close_trade(custom_close)
            # return DO NOT RETURN HERE BECAUSE TRADE CAN BE CLOSED WHILE CANDLE IS NOT CLOSED

        position = self.check_strategy()

        if (position == 'Idle'):
            return

        self.take_position(position)

    def take_position(self, side: str):
        current_candle = self.get_last_candle()
        self.trade.is_closed = False
        self.trade.price = current_candle.close
        self.trade.opened_at = datetime.fromtimestamp(
            current_candle.start_timestamp / 1000, tz=timezone.utc).isoformat()
        self.trade.type = TradeType(side.lower())
        self.trade.position_value = self.get_position_value()

    def check_to_close_trade(self, custom_close: str | None):
        fees_amount = self.trade.position_value * self.FEES * 2
        current_candle = self.get_last_candle()
        closed_date = self.get_close_date_from_candle(current_candle)
        # Loss
        if ((self.trade.type.value == 'sell' and current_candle.high >= self.trade.stop_loss) or (self.trade.type.value == 'buy' and current_candle.low <= self.trade.stop_loss)):
            diff_price_amount = abs(self.trade.stop_loss - self.trade.price)
            loss_amount = self.trade.position_value * \
                (diff_price_amount / self.trade.price)
            self.balance -= loss_amount + fees_amount
            self.trade.close = self.trade.stop_loss
            self.trade.profit = -loss_amount
            self.trade.closed_at = closed_date.isoformat()
            # Save into database
            self.trade.is_closed = True
            self.trade.save()
            self.trade._id = ObjectId()
            self.set_drawdown()
        # Profit
        elif ((self.trade.type.value == 'sell' and current_candle.low <= self.trade.take_profit) or (self.trade.type.value == 'buy' and current_candle.high >= self.trade.take_profit)):
            diff_price_amount = abs(self.trade.take_profit - self.trade.price)
            profit_amount = self.trade.position_value * \
                (diff_price_amount / self.trade.price)
            self.balance += profit_amount - fees_amount
            self.trade.close = self.trade.take_profit
            self.trade.profit = profit_amount
            self.trade.closed_at = closed_date.isoformat()
            # Save into database
            self.trade.is_closed = True
            self.trade.save()
            self.trade._id = ObjectId()
            self.set_drawdown()

        elif (custom_close == 'close_profit'):
            diff_price_amount = abs(current_candle.close - self.trade.price)
            trade_profit = self.trade.position_value * \
                (diff_price_amount / self.trade.price)
            if ((self.trade.type.value == 'sell' and current_candle.close <= self.trade.price) or (self.trade.type.value == 'buy' and current_candle.close >= self.trade.price)):
                self.balance += trade_profit - fees_amount
                self.trade.profit = trade_profit
                self.trade.close = current_candle.close
                self.trade.closed_at = closed_date.isoformat()
                # Save into database
                self.trade.is_closed = True
                self.trade.save()
                self.trade._id = ObjectId()
                self.set_drawdown()
        elif (custom_close == 'force_close'):
            diff_price_amount = abs(current_candle.close - self.trade.price)
            trade_profit = self.trade.position_value * \
                (diff_price_amount / self.trade.price)
            if ((self.trade.type.value == 'sell' and current_candle.close <= self.trade.price) or (self.trade.type.value == 'buy' and current_candle.close >= self.trade.price)):
                self.balance += trade_profit - fees_amount
                self.trade.profit = trade_profit
            if ((self.trade.type.value == 'sell' and current_candle.close >= self.trade.price) or (self.trade.type.value == 'buy' and current_candle.close <= self.trade.price)):
                self.balance -= trade_profit + fees_amount
                self.trade.profit = -trade_profit
            self.trade.close = current_candle.close
            self.trade.closed_at = closed_date.isoformat()
            # Save into database
            self.trade.is_closed = True
            self.trade.save()
            self.trade._id = ObjectId()
            self.set_drawdown()


if __name__ == '__main__':
    BotDev().start()
