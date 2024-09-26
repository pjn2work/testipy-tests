import os
from datetime import datetime, timezone
from typing import Callable


def get_current_time() -> datetime:
    return datetime.now(timezone.utc)


def get_token_for(resource_id: str) -> str:
    file_object = os.popen(  # noqa: S605
        f"az account get-access-token --resource {resource_id} --query accessToken -otsv"
    )
    token_value = file_object.read().replace("\n", "")
    file_object.close()

    return token_value


class DatabricksTokenProvider:
    # Ask for a new token after 57 mins. It is important that this value is not too low. Otherwise the az
    # command will just give us the previous (cached on disk) token which will soon expire. Asking for a
    # new token at this point results in a new token being issued and it will last for around an hour. Of course
    # specifying a value greater than 60 mins the token in use will expire and could be used unsuccessfully
    EXPIRE_AFTER: int = 57

    _generated_at: datetime = None

    _cached_token_value: str = None

    def __init__(
        self,
        initial_token: str,
        databricks_resource_id: str,
        pipeline_execution: bool,
        pipeline_token_retriever: Callable[[str], str] = get_token_for,
        current_time_generator: Callable[[], datetime] = get_current_time,
    ):
        self._initial_token = initial_token
        self._databricks_resource_id: str = databricks_resource_id
        self._pipeline_execution: bool = pipeline_execution
        self._pipeline_token_retriever: Callable[[str], str] = pipeline_token_retriever
        self._current_time_generator = current_time_generator

    @classmethod
    def _set_cached_token(cls, token_value: str):
        cls._cached_token_value = token_value

    @classmethod
    def _get_cached_token(cls) -> str:
        return cls._cached_token_value

    @classmethod
    def _set_generated_at(cls, generated_at: datetime):
        cls._generated_at = generated_at

    @classmethod
    def _get_generated_at(cls) -> datetime:
        return cls._generated_at

    def is_expiring(self) -> bool:
        if self._pipeline_execution:
            minutes_diff = (
                datetime.now(timezone.utc) - self._get_generated_at()
            ).total_seconds() / 60.0
            return minutes_diff > self.EXPIRE_AFTER
        else:
            return False

    def get_token(self) -> str:
        if self._pipeline_execution:
            if self._get_generated_at() is None or self.is_expiring():
                self._set_cached_token(
                    self._pipeline_token_retriever(self._databricks_resource_id)
                )
                self._set_generated_at(self._current_time_generator())

            return self._get_cached_token()
        else:
            return self._initial_token  # usually a Personal Access Token (PAT)
