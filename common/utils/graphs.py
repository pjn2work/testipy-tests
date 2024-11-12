from matplotlib import colors as plt_colors
from matplotlib import pyplot as plt
from matplotlib.axes import Axes
import pandas as pd
import numpy as np
import random
import plotly.io as pio
import plotly.graph_objects as go
from typing import Any
from io import BytesIO


# stop warnings for having too much figures opened in matplotlib
plt.rcParams.update({'figure.max_open_warning': 0})

# have plotly render to jupyter notebook, so we can do actions on graphs in HTML
pio.renderers.keys()
pio.renderers.default = 'notebook'


COLORS: list[str] = list(plt_colors.XKCD_COLORS.values())
STATIC_AXIS: dict[str, Axes] = {}
FIXED_COLORS: dict[str, str] = {}


def _draw_guidelines(ax, n=8, color="lightgray"):
    deltax = ax.get_xlim()[1]/n
    deltay = ax.get_ylim()[1]/n
    for s in range(1, n):
        ax.axvline(s*deltax, color=color, linestyle=(0, (1, 5)))
        ax.axhline(s*deltay, color=color, linestyle=(0, (1, 4)))


def is_static_axis(axis_name: str, metric_name: str) -> bool:
    return (axis_name.startswith("_") and metric_name.endswith(axis_name)) or \
        (axis_name.endswith("_") and metric_name.startswith(axis_name))


def multi_plot_matplotlib(
        df: pd.DataFrame,
        title: str,
        xlim: tuple,
        fields_ax1=None,
        fields_ax2=None,
        linestyle: str = "-",
        ax2_static_shrink: float = 1.0,
        resample_sec: int = 1,
        fig_size: tuple[int, int] = (25, 5),
) -> plt.Figure | None:
    fields_ax1 = [k for k in fields_ax1 if k in df.columns and df[k].max() > 0] if fields_ax1 is not None else [k for k in df.columns if df[k].max() > 0]
    fields_ax2 = [k for k in df.columns if k not in fields_ax1 and df[k].max() > 0] if fields_ax2 is None else [k for k in fields_ax2 if k in df.columns and df[k].max() > 0]

    if (df.shape[0] <= 1) or (len(fields_ax1) + len(fields_ax2) == 0):
        print(f"WARNING! No data for {title}")
        return None

    if len(fields_ax1) == 0:
        fields_ax1 = [fields_ax2[0]]
        fields_ax2 = fields_ax2[1:]

    if resample_sec > 1:
        df = df.resample(f"{resample_sec}s").sum()/resample_sec

    # same axis for All queues_ and All ms_ and All err_
    static_axis = STATIC_AXIS.copy()

    ax = None
    colors = get_colors_by_action(fields_ax1)
    for i, col in enumerate(fields_ax1):
        if ax is None:
            ax = df[[col]].plot(figsize=fig_size, title=title.upper(), color=colors[i], style=linestyle)
        else:
            df[[col]].plot(ax=ax, color=colors[i], style=linestyle)
    ax.set_ylabel(ylabel="/".join(fields_ax1))
    ax.grid(True, linestyle='-.', color="lightgray", which="both", axis="both")

    # limit axis X & Y
    try:
        lines, labels = ax.get_legend_handles_labels()
        ax.set_ylim([0, None])
        ax.set_xlim(xlim)
    except Exception as ex:
        print(f"Error in {title} - {df.columns} - {ex}")
        return None

    # plot next columns in its own Y-axis
    a = 0
    colors = get_colors_by_action(fields_ax2)
    for i, col in enumerate(fields_ax2):
        if df[col].shape[0] > 1:

            # decide which axis to use or create new one
            ax_new = None
            for s, axis in static_axis.items():
                if is_static_axis(s, col) and axis is not None:
                    ax_new = axis
                    break
            if ax_new is None:
                ax_new = ax.twinx()
                ax_new.spines['right'].set_position(('axes', 1 + .05 * a))
                ax_new.set_ylabel(ylabel=col)
                a += 1
            for s, axis in static_axis.items():
                if is_static_axis(s, col) and axis is not None:
                    static_axis[s] = ax_new
                    ax_new.set_ylabel(ylabel=s)
                    break

            # plot the line
            df[col].plot(ax=ax_new, label=col, color=colors[i], style=linestyle, grid=False)
            ax_new.set_ylim([0, max(df[col].max(), ax_new.get_ylim()[1])])
            ax_new.set_xlim(xlim)

            # Proper legend position
            line, label = ax_new.get_legend_handles_labels()
            lines.append(line[-1])
            labels.append(label[-1])

    for _, axis in static_axis.items():
        if axis:
            axis.set_ylim([0, axis.get_ylim()[1]*ax2_static_shrink])

    # best lower|center|upper left|center|right
    _ = ax.legend(lines, labels, loc="lower left")

    return ax.get_figure()


