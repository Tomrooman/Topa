from bot.candle import Candle
from flask import Blueprint
from .candle_service import Candle_service

controller_name = "candles"
blueprint = Blueprint(controller_name, __name__)
candle_service = Candle_service()


@blueprint.route(f"/{controller_name}", methods=['GET'])
def candles() -> list[Candle]:
    return candle_service.handle_route()
