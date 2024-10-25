from typing import Any

from behave.runner import Context


def get_data_bucket_from_context(context: Context) -> dict:
    data_bucket = "DATA_BUCKET"
    if not hasattr(context, data_bucket):
        setattr(context, data_bucket, {})
    return getattr(context, data_bucket)


def save_into_context(context: Context, key: str, value: Any):
    db = get_data_bucket_from_context(context)
    db[key] = value


def get_from_context(context: Context, key: str) -> Any:
    db = get_data_bucket_from_context(context)
    if key not in db:
        raise KeyError(f"{key=} is not in context.")
    return db[key]
