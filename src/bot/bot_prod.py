import sys  # NOQA
import os  # NOQA
parent_dir = os.path.dirname(os.path.realpath(__file__))  # NOQA
sys.path.append(parent_dir + '/..')  # NOQA
from bot.bot_manager import BotManager
from bot.fxopen.fxopen_api import FxOpenApi
from database.models.trade_model import TradeModel
from config.config_service import ConfigService


class BotProd(BotManager):
    configService = ConfigService()
    fxopenApi = None

    def start(self):
        environment = sys.argv[1]
        self.fxopenApi = FxOpenApi(environment)
        print('test prod')
        candles = self.fxopenApi.get_candles('M5', 5)
        print('get candles response : ', candles)


if __name__ == '__main__':
    BotProd().start()
