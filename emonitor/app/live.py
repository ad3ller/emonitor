# packages
import os
import sqlite3
import datetime
# emonitor
from emonitor.tools import db_path, history
from emonitor.core import INSTRUM_FILE
from emonitor.config import EmonitorConfig
# ploting
from bokeh.core.properties import value
from bokeh.io import curdoc
from bokeh.layouts import row, column
from bokeh.plotting import figure
from bokeh.models import ColumnDataSource
from bokeh.models.widgets import CheckboxGroup, Select, Slider, Button
from bokeh.palettes import Category10
colors = Category10[10]

config = EmonitorConfig(INSTRUM_FILE)

def get_data(db, start, end, **kwargs):
    # data
    try:
        fil = db_path(db)
        conn = sqlite3.connect(fil)
        df = history(conn, start, end, **kwargs)
        conn.close()
    except:
        df = {}
    finally:
        return df

def make_plot(instrum):
    # config
    settings = config[instrum]
    y_axis_label = settings.get("y_axis_label", None)
    y_axis_type = settings.get("y_axis_type", "linear")
    
    # figure
    fig = figure(plot_height=500, plot_width=700,
                 x_axis_type="datetime", y_axis_type=y_axis_type)

    # plotting
    for i, col in enumerate(source.column_names[1:]):
        fig.line(source.column_names[0], col,
                 line_color=colors[i], legend=value(col), source=source)

    # format
    if y_axis_label is not None:
        fig.yaxis.axis_label = y_axis_label
    fig.legend.location = "top_left"
    fig.legend.click_policy="hide"

    return fig

def plot(attr, old, new):
    replot()

def replot():
    global start, end, source, fig
    # time range
    hours = time_slider.value
    end = datetime.datetime.now()
    delta = datetime.timedelta(**{"hours": hours})
    start = end - delta
    # data
    instrum = instrum_select.value
    db = config[instrum]['db']
    source = ColumnDataSource(get_data(db, start, end,
                              dropna=False, ascending=True, limit=1000))
    # plot
    fig = make_plot(instrum)
    curdoc().clear()
    curdoc().add_root(row(controls, fig))
    curdoc().title = f"{instrum}"

def update_data():
    global start, end, source
    # time range
    hours = time_slider.value
    end = datetime.datetime.now()
    delta = datetime.timedelta(**{"hours": hours})
    start = end - delta
    # data
    instrum = instrum_select.value
    db = config[instrum]['db']
    source.data = ColumnDataSource(get_data(db, start, end,
                                   dropna=False, ascending=True, limit=1000)).data

def stream_data():
    global end, start, source
    # time range
    _start = end
    _end = datetime.datetime.now()
    # data
    instrum = instrum_select.value
    db = config[instrum]['db']
    new_data = get_data(db, _start, _end,
                        dropna=False, ascending=True, limit=None)
    if not isinstance(new_data, dict) and len(new_data.index) > 0:
        source.stream(new_data)
        # overwrite (on success)
        start = _start
        end = _end

def set_stream(attr, old, new):
    global stream
    try:
        curdoc().remove_periodic_callback(stream)
    except:
        pass
    if stream_slider.value > 0:
        stream = curdoc().add_periodic_callback(stream_data, stream_slider.value * 1000)

#default
instrum = config.instruments()[0]

# inputs
instrum_select = Select(value=instrum, options=sorted(config.instruments()))
instrum_select.on_change('value', plot)

time_slider = Slider(start=0.1, end=24, value=4, step=.1,
                     title="time delta (hours)", callback_policy='mouseup')

stream_slider = Slider(start=1, end=60, value=10, step=1,
                       title="refresh time (seconds)", callback_policy='mouseup')
stream_slider.on_change('value', set_stream)

update_button = Button(label="update", button_type="success")
update_button.on_click(update_data)

controls = column(instrum_select, time_slider, stream_slider, update_button)

# plot
plot(None, None, None)
stream = curdoc().add_periodic_callback(stream_data, stream_slider.value * 1000)

# periodically replot
timeout = curdoc().add_periodic_callback(replot, 1024 * 1000)