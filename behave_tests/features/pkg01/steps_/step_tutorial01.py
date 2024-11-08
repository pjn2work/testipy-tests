from behave import when, then
from behave.runner import Context

from behave_tests.testdata import ENVIRONMENT


@when('we implement a test {v}')
def step_impl2(context: Context, v: str):
    print("  >> when", v)
    assert int(v) > 0, f"{v} is not > 0"


@then('behave table test step')
def step_impl4(context: Context):
    print(f"  Table contents for {ENVIRONMENT}")
    for i, row in enumerate(context.table):
        print("  >>", i, row["column_A"], row["column_B"])


@then('behave will test it for us! {index:d} and {desc}')
def step_impl3(context: Context, index: int, desc: str):
    print(f"  >> {index=}, {desc=}, tags={context.scenario.tags}")
    context.testipy_reporting.test_info(context, f"This test will fail if index >= 5. {index=}")
    context.testipy_reason_of_state = f"{index} < 5"

    assert index<5, f"{index} < 5 failed"
