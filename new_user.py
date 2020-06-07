import dash
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import numpy as np
import os.path
import dash_dangerously_set_inner_html as ddsih
from dash.dependencies import Input, Output, State
import time
from scipy.spatial.distance import cosine

from recom import CollaborativeFiltering

external_stylesheets = ['https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/css/bootstrap.min.css']
external_scripts = ['https://ajax.googleapis.com/ajax/libs/jquery/3.3.1/jquery.min.js',
                    'https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/js/bootstrap.min.js']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets, external_scripts=external_scripts)
app.config['suppress_callback_exceptions']=True
genres = ['Action', 'Adventure', 'Animation', "Children's", 'Comedy', 'Crime', 'Documentary', 'Drama', 'Fantasy',
          'Film-Noir', 'Horror', 'Musical', 'Mystery', 'Romance', 'Sci-Fi', 'Thriller', 'War', 'Western']
movie_df = pd.read_csv('ml-latest-small/movies.csv', index_col='movieId')
rating_df = pd.read_csv('ml-latest-small/ratings.csv', usecols=['userId','movieId','rating'], index_col='movieId')
link_df = pd.read_csv('ml-latest-small/links.csv', usecols=['movieId', 'imdbId'], index_col='movieId', dtype={'imdbId': str})

gg = rating_df.groupby('movieId')['rating'].agg(['mean','count'])
movie_profile = {}
movies = []
user_id = rating_df['userId'].max() + 1
for idx, row in movie_df.iterrows():
    movie_profile[idx] = np.zeros(18)
    for i, g in enumerate(genres):
        if g in row['genres']:
            movie_profile[idx][i] = 1

app.layout = html.Div(children=[
    dcc.Location(id='url', refresh=False),
    html.Div(children=[
        html.Div(children=[
            html.H3('Distribute 5 points among the movie genres below')]+
            [html.Div(children=[
                html.Div(children = [html.Label(g)], className="col-lg-2"),
                html.Div(children=[dcc.Input(type="text", value='0', id="in"+str(idx), style={'margin': '5px'})],
                         className="col-lg-4")
            ],className='row') for idx, g in enumerate(genres)] +
            [html.Div("&nbsp;", className="cl"),
             html.Button(id='submit-button', n_clicks=0, children='Submit', className='btn btn-success',
                         style={'margin-top': '20px', 'float': 'right'}),
             dcc.ConfirmDialog(
                 id='confirm',
                 message='Sum of all the input values must be 5!',
             )
             ]
        , id='content'),
    ], id="main"),
], id='shell')

@app.callback(Output('confirm', 'displayed'),
                [Input('submit-button', 'n_clicks')],
                [State('in'+str(idx), 'value') for idx, g in enumerate(genres)])
def display_confirm(n_clicks,  *inputs):
    if n_clicks == 0:
        return False
    sum = 0
    for i in inputs:
        sum += float(i)
    if sum != 5:
        return True
    return False

@app.callback(Output('content', 'children'),
    [Input('submit-button', 'n_clicks')],
              [State('in'+str(idx), 'value') for idx, g in enumerate(genres)])
def update_output(n_clicks, *inputs):
    if n_clicks == 0:
        raise Exception
    sum = 0
    v = []
    for i in inputs:
        sum += float(i)
        v.append(float(i))
    if sum != 5:
        raise Exception

    v = np.array(v)
    global movie_profile
    global gg

    global movies
    movies = []
    total_rat = gg['count'].sum()
    for mid, pr in movie_profile.items():
        if mid not in gg.index:
            continue
        ct = gg.loc[mid]['count']
        if ct / total_rat * 100 < 0.05:
            continue
        c = cosine(pr, v)
        movies.append([c, mid])
    movies.sort()
    movies = movies[:100]
    for i in range(len(movies)):
        movies[i][0] += 1-gg.loc[movies[i][1]]['mean']/5
    movies.sort()
    global movie_df
    global rating_df
    global link_df
    global user_id
    movies = movies[:10]
    # movie_id = movies[-1][1]
    return html.Div(children=[html.Div(children=[html.Div(children=[
        html.Div(children=[
            html.Img(src='/assets/posters/tt'+link_df.loc[movie_id]['imdbId']+'.jpg', alt=movie_df.loc[movie_id]['title'])
        ], className='col-lg-6'),
        html.Div(children=[
            html.Div(children=[
                html.H1(movie_df.loc[movie_id]['title'])
            ], className='row'),
            html.Div(children=[
                html.P("Categories: "+movie_df.loc[movie_id]['genres'].replace('|', ', '))
            ], className='row'),
            html.Div(children=[
                html.Div(children=[
                    html.Div(children=[
                        html.P('AVG RATING'),
                        html.Div(children=[
                            html.Div(className="stars-in", style={"width": str(int(gg.loc[movie_id]['mean']*12))+"px"})
                        ], className="stars"),
                        # html.Span("12", className='comments')
                    ], className="rating")
                ], className='col-lg-6'),
                html.Div(children=[
                    html.H3(str(round(gg.loc[movie_id]['mean'], 2))+" / 5")
                ], className='col-lg-6'),
            ], className='row'),
            html.Div(children=[
                dcc.Checklist(
                    options=[{'label': ' PROVIDE RATING', 'value': 'yes'}],
                    values=[],
                    id="check-"+str(index)
                ),
            ], className='row'),
            html.Div(children=[

                dcc.Slider(
                    min=1,
                    max=9,
                    marks={1: 1, 2: 1.5, 3: 2, 4: 2.5, 5: 3, 6: 3.5, 7: 4, 8: 4.5, 9: 5},
                    value=5,
                    id="rating-"+str(index),
                ),
            ], className='row'),
        ], className='col-lg-6'),
    ], className='row'), html.Hr()], style={'margin-top':'15px'}) for index, [_, movie_id] in enumerate(movies)]+
    [html.Div(children=[
        html.Button(id='submit-button2', n_clicks=0, children='Submit Ratings', className='btn btn-success'),
    ], className='row', style={'margin-top': '50px', 'float': 'right'}),
        dcc.ConfirmDialog(
            id='confirm2',
            message='Rating submitted successfully. Your user id is '+str(user_id),
        ),
        dcc.ConfirmDialog(
            id='confirm3',
            message='Please rate at least 3 movies!',
        )]
    )

@app.callback(Output('confirm3', 'displayed'),
              [Input('submit-button2', 'n_clicks')],
              [State('check-'+str(i), 'values') for i in range(10)])
def check_ratings(n_clicks, *values):
    if n_clicks == 0:
        return False
    cnt = 0
    for x in values:
        if len(x) > 0:
            cnt += 1
    if cnt < 3:
        return True
    return False

@app.callback(Output('confirm2', 'displayed'),
              [Input('submit-button2', 'n_clicks')],
              [State('check-'+str(i), 'values') for i in range(10)] +
               [State('rating-'+str(i), 'value') for i in range(10)])
def save_ratings(n_clicks, *values):
    if n_clicks == 0:
        return False
    global movies
    global user_id
    global rating_df
    if user_id is None:
        user_id = rating_df['userId'].max() + 1
    data = []
    for i, [_, movie_id] in enumerate(movies):
        if len(values[i]) == 0:
            continue
        data.append([int(user_id), int(movie_id), values[i+10]/2+0.5, int(time.time())])
    if len(data) < 3:
        return False
    new_df = pd.DataFrame(data=data,columns=['userId', 'movieId', 'rating', 'timestamp'])
    with open('ml-latest-small/ratings.csv', 'a') as f:
        new_df.to_csv(f, header=False, index=False)
    return True

if __name__ == '__main__':
    app.run_server(debug=True)