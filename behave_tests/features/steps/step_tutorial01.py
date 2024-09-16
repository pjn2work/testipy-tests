from behave import given, when, then
from behave.runner import Context


@given('we have behave installed')
def step_impl1(context: Context, **kwargs):
    print(">>>>> given 1")


@when('we implement a test {v}')
def step_impl2(context: Context, v: str):
    context.data = "Pedro"
    print(">>>>> when", v)
    assert int(v) > 0, f"{V} is not > 0"


@then('behave will test it for us.')
def step_impl4(context: Context):
    print(">>>>> then")


@then('behave will test it for us! {index} and {desc}')
def step_impl3(context: Context, index: str, desc: str):
    print(context.data)
    print(">>>>> then", index, desc)
    index = int(index)
    assert index<5, f"{index} < 5 failed"
