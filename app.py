from dash import Dash, dcc, html, Input, Output
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import netCDF4 as nc

# Set up the app
app = Dash(__name__)
server = app.server

# Load the data
grid = nc.Dataset('data/tancitaro_sampled_150m.nc')
x = grid['x'][:]
y = grid['y'][:]
z = grid['z'][:]
z = np.round(z/1000, 3)

df = pd.read_csv('data/enjambres.csv')
df['profundidad'] = -df['profundidad']
df['fecha_utc'] = pd.to_datetime(df['fecha_utc'])

# Join fecha_utc and hora_utc into a single datetime column with the format 'YYYY-MM-DDTHH:MM:SS'
df['fecha_hora_utc'] = df['fecha_utc'].dt.strftime('%Y-%m-%d') + 'T' + df['hora_utc']

# Set the markdown text for the app layout
markdown_text = '''
# Enjambre sísmico Michoacán 2019 - 2022

Enjambres sísmicos registrados entre abril 2019 y agosto 2022 en los alrededores
de los volcanes Tancítaro y Paricutín en Michoacán, México.
'''
datepicker_label = "#### Rango de fechas UTC:"
magnitudes_label = "#### Rango de magnitudes:"
topo_label = "#### Exageración de elevación:"
foot_label = '''
### Referencias

- Sismos del [Servicio Sismológico Nacional](http://www.ssn.unam.mx/).
- Topografía de [OpenTopography](https://www.opentopography.org/).
- Creado por [Juan Carlos Bucio T.](https://jcbucio.github.io/).
- Código fuente en [GitHub](https://github.com/JCBucio/enjambre-sismico-mich).
'''

marks_range = np.arange(2.0, 5.0, 0.5)

# Set up the app layout
app.layout = html.Div([
    dcc.Markdown(children=markdown_text, style={'textAlign': 'center'}),
    html.Div([
        dcc.Markdown(children=datepicker_label),
        dcc.DatePickerRange(
            id='date-picker-range',
            min_date_allowed=df['fecha_utc'].min(),
            max_date_allowed=df['fecha_utc'].max(),
            start_date=df['fecha_utc'].min(),
            end_date=df['fecha_utc'].max(),
            clearable=True,
            start_date_placeholder_text="Fecha inicial",
            end_date_placeholder_text="Fecha final",
        )
    ], style={'textAlign': 'center'}),
    dcc.Loading(
        id="loading-1",
        type="default",
        children=html.Div(id="loading-output-1", style={'padding': '30px'}),
    ),
    dcc.Graph(id='graph', style={'height': '60vh'}),
    html.Div([
        html.Div([
            html.Div([
                dcc.Markdown(topo_label),
                dcc.Slider(
                    id='topo-slider',
                    min=1,
                    max=10,
                    value=1,
                    marks={str(m): str(m) for m in range(1, 11)},
                    step=1
                )
            ], style={'padding': 10, 'flex': 1, 'textAlign': 'center'}),
            html.Div([
                dcc.Markdown(magnitudes_label),
                dcc.RangeSlider(
                    id='range-slider',
                    min=2.0,
                    max=5.0,
                    value=[2.0, 5.0],
                    marks={str(m): str(m) for m in marks_range},
                    step=0.1
                )
            ], style={'padding': 10, 'flex': 1, 'textAlign': 'center'})
        ], style={'display': 'flex', 'flex-direction': 'row'}),
    ]),
    html.Br(),
    dcc.Markdown(foot_label)
], style={'fontFamily': 'monospace', 'margin': '2rem'})

# Define the callback for the graph
@app.callback(
    Output('graph', 'figure'),
    Output('loading-output-1', 'children'),
    Input('range-slider', 'value'),
    Input('date-picker-range', 'start_date'),
    Input('date-picker-range', 'end_date'),
    Input('topo-slider', 'value'),
)

def update_chart(slider_range, start_date, end_date, topo_exag):
    # Get the lower and upper bounds of the magnitudes
    low, high = slider_range

    # Filter by date
    # If there is no date selected, show all data
    if start_date is None:
        start_date = df['fecha_utc'].min()
    
    if end_date is None:
        end_date = df['fecha_utc'].max()

    # Convert the date strings to datetime objects
    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)

    # Filter by date and magnitude
    mask = df[(df['magnitud'] >= low) & (df['magnitud'] <= high) & (df['fecha_utc'] >= start_date) & (df['fecha_utc'] <= end_date)]

    # If the mask is empty, show a message
    if len(mask) > 0:

        # Create the figure
        fig = go.Figure()

        # Add the topography
        fig.add_trace(go.Surface(
            z=z*topo_exag, x=x, y=y, 
            name="Topografía", 
            showscale=False,
            # Set the hover template and multiply the z value by 1000 to convert from km to m
            hovertemplate='<b>Longitud</b>: %{x}<br><b>Latitud</b>: %{y}<br><b>Elevación</b>: %{z} km',
            showlegend=True,
        ))

        # Add the earthquakes
        fig.add_trace(go.Scatter3d(
            x=mask['longitud'],
            y=mask['latitud'],
            z=mask['profundidad'],
            mode='markers',
            marker=dict(
                size=1.5,
                color=mask['magnitud'],
                colorscale='Viridis',
                colorbar=dict(title='Magnitudes', titleside='bottom', xpad=0.5, ypad=0.5),
                opacity=0.8
            ),
            # Set the labels in the hover tooltip
            hovertemplate=
                '<b>Fecha y hora UTC</b>: %{customdata[0]}<br>' +
                '<b>Latitud</b>: %{customdata[1]}<br>' +
                '<b>Longitud</b>: %{customdata[2]}<br>' +
                '<b>Profundidad (km)</b>: %{customdata[3]}<br>' +
                '<b>Magnitud</b>: %{customdata[4]}<br>' +
                '<b>Referencia</b>: %{customdata[5]}<br>',
            customdata=mask[['fecha_hora_utc', 'latitud', 'longitud', 'profundidad', 'magnitud', 'referencia']].values,
            name="Sismos",
            showlegend=True   
        ))

        # Format the labels
        fig.update_layout(
            scene = dict(
                xaxis_title='Latitud',
                yaxis_title='Longitud',
                zaxis_title='Profundidad (km)'
            ),
            margin=dict(l=0, r=0, b=0, t=0),
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=0.01,
                font=dict(
                    size=14
                )
            ),
            showlegend=True,
            legend_title_text='Capas',
            font_family="monospace"
        )

    else:
        # If there is no data, show a message
        fig = px.scatter_3d()
        fig.update_layout(
            title="No hay datos para mostrar",
            font_family="monospace",
            # Put the title in the middle of the x and y axis
            title_x=0.5
       )
    
    return fig, " "

if __name__ == '__main__':
    app.run_server(debug=False)