from dotenv import dotenv_values

environmentVariablesNeeded = [
    "DATABASE_NAME",
    "DATABASE_USER",
    "DATABASE_PASSWORD",
    "DATABASE_HOST",
    "DATABASE_PORT",
    "DATABASE_AUTH_MECHANISM",
]


class ConfigService:
    config = dotenv_values(".env")

    def __init__(self):
        for key in environmentVariablesNeeded:
            if (key not in self.config):
                raise Exception(f"Environment variable {key} is missing")
            if (self.config[key] == ""):
                raise Exception(f"Environment variable {key} is empty")

    def get_database_name(self) -> str:
        return str(self.config['DATABASE_NAME'])

    def get_database_user(self) -> str:
        return str(self.config['DATABASE_USER'])

    def get_database_password(self) -> str:
        return str(self.config['DATABASE_PASSWORD'])

    def get_database_host(self) -> str:
        return str(self.config['DATABASE_HOST'])

    def get_database_port(self) -> int:
        return int(str(self.config['DATABASE_PORT']))

    def get_database_auth_mechanism(self) -> str:
        return str(self.config['DATABASE_AUTH_MECHANISM'])
