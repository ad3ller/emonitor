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
from bokeh.models.widgets import Select, DatePicker, Button
from bokeh.palettes import Category10
# emonitor
from emonitor.tools import db_path, history
from emonitor.core import INSTRUM_FILE
from emonitor.config import EmonitorConfig


COLORS = Category10[10]
MAX_ROWS = 1000


def get_data(instrum, start, end, **kwargs):
    """ query sqlite database for live data
    """
    # data
    try:
        # output data
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
                     line_color=COLORS[i], legend_label=col, source=source)
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
    global instrum, source, fig
    # time range
    start = datetime.datetime.strptime(start_ctrl.value + ' 00:00:00', '%Y-%m-%d %H:%M:%S')
    end = datetime.datetime.strptime(end_ctrl.value + ' 23:59:59', '%Y-%m-%d %H:%M:%S')
    # data
    instrum = instrum_select.value
    source = ColumnDataSource(get_data(instrum, start, end,
                                       dropna=False, ascending=True, limit=MAX_ROWS))
    # plot
    fig = make_plot(instrum)
    fig.title.text = 'history'
    curdoc().clear()
    curdoc().add_root(row(controls, fig))
    curdoc().title = f"{instrum}"


def refresh_plot(attr, old, new):
    """ event triggered plot_data() call
    """
    plot_data()


# default values
config = EmonitorConfig(INSTRUM_FILE)
instrum = config.instruments()[0]

# controls
## instrument
instrum_select = Select(title='table', value=instrum, options=sorted(config.instruments()))
instrum_select.on_change('value', refresh_plot)

## start time delta
start_ctrl = DatePicker(title='start', min_date=datetime.date(2017, 1, 1), max_date=datetime.date.today(),
                        value=datetime.date.today() - datetime.timedelta(days=7))
start_ctrl.on_change('value', refresh_plot)

end_ctrl = DatePicker(title='end', min_date=datetime.date(2017, 1, 1), max_date=datetime.date.today(),
                      value=datetime.date.today())
end_ctrl.on_change('value', refresh_plot)

## force update_data()
update_button = Button(label="refresh", button_type="success")
update_button.on_click(plot_data)

controls = column(instrum_select, start_ctrl, end_ctrl, update_button)

# plot
plot_data()
