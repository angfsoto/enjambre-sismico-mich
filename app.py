from dash import Dash, dcc, html, Input, Output
import plotly.express as px
import plotly.io as pio
import pandas as pd

app = Dash(__name__)

server = app.server
# Set the default theme to 'plotly_dark'
# pio.templates.default = 'plotly_dark'

df = pd.read_csv('data/enjambres.csv')
df['profundidad'] = -df['profundidad']

markdown_text = '''
# Enjambre sísmico Michoacán 2019 - 2022

Gráfica de sismos registrados entre 2019 y 2022 en los alrededores
de los volcanes Tancítaro y Paricutín en Michoacán, México. Creado por [Juan Carlos Bucio T.](https://jcbucio.github.io/).
'''

magnitudes_label = "### Arrastra el slider para ver un rango diferente de magnitudes:"

app.layout = html.Div([
    dcc.Markdown(children=markdown_text),
    dcc.Graph(id='graph', style={'height': '70vh'}),
    dcc.Markdown(magnitudes_label),
    dcc.RangeSlider(
        id='range-slider',
        min=2.0, max=5.0, step=0.1,
        marks={2.0: '2.0', 3.0: '3.0', 4.0: '4.0', 5.0: '5.0'},
        value=[2.0, 5.0]
    )
], style={'fontFamily': 'monospace', 'margin': '2rem'})

@app.callback(
    Output('graph', 'figure'),
    Input('range-slider', 'value')
)

def update_bar_chart(slider_range):
    low, high = slider_range
    mask = (df['magnitud'] > low) & (df['magnitud'] < high)

    fig = px.scatter_3d(df[mask], x="latitud", y="longitud", z="profundidad", size='magnitud', size_max=10,
                        color="magnitud", hover_data=['fecha_utc', 'hora_utc', 'latitud', 'longitud', 'profundidad', 'magnitud', 'referencia'])

    # Format the labels
    fig.update_layout(scene = dict(
                    xaxis_title='Latitud',
                    yaxis_title='Longitud',
                    zaxis_title='Profundidad'),
                    margin=dict(r=20, b=10, l=10, t=10))

    # Format the labels for the colorbar
    fig.update_layout(coloraxis_colorbar=dict(title="Magnitudes"))

    # Change the font family to monospace
    fig.update_layout(font_family="monospace")

    # Set the figure to use all the space in the browser
    fig.update_layout(margin=dict(l=0, r=0, b=0, t=0))
    
    return fig


if __name__ == '__main__':
    app.run_server(debug=False)