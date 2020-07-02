import dash
from dash.dependencies import Output, Input, Event
import dash_core_components as dcc
import dash_html_components as html
import plotly
import plotly.graph_objs as go
import sqlite3
import pandas as pd

conn = sqlite3.connect('twitter.db', check_same_thread=False)

app_colors = {
    'background': '#4f5b66	',
    'text': '#FFFFFF',
    'sentiment-plot': '#41EAD4',
    'someothercolor': '#CECECE',
}

app = dash.Dash(__name__)
server = app.server
app.layout = html.Div(
    [html.H2('Live Twitter Sentiment', style={'color': "#CECECE"}),
     dcc.Input(id='sentiment_term', value='', placeholder='enter a term', type='text',
               style={'color': app_colors['someothercolor']}),
     dcc.Graph(id='live-graph', animate=False, figure={
         'layout': {
             'plot_bgcolor': app_colors['background'],
             'paper_bgcolor': app_colors['background'],
         }
     }),
     dcc.Interval(
         id='graph-update',
         interval=1 * 1000
     ),

     ], style={'backgroundColor': app_colors['background'],
               'margin-top': '-30px',
               'height': '2000px'},
)

external_css = ["https://cdnjs.cloudflare.com/ajax/libs/materialize/1.0.0/css/materialize.min.css"]
for css in external_css:
    app.css.append_css({"external_url": css})


@app.callback(Output('live-graph', 'figure'),
              [Input(component_id='sentiment_term', component_property='value')],
              events=[Event('graph-update', 'interval')])
def update_graph_scatter(sentiment_term):
    try:
        conn = sqlite3.connect('twitter.db')
        c = conn.cursor()
        df = pd.read_sql("SELECT * FROM sentiment WHERE tweet LIKE ? ORDER BY unix DESC LIMIT 1000", conn,
                         params=('%' + sentiment_term + '%',))
        df.sort_values('unix', inplace=True)
        df['sentiment_smoothed'] = df['sentiment'].rolling(int(len(df) / 5)).mean()

        df['date'] = pd.to_datetime(df['unix'], unit='ms')
        df.set_index('date', inplace=True)

        df = df.resample('1000ms').mean()
        df.dropna(inplace=True)
        X = df.index
        Y = df.sentiment_smoothed

        data = plotly.graph_objs.Scatter(
            x=X,
            y=Y,
            name='Scatter',
            mode='lines+markers'
        )

        return {'data': [data], 'layout': go.Layout(xaxis=dict(range=[min(X), max(X)]),
                                                    yaxis=dict(range=[min(Y), max(Y)]),
                                                    title='Term: {}'.format(sentiment_term))}

    except Exception as e:
        with open('errors.txt', 'a') as f:
            f.write(str(e))
            f.write('\n')


if __name__ == '__main__':
    app.run_server(debug=True)
