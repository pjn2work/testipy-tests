from behave import when, then
from behave.runner import Context


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
    context.testipy_reporting.test_info(context, f"This test will fail if index >= 5. {index=}")

    assert index<5, f"{index} < 5 failed"
