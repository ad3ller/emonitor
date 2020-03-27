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
from bokeh.models import ColumnDataSource
from bokeh.models.widgets import Select, DatePicker, Button, Paragraph
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
    global instrum, timezone, source, fig
    # time range
    start_str = f"{start_date.value} {start_hour.value}:{start_minute.value}"
    start = datetime.datetime.strptime(start_str, '%Y-%m-%d %H:%M')
    logging.debug(f'start: {start}')

    end_str = f"{end_date.value} {end_hour.value}:{end_minute.value}"
    end = datetime.datetime.strptime(end_str, '%Y-%m-%d %H:%M')
    logging.debug(f'end: {end}')
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


def refresh_plot(attr, old, new):
    """ event triggered plot_data() call
    """
    plot_data()


hours = ["{:02d}".format(h) for h in range(24)]
minutes = ["{:02d}".format(m) for m in range(60)]

# default values
config = EmonitorConfig(INSTRUM_FILE)
instrum = config.instruments()[0]
timezone = config.get(instrum, 'plot_timezone', fallback='UTC')
logger.debug("timezone: " + timezone)
today = datetime.datetime.now(tz=pytz.timezone(timezone)).date()

# controls
## instrument
instrum_select = Select(width=300, title='table', value=instrum, options=sorted(config.instruments()))
instrum_select.on_change('value', refresh_plot)

## start time delta
start_date = DatePicker(title='start', width=140, 
                        min_date=datetime.date(2020, 1, 1), 
                        max_date=today,
                        value=today - datetime.timedelta(days=7))
start_hour = select = Select(title='hour', value="0", options=hours, width=70)
start_minute = select = Select(title='min', value="0", options=minutes, width=70)
start_date.on_change('value', refresh_plot)
start_hour.on_change('value', refresh_plot)
start_minute.on_change('value', refresh_plot)

end_date = DatePicker(title='end', width=140, 
                      min_date=datetime.date(2020, 1, 1),
                      max_date=today,
                      value=today)
end_date.on_change('value', refresh_plot)
end_hour = select = Select(title='hour', value="23", options=hours, width=70)
end_minute = select = Select(title='min', value="59", options=minutes, width=70)
end_hour.on_change('value', refresh_plot)
end_minute.on_change('value', refresh_plot)

## live button
live_button = Button(width=130, margin=[15, 10, 15, 10], label="live", button_type="default")
live_button.js_on_click(CustomJS(code=""" window.location.href='./live'; """))

## force update_data()
history_button = Button(width=130, margin=[15, 10, 15, 10], label="history", button_type="primary")
history_button.on_click(plot_data)

tz_text = Paragraph(text=f"timezone: {timezone}", width=340)

controls = column(row(live_button, history_button),
                  instrum_select,
                  row(start_date, start_hour, start_minute),
                  row(end_date, end_hour, end_minute),
                  tz_text)

# plot
plot_data()
