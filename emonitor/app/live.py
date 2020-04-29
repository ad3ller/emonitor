# -*- coding: utf-8 -*-
"""
Created on Sun Apr 28 17:33:12 2019

@author: Adam
"""
import os
import sqlite3
import datetime
import pytz
import warnings
import logging
logger = logging.getLogger(__name__)
# ploting
from bokeh.core.properties import value
from bokeh.io import curdoc
from bokeh.models.callbacks import CustomJS
from bokeh.layouts import row, column
from bokeh.plotting import figure
from bokeh.models import ColumnDataSource, HoverTool
from bokeh.models.widgets import Select, Slider, Button, Paragraph
from bokeh.palettes import Category10
# emonitor
from emonitor.tools import db_path, history
from emonitor.core import INSTRUM_FILE
from emonitor.config import EmonitorConfig


COLORS = Category10[10]
MAX_ROWS = 1000
TOOLTIPS = [('date',   '@TIMESTAMP{%a %F}'),
            ('time',   '@TIMESTAMP{%T}'),
            ("sensor", "$name"),
            ("value", "$y")]


def get_data(instrum, start, end, **kwargs):
    """ query sqlite database for live data
    """
    # data
    try:
        # try live data first
        fil = db_path(instrum, live=True)
        if os.path.isfile(fil):
            # live data
            conn = sqlite3.connect(fil)
            df = history(conn, start, end, **kwargs)
            conn.close()
            if len(df.index) > 0:
                df.index = df.index.tz_localize(None)
                return df
        # fallback to output data
        db = config.get(instrum, 'db', fallback=instrum)
        fil = db_path(db, live=False)
        if not os.path.isfile(fil):
            raise OSError(f"{fil} not found")
        conn = sqlite3.connect(fil)
        df = history(conn, start, end, **kwargs)
        conn.close()
        # localize timestamps for plotting
        df.index = df.index.tz_localize(None)
    except:
        df = {}
    finally:
        return df


def make_plot(instrum):
    """ configure bokeh figure and plot data
    """
    # config
    settings = config[instrum]
    tcol = settings.get("tcol", "TIMESTAMP")
    plot_height = int(settings.get("plot_height", 500))
    plot_width = int(settings.get("plot_width", 700))
    y_axis_label = settings.get("y_axis_label", None)
    y_axis_type = settings.get("y_axis_type", "linear")

    # figure
    fig = figure(plot_height=plot_height, plot_width=plot_width,
                 x_axis_type="datetime", y_axis_type=y_axis_type)

    # plotting
    i = 0
    for col in source.column_names:
        if col != tcol:
            fig.line(tcol, col,
                     line_color=COLORS[i], legend_label=col, name=col, source=source)
            i += 1

    # format
    if y_axis_label is not None:
        fig.yaxis.axis_label = y_axis_label

    # hover
    fig.add_tools(HoverTool(tooltips=TOOLTIPS, formatters={'@TIMESTAMP' : 'datetime'}))

    # supress empty legend warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        fig.legend.location = "top_left"
        fig.legend.click_policy = "hide"

    return fig


def plot_data():
    """ get_data() and make_plot()
    """
    global instrum, timezone, latest, source, fig
    # time range
    hours = time_slider.value
    end = datetime.datetime.now(tz=pytz.utc)
    start = end - datetime.timedelta(**{"hours": hours})
    latest = end
    # data
    instrum = instrum_select.value
    source = ColumnDataSource(get_data(instrum, start, end,
                                       dropna=False,
                                       ascending=True,
                                       tz=timezone,
                                       limit=MAX_ROWS))
    # plot
    fig = make_plot(instrum)
    curdoc().clear()
    curdoc().add_root(row(controls, fig))
    curdoc().title = f"{instrum}"


def stream_data():
    """ stream new data
    """
    global latest, timezone, source
    # time range
    start = latest
    end = datetime.datetime.now(tz=pytz.utc)
    # data
    instrum = instrum_select.value
    new_data = get_data(instrum, start, end,
                        dropna=False,
                        ascending=True,
                        tz=timezone,
                        limit=None)
    if not isinstance(new_data, dict) and len(new_data.index) > 0:
        source.stream(new_data, rollover=MAX_ROWS)
        latest = end
        logger.debug("stream new data")
    else:
        logger.debug("no new data")


def refresh_plot(attr, old, new):
    """ event triggered plot_data() call
    """
    plot_data()


def refresh_stream(attr, old, new):
    """ event triggered configure streaming
    """
    global stream
    try:
        curdoc().remove_periodic_callback(stream)
    except:
        pass
    if stream_slider.value > 0:
        stream = curdoc().add_periodic_callback(stream_data, stream_slider.value * 1000)


# default values
config = EmonitorConfig(INSTRUM_FILE)
instrum = config.instruments()[0]
timezone = config.get(instrum, 'plot_timezone', fallback='UTC')
logger.debug("timezone: " + timezone)

# controls
## instrument
instrum_select = Select(width=300, title='table', value=instrum, options=sorted(config.instruments()))
instrum_select.on_change('value', refresh_plot)

## live time delta
time_slider = Slider(start=0.1, end=24, value=4, step=.1,
                     title="time delta (hours)", width=300)
time_slider.on_change('value_throttled', refresh_plot)

## streaming refresh time
stream_slider = Slider(start=1, end=60, value=10, step=1,
                       title="refresh (seconds)", width=300)
stream_slider.on_change('value_throttled', refresh_stream)

## force update_data()
live_button = Button(width=130, margin=[15, 10, 15, 10], label="live", button_type="primary")
live_button.on_click(plot_data)

history_button = Button(width=130, margin=[15, 10, 15, 10], label="history", button_type="default")
history_button.js_on_click(CustomJS(code=""" window.location.href='./history'; """))

tz_text = Paragraph(text=f"timezone: {timezone}", width=340)

controls = column(row(live_button, history_button),
                  instrum_select,
                  time_slider,
                  stream_slider,
                  tz_text)

# plot
plot_data()
stream = curdoc().add_periodic_callback(stream_data, stream_slider.value * 1000)

# periodically refresh plot
timeout = curdoc().add_periodic_callback(plot_data, 1024 * 1000)