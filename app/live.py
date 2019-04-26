# packages
import os
import sqlite3
from emonitor.tools import db_path, history, live
# ploting
from bokeh.core.properties import value
from bokeh.io import curdoc
from bokeh.layouts import row, column
from bokeh.plotting import figure
from bokeh.models import ColumnDataSource
from bokeh.models import Select
from bokeh.palettes import Category10
colors = Category10[10]

def get_data(table):
    # data
    fil = db_path(table)
    conn = sqlite3.connect(fil)
    df = live(conn, delta)
    conn.close()
    return df

def plot_live(table):
    # config
    settings = config[table]
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
    fig.legend.click_policy="hide"

    return fig

def replot(attr, old, new):
    global source
    table = table_select.value
    source = ColumnDataSource(get_data(table))
    fig = plot_live(table)
    curdoc().clear()
    curdoc().add_root(row(controls, fig))
    curdoc().title = "emonitor"

#def refresh(attr, old, new):
#    source.stream(new_data)

#default
table = 'pressure'
delta = {"hours":72}

# config
config = {
    'pressure': {
        'y_axis_label': 'mbar',
        'y_axis_type': 'log',

    },
    'temperature': {
        'y_axis_label': 'Kelvin',
    },
}

# inputs
table_select = Select(value=table, title='table', options=sorted(config.keys()))
table_select.on_change('value', replot)
controls = column(table_select)

# plot
source = ColumnDataSource(get_data(table))
fig = plot_live(table)

# output
curdoc().add_root(row(controls, fig))
curdoc().title = "emonitor"