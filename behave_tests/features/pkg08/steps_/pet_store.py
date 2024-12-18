import requests
from requests import Response

from behave import step, given
from behave.runner import Context

from behave_tests.features import TestipyStep
from behave_tests.features.common import get_from_context, save_into_context
from testipy.helpers.handle_assertions import assert_equal_dicts, ExpectedError
from testipy.helpers import prettify


@given("the base url is {url}")
def set_base_url(context: Context, url: str):
    context.url = url


@step("post {key} to pet store, I receive a {status_code:d} status code")
def post_to_petstore(context: Context, key: str, status_code: int):
    data = get_from_context(context, key)
    response = _post_as_dict(context.url, data)

    log_info = f"Status code: {response.status_code}" + "\nHeaders:\n" + prettify(dict(response.headers)) + "\nBody:\n" + prettify(response.json())
    context.logging.info(log_info)

    save_into_context(context, key + "_response", response)
    assert response.status_code == status_code, f"Expected {status_code=}, not {response.status_code}."

    if 200 <= status_code <= 299:
        received = response.json()
        assert_equal_dicts(data, received)
    else:
        raise ExpectedError(f"designed to fail with {status_code}")


@step("I can get the {key} pet from store, and receive a {status_code:d} status code")
def get_from_petstore(context: Context, key: str, status_code: int):
    data = get_from_context(context, key)
    url = context.url + str(data["id"])

    with TestipyStep(context, f"GET {url}"):
        response = _get_as_dict(url)

        log_info = f"Status code: {response.status_code}" + "\nHeaders:\n" + prettify(
            dict(response.headers)) + "\nBody:\n" + prettify(response.json())
        context.logging.info(log_info)

        save_into_context(context, key + "_response", response)
        assert response.status_code == status_code, f"Expected {status_code=}, not {response.status_code}."

    if 200 <= status_code <= 299:
        assert_equal_dicts(data, response.json())



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
