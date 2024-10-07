import requests
from requests import Response

from behave import step, given
from behave.runner import Context

from behave_tests.features.testipy_report import TestipyStep
from testipy.helpers.handle_assertions import assert_equal_dicts


@given("the base url is {url}")
def set_base_url(context: Context, url: str):
    context.url = url


@step("post data to pet store, I receive a {status_code} status code")
def post_to_petstore(context: Context, status_code: str):
    status_code = int(status_code)

    context.response = _post_as_dict(context.url, context.data)
    assert context.response.status_code == status_code, f"Expected {status_code=}, not {context.response.status_code}.\n{context.response.text}"

    if 200 <= status_code <= 299:
        received = context.response.json()
        assert_equal_dicts(context.data, received)


@step("I can get the same pet from store, and receive a {status_code} status code")
def get_from_petstore(context: Context, status_code: str):
    status_code = int(status_code)
    url = context.url + str(context.data["id"])

    with TestipyStep(context, f"GET {url}"):
        context.response = _get_as_dict(url)
        assert context.response.status_code == status_code, f"Expected {status_code=}, not {context.response.status_code}."

    if 200 <= status_code <= 299:
        assert_equal_dicts(context.data, context.response.json())



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


def _delete_as_str(url: str = "", timeout: int = 5) -> Response:
    return requests.delete(url, headers={"accept": "application/json"}, timeout=timeout)
