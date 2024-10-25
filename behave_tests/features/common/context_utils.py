from typing import Any, Iterable

from behave.model import Feature, Scenario, ScenarioOutline, Tag
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


def filter_tags_with_prefix(tags: Iterable[Tag], /, *, prefix: str) -> set[Tag]:
    return {tag for tag in tags if tag.startswith(prefix)}


def should_run(
    context: Context, /, *, iterator: Iterable[Feature | ScenarioOutline | Scenario]
) -> list[Feature | ScenarioOutline | Scenario]:
    return [x for x in iterator if x.should_run(config=context._config)]


def get_all_tags_with_prefix(context: Context, /, *, prefix: str) -> set[Tag]:
    tags = set()
    for feature in should_run(context, iterator=context._runner.features):
        tags.update(filter_tags_with_prefix(feature.tags, prefix=prefix))
        for scenario in should_run(context, iterator=feature.scenarios):
            tags.update(filter_tags_with_prefix(scenario.tags, prefix=prefix))
            if isinstance(scenario, ScenarioOutline):
                for example in should_run(context, iterator=scenario.scenarios):
                    tags.update(filter_tags_with_prefix(example.tags, prefix=prefix))
    return tags


def get_tag_values_for_prefix(tags: Iterable[Tag], /, *, tag_prefix: str) -> list[str]:
    return [
        tag.removeprefix(tag_prefix)
        for tag in tags
        if tag.startswith(tag_prefix)
    ]
