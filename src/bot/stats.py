import sys  # NOQA
import os  # NOQA
parent_dir = os.path.dirname(os.path.realpath(__file__))  # NOQA
sys.path.append(parent_dir + '/..')  # NOQA
from api.routes.stats.stats_service import StatsService


class Stats:

    def start(self):
        stats = StatsService().handle_route()
        print(stats)


if __name__ == '__main__':
    Stats().start()
