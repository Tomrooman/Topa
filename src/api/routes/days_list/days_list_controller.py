from flask import Blueprint
from .days_list_service import Days_list_service

controller_name = "days_list"
blueprint = Blueprint(controller_name, __name__)
days_list_service = Days_list_service()


@blueprint.get(f"/{controller_name}")
def days_list():
    return days_list_service.handle_route()
