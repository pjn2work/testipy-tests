from decouple import config


ENVIRONMENT: str = config("ENVIRONMENT", cast=str)

ACCOUNT_URL: str = config("ACCOUNT_URL", cast=str)

SOURCE_WORKSPACE_NAME: str = config("ACCOUNT_URL", cast=str)
SOURCE_WORKSPACE_DATA_PATH: str = config("SOURCE_WORKSPACE_DATA_PATH", cast=str)

TARGET_WORKSPACE_NAME: str = config("TARGET_WORKSPACE_NAME", cast=str)
TARGET_WORKSPACE_DATA_PATH: str = config("TARGET_WORKSPACE_DATA_PATH", cast=str)

SOURCE_SFTP_HOST: str = config("SOURCE_SFTP_HOST", cast=str)
SOURCE_SFTP_USER: str = config("SOURCE_SFTP_USER", cast=str)
SOURCE_SFTP_PWD: str = config("SOURCE_SFTP_PWD", cast=str)