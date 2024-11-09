from behave import when, then
from behave.runner import Context

from behave_tests.testdata import ENVIRONMENT
from behave_tests.features.common.context_utils import set_step_reason_of_state


def create_plotly(context: Context):

    import pandas as pd
    import plotly.express as px
    import plotly.io as pio

    # Sample DataFrame
    df = pd.DataFrame({
        'Category': ['A', 'B', 'C'],
        'Values': [10, 15, 7]
    })

    # Create Plotly figure
    fig = px.bar(df, x='Category', y='Values', title="Sample Plotly Graph")

    # Get HTML string of the figure
    fig_html = pio.to_html(fig, full_html=False)

    context.testipy_reporting.test_info(context, fig_html, true_html=True)


@when('we implement a test {v}')
def step_impl2(context: Context, v: str):
    print("  >> when", v)
    assert int(v) > 0, f"{v} is not > 0"


@then('behave table test step')
def step_impl4(context: Context):
    print(f"  Table contents for {ENVIRONMENT}")
    for i, row in enumerate(context.table):
        print("  >>", i, row["column_A"], row["column_B"])
    create_plotly(context)


@then('behave will test it for us! {index:d} and {desc}')
def step_impl3(context: Context, index: int, desc: str):
    print(f"  >> {index=}, {desc=}, tags={context.scenario.tags}")
    context.testipy_reporting.test_info(context, f"This test will fail if index >= 5. {index=}")
    set_step_reason_of_state(context, f"{index} < 5")

    assert index<5, f"{index} < 5 failed"