def multi_plot_plotly(
        df: pd.DataFrame,
        title: str,
        xlim: tuple,
        fields_ax1=None,
        fields_ax2=None,
        linestyle: str = "lines",
        resample_sec: int = 1
) -> go.Figure | None:
    fields_ax1 = [k for k in fields_ax1 if k in df.columns and df[k].max() > 0] if fields_ax1 is not None else [k for k in df.columns if df[k].max() > 0]
    fields_ax2 = [k for k in df.columns if k not in fields_ax1 and df[k].max() > 0] if fields_ax2 is None else [k for k in fields_ax2 if k in df.columns and df[k].max() > 0]

    if (df.shape[0] <= 1) or (len(fields_ax1) + len(fields_ax2) == 0):
        print(f"WARNING! No data for {title}")
        return None

    if len(fields_ax1) == 0:
        fields_ax1 = [fields_ax2[0]]
        fields_ax2 = fields_ax2[1:]

    if resample_sec > 1:
        df = df.resample(f"{resample_sec}s").sum()/resample_sec

    # same axis for All queues_ and All ms_ and All err_
    static_axis = STATIC_AXIS.copy()

    # create a graph figure to plot all columns with respective colors
    fig = go.Figure()
    get_colors_by_action(fields_ax1+fields_ax2)

    # plot all fields_ax1 columns in left y-axis:
    for col in fields_ax1:
        fig.add_trace(go.Scatter(x=df.index, y=df[col], name=col, marker={"color": FIXED_COLORS[col]}, mode=linestyle))

    # common arguments for left y-axis and all right y-axis
    common_yaxis_args = dict(
        title_font=dict(size=12, family="Overpass, Open Sans, Courier New"), separatethousands=True,
        rangemode="tozero", zeroline=True, zerolinecolor="black", zerolinewidth=2,
        minor_tickwidth=20, title_standoff=0, minor_ticklen=1, nticks=10,
        showline=True, showticklabels=True, tickfont=dict(size=10, family="Arial")
    )

    # plot fields_ax2 columns in its own y-axis
    _y, _yaxis = 2, dict()
    for col in fields_ax2:

        # decide which axis to use or create new one
        for s, axis in static_axis.items():
            if is_static_axis(s, col):
                if axis is None:
                    _y_title = s
                    _y_curr = static_axis[s] = _y
                    _y += 1
                else:
                    _y_curr = axis
                break
        else:
            _y_title, _y_curr = col, _y
            _y += 1

        # plot column on secondary y-axis
        fig.add_trace(go.Scatter(x=df.index, y=df[col], name=col, yaxis=f"y{_y_curr}", marker={"color": FIXED_COLORS[col]}, mode=linestyle))

        # create secondary y-axis
        _y_name = f"yaxis{_y_curr}"
        if _y_name not in _yaxis:
            _yaxis[_y_name] = dict(
                title=_y_title, linewidth=10,
                tickmode="sync", tickprefix="  ",
                color=FIXED_COLORS[col],
                overlaying="y", side="right", anchor="free", autoshift=True,
                **common_yaxis_args
            )

    # create graph
    x_label = df.index.name if df.index.name else "index"
    fig.update_layout(
        title_text=title,
        plot_bgcolor='white',
        height=360,
        margin=dict(l=5, r=5, t=40, b=5),
        showlegend=True,
        legend=dict(orientation="h", yanchor="top"),

        xaxis=dict(
            title=dict(text=x_label, standoff=5), tickformat='%H:%M:%S', automargin="width", range=xlim,
            tickangle=0, domain=[0.0, 0.7], minor_ticklen=1, tickmode="auto", nticks=22,
            showline=False, showticklabels=True,
            showgrid=True, gridwidth=1, griddash="4px", gridcolor="#DDD", minor_gridwidth=1
        ),

        yaxis=dict(
            title="/".join(fields_ax1),
            tickmode="auto", color="black",
            showgrid=True, gridwidth=1, griddash="4px", gridcolor="#DDD",
            **common_yaxis_args
        ),

        **_yaxis
    )

    return fig


