from behave import step
from behave.runner import Context

from behave_tests.features.common import get_from_context
from behave_tests.features.steps.functions import verify_field_types


@step("the body from {key} response, must have the following types")
def verify_response_body_field_types_from_context(context: Context, key: str):
    table_data: list[dict] = get_from_context(context, key + "_response").json()

    assert len(table_data) > 0, f"Expected some results inside {key}_response.body"

    verify_field_types(context, table_data)


@step("the headers from {key} response, must have the following types")
def verify_response_headers_field_types_from_context(context: Context, key: str):
    headers = get_from_context(context, key + "_response").headers

    assert len(headers) > 0, f"Expected some results inside {key}_response.headers"

    verify_field_types(context, [dict(headers)])
