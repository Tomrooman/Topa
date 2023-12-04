from flask import Blueprint
from .candle_service import CandleService

controller_name = "candles"
blueprint = Blueprint(controller_name, __name__)
candleService = CandleService()


@blueprint.route(f"/{controller_name}", methods=['GET'])
def candles():
    return candleService.handle_route()
