from behave import given, when, then
from behave.runner import Context
from behave_tests.features.testipy_report import get_rm


@given('we have behave installed')
def step_impl1(context: Context, **kwargs):
    print("  > background step")


@when('we implement a test {v}')
def step_impl2(context: Context, v: str):
    print("  >> when", v)
    assert int(v) > 0, f"{v} is not > 0"


@then('behave table test step')
def step_impl4(context: Context):
    print("  Table contents")
    for i, row in enumerate(context.table):
        print("  >>", i, row["column_A"], row["column_B"])


@then('behave will test it for us! {index} and {desc}')
def step_impl3(context: Context, index: str, desc: str):
    index = int(index)

    print(f"  >> {index=}, {desc=}, tags={context.scenario.tags}")
    get_rm().test_info(context.testipy_current_test, f"This test will fail if index >= 5. {index=}")

    assert index<5, f"{index} < 5 failed"
