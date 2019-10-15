# -*- coding: utf-8 -*-
"""
Created on Sun Apr 28 17:33:12 2019

@author: Adam
"""
import os
import sqlite3
import datetime
import warnings
import logging
logger = logging.getLogger(__name__)
# ploting
from bokeh.core.properties import value
from bokeh.io import curdoc
from bokeh.layouts import row, column
from bokeh.plotting import figure
from bokeh.models import ColumnDataSource
from bokeh.models.widgets import Select, Slider, Button
from bokeh.palettes import Category10
# emonitor
from emonitor.tools import db_path, history
from emonitor.core import INSTRUM_FILE
from emonitor.config import EmonitorConfig


COLORS = Category10[10]


def get_data(instrum, start, end, **kwargs):
    """ query sqlite database for live data
    """
    # data
    try:
        # try live data first
        fil = db_path(instrum, live=True)
        if os.path.isfile(fil):
            pass
        else:
            # fallback to output data
            db = config.get(instrum, 'db', fallback=instrum)
            fil = db_path(db, live=False)
            if not os.path.isfile(fil):
                raise OSError(f"{fil} not found")
        conn = sqlite3.connect(fil)
        df = history(conn, start, end, **kwargs)
        conn.close()
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
                     line_color=COLORS[i], legend=value(col), source=source)
            i += 1

    # format
    if y_axis_label is not None:
        fig.yaxis.axis_label = y_axis_label

    # supress empty legend warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        fig.legend.location = "top_left"
        fig.legend.click_policy = "hide"

    return fig


def plot_data():
    """ get_data() and make_plot()
    """
    global instrum, latest, source, fig
    # time range
    hours = time_slider.value
    end = datetime.datetime.now()
    start = end - datetime.timedelta(**{"hours": hours})
    latest = end
    # data
    instrum = instrum_select.value
    source = ColumnDataSource(get_data(instrum, start, end,
                                       dropna=False, ascending=True, limit=1000))
    # plot
    fig = make_plot(instrum)
    curdoc().clear()
    curdoc().add_root(row(controls, fig))
    curdoc().title = f"{instrum}"


def update_data():
    """ update plot data source
    """
    global latest, source
    # time range
    hours = time_slider.value
    end = datetime.datetime.now()
    start = end - datetime.timedelta(**{"hours": hours})
    latest = end
    # data
    instrum = instrum_select.value
    source.data = ColumnDataSource(get_data(instrum, start, end,
                                            dropna=False, ascending=True, limit=1000)).data


def stream_data():
    """ stream new data
    """
    global latest, source
    # time range
    start = latest
    end = datetime.datetime.now()
    # data
    instrum = instrum_select.value
    new_data = get_data(instrum, start, end,
                        dropna=False, ascending=True, limit=None)
    if not isinstance(new_data, dict) and len(new_data.index) > 0:
        new_data = ColumnDataSource(new_data).data
        source.stream(new_data)
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

# controls
## instrument
instrum_select = Select(value=instrum, options=sorted(config.instruments()))
instrum_select.on_change('value', refresh_plot)

## live time delta
time_slider = Slider(start=0.1, end=24, value=4, step=.1,
                     title="time delta (hours)", callback_policy='mouseup')

## streaming refresh time
stream_slider = Slider(start=1, end=60, value=10, step=1,
                       title="refresh time (seconds)", callback_policy='mouseup')
stream_slider.on_change('value', refresh_stream)

## force update_data()
update_button = Button(label="update", button_type="success")
update_button.on_click(update_data)

controls = column(instrum_select, time_slider, stream_slider, update_button)

# plot
plot_data()
stream = curdoc().add_periodic_callback(stream_data, stream_slider.value * 1000)

# periodically refresh plot
timeout = curdoc().add_periodic_callback(update_data, 1024 * 1000)
