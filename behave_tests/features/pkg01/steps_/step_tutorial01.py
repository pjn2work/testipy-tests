from behave import when, then
from behave.runner import Context
from behave_pandas import table_to_dataframe

from behave_tests.features import test_info, set_feature_step_reason_of_state

from common.utils.graphs import multi_plot_plotly, multi_plot_matplotlib, figure_to_attachment, figure_to_html


def create_plotly(context: Context, df):

    import plotly.express as px

    # Create Plotly figure
    fig = px.bar(df, y=["price", "discount"], title="Sample Plotly Graph")
    fig_html = figure_to_html(fig)
    test_info(context, fig_html, true_html=True)

    # plotly Image
    fig = multi_plot_plotly(df, title="multi_plot_plotly", xlim=(0, 150), fields_ax1=["price"])
    attachment = figure_to_attachment(fig, filename="PlotlyFigure", width=1750, scale=1)
    test_info(context, "plotly picture", attachment=attachment)

    # matplotlib Image
    fig = multi_plot_matplotlib(df, "multi_plot_matplotlib", xlim=(0, 150), fields_ax1=["price"], fig_size=(17, 4))
    attachment = figure_to_attachment(fig, filename="MatplotlibFigure")
    test_info(context, "matplotlib picture", attachment=attachment)


@when('we implement a test {v}')
def step_impl2(context: Context, v: str):
    print("  >> when", v)
    assert int(v) > 0, f"{v} is not > 0"


@then('plot table having header at {header:d} row and index at {index:d} column')
def step_impl4(context: Context, header: int, index: int):
    print("index |", " | ".join(context.table.headings))
    for i, row in enumerate(context.table):
        print(i, ">>", " | ".join(row.cells))

    df = table_to_dataframe(context.table, column_levels=header, index_levels=index)
    print(df)

    create_plotly(context, df)


@then('behave will test it for us! {index:d} and {desc}')
def step_impl3(context: Context, index: int, desc: str):
    print(f"  >> {index=}, {desc=}, tags={context.scenario.tags}")
    test_info(context, f"This test will fail if index >= 5. {index=}")
    set_feature_step_reason_of_state(context, f"{index} < 5")

    assert index<5, f"{index} < 5 failed"
