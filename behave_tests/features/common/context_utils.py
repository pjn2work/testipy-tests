from functools import partial
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


def has_in_context(context: Context, key: str) -> bool:
    db = get_data_bucket_from_context(context)
    return key in db


def filter_tags_with_prefix(tags: Iterable[Tag], /, *, prefix: str, trim_prefix: bool) -> set[Tag]:
    return {
        tag.removeprefix(prefix) if trim_prefix else tag
        for tag in tags
        if tag.startswith(prefix)
    }


def should_run(
    context: Context, /, *, iterator: Iterable[Feature | ScenarioOutline | Scenario]
) -> list[Feature | ScenarioOutline | Scenario]:
    return [x for x in iterator if x.should_run(config=context._config)]


def get_all_tags_with_prefix(
        context: Context, /, *,
        prefix: str,
        trim_prefix: bool = True,
        include_features: bool = True,
        include_scenarios: bool = True,
        include_examples: bool = True,
) -> set[Tag]:
    tags = set()
    for feature in should_run(context, iterator=context._runner.features):
        if include_features:
            tags.update(filter_tags_with_prefix(feature.tags, prefix=prefix, trim_prefix=trim_prefix))
        for scenario in should_run(context, iterator=feature.scenarios):
            if include_scenarios:
                tags.update(filter_tags_with_prefix(scenario.tags, prefix=prefix, trim_prefix=trim_prefix))
            if isinstance(scenario, ScenarioOutline) and include_examples:
                for example in should_run(context, iterator=scenario.scenarios):
                    tags.update(filter_tags_with_prefix(example.tags, prefix=prefix, trim_prefix=trim_prefix))
    return tags


get_all_features_tags_with_prefix = partial(get_all_tags_with_prefix, include_features=True, include_scenarios=False, include_examples=False)
get_all_scenarios_tags_with_prefix = partial(get_all_tags_with_prefix, include_features=False, include_scenarios=True, include_examples=False)
get_all_examples_tags_with_prefix = partial(get_all_tags_with_prefix, include_features=False, include_scenarios=False, include_examples=True)
