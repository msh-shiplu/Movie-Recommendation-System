import dash
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import os.path
import dash_dangerously_set_inner_html as ddsih
from dash.dependencies import Input, Output, State
import time

from recom import CollaborativeFiltering

external_stylesheets = ['https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/css/bootstrap.min.css']
external_scripts = ['https://ajax.googleapis.com/ajax/libs/jquery/3.3.1/jquery.min.js', 'https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/js/bootstrap.min.js']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets, external_scripts=external_scripts)
app.config['suppress_callback_exceptions']=True

rating_df = pd.read_csv('ml-latest-small/ratings.csv', usecols=['userId','movieId','rating'], index_col='movieId')
link_df = pd.read_csv('ml-latest-small/links.csv', usecols=['movieId', 'imdbId'], index_col='movieId', dtype={'imdbId': str})
movie_df = pd.read_csv('ml-latest-small/movies.csv', index_col='movieId')

'''
********************** User ID *********************************
The below line is selecting a random user. If you want to fix it
provide the user it as follows
'''
# user_id = 280
user_id = rating_df.sample(n=1).iloc[0]['userId']

df = rating_df.join(link_df).join(movie_df)
user_df = df[df['userId']==user_id]
most_liked = user_df.sort_values(by=['rating'], ascending=False)
least_liked = user_df.sort_values(by=['rating'])

cf = CollaborativeFiltering(df)
user_idx = cf.user_map[user_id]
rc = cf.score[user_idx].argsort()[-100:][::-1]
rc = [cf.movie_idx_map[idx] for idx in rc]
recommend = df.loc[rc]
recommend = recommend[~recommend.index.isin(user_df.index)]
gg = recommend.groupby('movieId')['rating'].mean()
gg = gg.to_frame('rating')
recommend = recommend[['imdbId', 'title']].drop_duplicates()
recommend = recommend.join(gg).head(n=10)

# print(user_df.iloc[0]['rating']*12)
# print("width: "+str(int(user_df.iloc[0]['rating']*12))+"px; display:inline; background:url('images/stars.gif') no-repeat 0 bottom; position:absolute; height:11px;")
def get_movie_list_html(movies, title, rating_title="YOUR RATING"):
    return html.Div(children=[
        html.Div(children=[
            html.H2(title),
            html.P(children=[
                # html.A(children="See All", href="#")
            ], className="text-right")
        ], className="head")] +

        [html.Div(children=[
            html.Div(children=[
                html.A(children=[
                    html.Span(children=[
                        html.Span(r['title'], className='name')
                    ], className="play"),
                    html.Img(src='/assets/posters/tt'+r['imdbId']+'.jpg', alt=r['title'])
                ], href="/"+str(idx))
            ], className='movie-image'),
            html.Div(children=[
                html.P(rating_title),
                html.Div(children=[
                    html.Div(className="stars-in", style={"width": str(int(r['rating']*12))+"px"})
                ], className="stars"),
                # html.Span("12", className='comments')
            ], className="rating")
        ], className="movie") for idx, r in movies.iterrows()]# if os.path.exists('assets/posters/tt'+r['imdbId']+'.jpg')]
        + [html.Div("&nbsp;", className="cl")]
    , className='box')

app.layout = html.Div(children=[
    dcc.Location(id='url', refresh=False),
    html.Div(children=[
        html.Div(children=[
            html.Div(children=[
                dcc.Dropdown(
                    options=[{'label': str(uid), 'value': str(uid)} for uid in rating_df['userId'].unique()],
                    value = str(int(user_id)),
                    id = 'user-select',
                    placeholder='Select User'
                )
            ]),
            get_movie_list_html(recommend, "RECOMMENDATIONS", "AVG RATING"),
            get_movie_list_html(most_liked.head(n=10), "TOP RATED BY YOU"),
            get_movie_list_html(least_liked.head(n=10), "LEAST RATED BY YOU")
        ], id='content'),

    ], id="main"),
    dcc.Input(
        id='movie-id',
        value=0,
        type='hidden',
    )
], id='shell')

@app.callback(Output('movie-id','value'),
              [Input('url', 'pathname')])
def set_movie_id(pathname):
    if pathname is None or pathname == '/':
        return 0
    else:
        movie_id = int(pathname[1:])
        return movie_id

last_time = time.time()

@app.callback(Output('content','children'),
              [Input('url', 'pathname')])
