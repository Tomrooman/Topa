from datetime import datetime, timezone
from dateutil import relativedelta
import pandas as pd
import curses
import sys  # NOQA
import os  # NOQA
parent_dir = os.path.dirname(os.path.realpath(__file__))  # NOQA
sys.path.append(parent_dir + '/..')  # NOQA
from src.bot.bot_manager import BotManager
from src.database.models.trade_model import TradeModel
from src.bot.candle import Candle, create_from_csv_line


class BotProd(BotManager):
    def start(self):
        print('test prod')
