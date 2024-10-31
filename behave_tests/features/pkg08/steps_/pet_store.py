import requests
from requests import Response

from behave import step, given
from behave.runner import Context

from behave_tests.features.common import get_from_context, save_into_context
from behave_tests.features.testipy_report import TestipyStep
from testipy.helpers.handle_assertions import assert_equal_dicts, ExpectedError


@given("the base url is {url}")
def set_base_url(context: Context, url: str):
    context.url = url


@step("post {key} to pet store, I receive a {status_code:d} status code")
def post_to_petstore(context: Context, key: str, status_code: int):
    data = get_from_context(context, key)
    context.response = _post_as_dict(context.url, data)
    context.logging.info(context.response.text)
    save_into_context(context, f"{key}_response", context.response.json())
    assert context.response.status_code == status_code, f"Expected {status_code=}, not {context.response.status_code}."

    if 200 <= status_code <= 299:
        received = context.response.json()
        assert_equal_dicts(data, received)
    else:
        raise ExpectedError(f"designed to fail with {status_code}")


@step("I can get the {key} pet from store, and receive a {status_code:d} status code")
def get_from_petstore(context: Context, key: str, status_code: int):
    data = get_from_context(context, key)
    url = context.url + str(data["id"])

    with TestipyStep(context, f"GET {url}"):
        context.response = _get_as_dict(url)
        context.logging.info(context.response.text)
        save_into_context(context, f"{key}_response", context.response.json())
        assert context.response.status_code == status_code, f"Expected {status_code=}, not {context.response.status_code}."

    if 200 <= status_code <= 299:
        assert_equal_dicts(data, context.response.json())



# --- Execution Methods --------------------------------------------------------------------------------------------

def _get_as_dict(url: str = "", timeout: int = 5) -> Response:
    return requests.get(url, headers={"accept": "application/json"}, timeout=timeout)


def _post_as_dict(url: str = "", data: dict = None, timeout: int = 5) -> Response:
    return requests.post(
        url,
        json=data,
        headers={"Content-Type": "application/json; charset=utf-8", "accept": "application/json"},
        timeout=timeout
    )


def _put_as_dict(url: str = "", data: dict = None, timeout: int = 5) -> Response:
    return requests.put(
        url,
        json=data,
        headers={"Content-Type": "application/json; charset=utf-8", "accept": "application/json"},
        timeout=timeout
    )
