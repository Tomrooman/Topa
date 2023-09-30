import sys  # NOQA
import os  # NOQA
parent_dir = os.path.dirname(os.path.realpath(__file__))  # NOQA
sys.path.append(parent_dir + '/..')  # NOQA
import pandas as pd
from candle import Candle, create_from_csv_line
from indicators import get_rsi
from pymongo import MongoClient
from config.config_service import ConfigService


configService = ConfigService()
client = MongoClient(host=configService.get_database_host(),
                     username=configService.get_database_user(),
                     password=configService.get_database_password(),
                     authSource=configService.get_database_name(),
                     authMechanism=configService.get_database_auth_mechanism(),
                     port=configService.get_database_port(),)
database = client[configService.get_database_name()]

FEES_PERCENTAGE = 0.0035
CANDLES_HISTORY_LENGTH = 50

# Historical data downloaded in UTC time zone
# Session times in UTC +1/2 time zone
# Europe : de 09h00 à 18h00
# New-York (qui se chevauche avec Londres) : de 14h00 à 22h00
# Tokyo : de 00h00 à 09h00


def main():
    candles = []
    index = 0
    open_file = pd.read_csv("data/formatted/EURUSD_5min.csv", chunksize=1)
    print(create_from_csv_line(open_file.get_chunk().values[0]))
    print(create_from_csv_line(open_file.get_chunk().values[0]))
    # for chunk in open_file:
    #     print(create_from_csv_line(chunk.values[0]))
    #     index += 1
    #     if (index == 15):
    #         return

    # with open("data/formatted/EURUSD_5min.csv", "rb") as text_file:
    #     for line in text_file:
    #         index += 1
    #         if (index > 1):
    #             candles.append(create_from_csv_line(line))
    #             if (len(candles) > CANDLES_HISTORY_LENGTH):
    #                 del candles[0]
    #             test_strategy(candles)
    #         if (index > 20):
    #             return


def test_strategy(candles: list[Candle]):
    rsi = get_rsi(candles, 14)
    if (rsi == None):
        return
    print(rsi)


if __name__ == '__main__':
    main()
