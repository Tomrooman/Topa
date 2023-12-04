from dataclasses import dataclass
from pymongo import MongoClient
from config.config_service import ConfigService


@dataclass
class MongoDB:
    configService = ConfigService()
    client = MongoClient(host=configService.get_database_host(),
                         username=configService.get_database_user(),
                         password=configService.get_database_password(),
                         authSource=configService.get_database_name(),
                         authMechanism=configService.get_database_auth_mechanism(),
                         port=configService.get_database_port(),)
    database = client[configService.get_database_name()]
    # Will throw error if authentication failed
    database.list_collection_names()