def multi_plot(
        df: pd.DataFrame,
        title: str,
        xlim: tuple[float],
        fields_ax1: list[str] = None,
        fields_ax2: list[str] = None,
        linestyle: str = "-",
        ax2_static_shrink: float = 1.0,
        resample_sec: int = 1,
        use_plotly: bool = True
) -> plt.Figure | go.Figure | None:
    # remove dot markers if dataframe has more than 4min to avoid thick lines
    if "." in linestyle and df.shape[0] > 240:
        linestyle.replace(".", "")

    if use_plotly:
        linestyle = "lines" if linestyle == "-" else "lines+markers"
        fig = multi_plot_plotly(df, title, xlim, fields_ax1=fields_ax1, fields_ax2=fields_ax2, linestyle=linestyle, resample_sec=resample_sec)
    else:
        fig = multi_plot_matplotlib(df, title, xlim, fields_ax1=fields_ax1, fields_ax2=fields_ax2, linestyle=linestyle, ax2_static_shrink=ax2_static_shrink, resample_sec=resample_sec)

    return fig


def bool_plot_horizontally(df: pd.DataFrame, title: str, xlim: tuple[float], columns=None) -> plt.Figure | None:
    # filter by selected columns
    columns = [k for k in df.columns if not k.startswith("acc_") and (df[k].max() > 0)] if columns is None else [k for k in df.columns if k in columns and df[k].max() > 0]
    if (df.shape[0] <= 1) or len(columns) == 0:
        print(f"WARNING! No data for {title}")
        return None

    df = df.copy()

    # for each column: set to True each second (row) that has data
    for col in columns:
        df[col] = df[col] != 0

    # convert boolean to 0/1
    df = df + 0

    # prepare plotting
    height = 5 * len(columns) / 10
    fig, ax = plt.subplots(figsize=(25, height))
    colors = get_colors_by_action(columns)

    # define Y-axis lane (horizontally) for each dataframe column
    lane = df.copy()
    for i, col in enumerate(columns):
        lane[col] = i - 0.5

    # plot each dataframe column in its own Y lane horizontally
    for col, color in zip(columns, colors):
        _ = ax.fill_between(df.index, lane[col], lane[col]+df[col], label=col, color=color)

    # set X-axis span
    ax.set_xlim(xlim)

    # change Y-ticks to labels
    ax.set_yticks(np.arange(len(columns)))
    ax.set_yticklabels(columns)

    # set grid and title
    ax.grid(axis="x")
    ax.set_title(title.upper())

    # set legend outside the plot
    _ = ax.legend(bbox_to_anchor=(1.01, 1.0), loc="upper left")

    return fig


def figure_to_attachment(fig: go.Figure | plt.Figure, filename: str, **kwargs) -> dict[str, Any]:
    if isinstance(fig, plt.Figure):
        tmpfile = BytesIO()
        fig.savefig(tmpfile, format="png", **kwargs)
        data = tmpfile.getvalue()
        name = f"{filename}.png"
    elif isinstance(fig, go.Figure):
        data = pio.to_image(fig, format="png", **kwargs)
        name = f"{filename}.png"
    else:
        raise ValueError(f"Can only receive a matplotlib figure or a plotly figure. Not {type(fig)}")

    attachment = {
        "mime": "image/png",
        "name": name,
        "data": data,
    }
    return attachment


def figure_to_html(fig: go.Figure) -> str:
    return pio.to_html(fig, full_html=False)


def get_colors_by_action(columns: list[str]) -> list[str]:

    def get_color(name: str):
        if name in FIXED_COLORS:
            return FIXED_COLORS[name]
        return _random_color(name)

    return [get_color(k) for k in columns]


def _random_color(name: str) -> str:
    def hex2int(h: str):
        if h[0] == "#":
            h = h[1:]
        return (int(h[0], 16)*16 + int(h[1], 16)) + \
            (int(h[2], 16)*16 + int(h[3], 16)) + \
            (int(h[4], 16)*16 + int(h[5], 16))

    if name not in FIXED_COLORS:
        if name.endswith("_err"):
            FIXED_COLORS[name] = "red"
        elif name.endswith("_timeout"):
            FIXED_COLORS[name] = "orange"
        else:
            _min_color, _max_color, color = hex2int("#303030"), hex2int("#E0E0D0"), "#FFFFFF"
            while not (_min_color < hex2int(color) < _max_color) or color in FIXED_COLORS.values():
                n = random.randint(0, len(COLORS)-1)
                color = COLORS[n]
            FIXED_COLORS[name] = color

    return FIXED_COLORS[name]
