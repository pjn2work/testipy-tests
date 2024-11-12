from decouple import config


ENVIRONMENT: str = config("ENVIRONMENT", cast=str)