def show(pathname):
    global user_id
    global user_df
    global movie_df
    rating_df = pd.read_csv('ml-latest-small/ratings.csv', usecols=['userId','movieId','rating'], index_col='movieId')
    df = rating_df.join(link_df).join(movie_df)

    if pathname is None or pathname == '/':

        user_df = df[df['userId']==user_id]
        most_liked = user_df.sort_values(by=['rating'], ascending=False)
        least_liked = user_df.sort_values(by=['rating'])

        cf = CollaborativeFiltering(df)
        user_idx = cf.user_map[user_id]
        rc = cf.score[user_idx].argsort()[-100:][::-1]
        rc = [cf.movie_idx_map[idx] for idx in rc]
        recommend = df.loc[rc]
        recommend = recommend[~recommend.index.isin(user_df.index)]
        gg = recommend.groupby('movieId')['rating'].mean()
        gg = gg.to_frame('rating')
        recommend = recommend[['imdbId', 'title']].drop_duplicates()
        recommend = recommend.join(gg).head(n=10)
        return [
            html.Div(children=[
                dcc.Dropdown(
                    options=[{'label': str(uid), 'value': str(uid)} for uid in rating_df['userId'].unique()],
                    value = str(int(user_id)),
                    id = 'user-select',
                    placeholder='Select User'
                )
            ]),
            get_movie_list_html(recommend, "RECOMMENDATIONS", "AVG RATING"),
            get_movie_list_html(most_liked.head(n=10), "TOP RATED BY YOU"),
            get_movie_list_html(least_liked.head(n=10), "LEAST RATED BY YOU")
        ]
    else:
        movie_id = int(pathname[1:])
        # global last_time
        # current_time = time.time()
        # if last_time is not None and current_time - last_time < 3:
        #     raise Exception
        # last_time = current_time
        return html.Div(children=[
            html.Div(children=[
                html.Img(src='/assets/posters/tt'+df.loc[movie_id]['imdbId'].iloc[0]+'.jpg', alt=df.loc[movie_id]['title'].iloc[0])
            ], className='col-lg-6'),
            html.Div(children=[
                html.Div(children=[
                    html.H1(df.loc[movie_id]['title'].iloc[0])
                ], className='row'),
                html.Div(children=[
                    html.Div(children=[
                        html.Div(children=[
                            html.P('AVG RATING'),
                            html.Div(children=[
                                html.Div(className="stars-in", style={"width": str(int(df.groupby('movieId')['rating'].mean()[movie_id]*12))+"px"})
                            ], className="stars"),
                            # html.Span("12", className='comments')
                        ], className="rating")
                    ], className='col-lg-6'),
                    html.Div(children=[
                        html.H3(str(round(df.groupby('movieId')['rating'].mean()[movie_id], 2))+" / 5")
                    ], className='col-lg-6'),
                ], className='row'),
                html.Div(children=[
                    html.P('YOUR RATING'),
                    dcc.Slider(
                        min=1,
                        max=9,
                        marks={1: 1, 2: 1.5, 3: 2, 4: 2.5, 5: 3, 6: 3.5, 7: 4, 8: 4.5, 9: 5},
                        value=int((user_df.loc[movie_id]['rating']-0.5)*2) if user_df.index.contains(movie_id) else 1,
                        id="movie-rating",
                    ),
                ], className='row'),
                dcc.ConfirmDialog(
                    id='confirm',
                    message='Rating saved successfully.',
                ),
                html.Div(children=[
                    html.Button(id='submit-button', n_clicks=0, children='Save Rating', className='btn btn-success'),
                ], className='row', style={'margin-top': '50px'}, hidden="hidden" if user_df.index.contains(movie_id) else ""),
                html.Div(children=[
                    dcc.Link('<< Return to home', href='/'),
                ], className='row', style={'margin-top': '50px'}),
            ], className='col-lg-6'),
        ], className='row')

@app.callback(Output('confirm', 'displayed'),
              [Input('submit-button', 'n_clicks')],
              [State(component_id='movie-rating', component_property='value'),
               State(component_id='movie-id', component_property='value')])
               # State(component_id='content', component_property='children')])
def save_rating_and_update(n_clicks, rating, movieid):
    if n_clicks == 0:
        return False
    global user_id
    global rating_df
    new_df = pd.DataFrame(data=[[int(user_id), int(movieid), rating/2+0.5, int(time.time())]],columns=['userId', 'movieId', 'rating', 'timestamp'])
    with open('ml-latest-small/ratings.csv', 'a') as f:
        new_df.to_csv(f, header=False, index=False)

    return True

@app.callback(Output('main', 'children'),
              [Input('user-select', 'value'), Input('url', 'pathname')]
              )
def change_user(user_val, pathname):
    if pathname is not None and pathname != '/':
        raise Exception
    global user_id
    user_id = int(user_val)
    global df
    user_df = df[df['userId']==user_id]
    most_liked = user_df.sort_values(by=['rating'], ascending=False)
    least_liked = user_df.sort_values(by=['rating'])
    global cf
    #cf = CollaborativeFiltering(df)
    user_idx = cf.user_map[user_id]
    rc = cf.score[user_idx].argsort()[-100:][::-1]
    rc = [cf.movie_idx_map[idx] for idx in rc]
    recommend = df.loc[rc]
    recommend = recommend[~recommend.index.isin(user_df.index)]
    gg = recommend.groupby('movieId')['rating'].mean()
    gg = gg.to_frame('rating')
    recommend = recommend[['imdbId', 'title']].drop_duplicates()
    recommend = recommend.join(gg).head(n=10)
    return html.Div(children=[
        html.Div(children=[
            dcc.Dropdown(
                options=[{'label': str(uid), 'value': str(uid)} for uid in rating_df['userId'].unique()],
                value = str(int(user_id)),
                id = 'user-select',
                placeholder='Select User'
            )
        ]),
        get_movie_list_html(recommend, "RECOMMENDATIONS", "AVG RATING"),
        get_movie_list_html(most_liked.head(n=10), "TOP RATED BY YOU"),
        get_movie_list_html(least_liked.head(n=10), "LEAST RATED BY YOU")
    ], id='content')

if __name__ == '__main__':
    app.run_server(debug=True)