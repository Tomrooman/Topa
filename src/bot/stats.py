import sys  # NOQA
import os  # NOQA
parent_dir = os.path.dirname(os.path.realpath(__file__))  # NOQA
sys.path.append(parent_dir + '/..')  # NOQA
from api.routes.stats.stats_service import StatsService
import json


class Stats:

    def start(self):
        stats = json.loads(StatsService().handle_route())
        losing_months = stats["analytics"]["losingMonths"]
        time_to_comeback = stats["timeToComeback"]
        time_to_comback_in_row = max(
            [time["losingMonthsCount"] for time in time_to_comeback])
        higher_losing_months_percentage = max(
            [abs(month["percentage_from_balance"]) for month in losing_months])
        max_losing_month_in_row = max(
            [month["inRow"] for month in losing_months])
        print(f'Losing months length: {len(losing_months)}')
        print(f'Max losing months in a row: {max_losing_month_in_row}')
        print(
            f'Higher loss in one month: {higher_losing_months_percentage}%')
        print(f'Time to comeback length: {len(time_to_comeback)}')
        print(f'Time to comeback in a row: {time_to_comback_in_row}')


if __name__ == '__main__':
    Stats().start()
