from flask import Blueprint
from .stats_service import StatsService

controller_name = "stats"
blueprint = Blueprint(controller_name, __name__)
statsService = StatsService()


@blueprint.route(f"/{controller_name}", methods=['GET'])
def candles():
    return statsService.handle_route()
