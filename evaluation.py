import pandas as pd
import os.path
import numpy as np
from recom import CollaborativeFiltering

rating_df = pd.read_csv('ml-latest-small/ratings.csv', usecols=['userId','movieId','rating'], index_col='movieId')
link_df = pd.read_csv('ml-latest-small/links.csv', usecols=['movieId', 'imdbId'], index_col='movieId', dtype={'imdbId': str})
movie_df = pd.read_csv('ml-latest-small/movies.csv', index_col='movieId')
user_id = 599

df = rating_df.join(link_df).join(movie_df)
user_df = df[df['userId']==user_id]
most_liked = user_df.sort_values(by=['rating'], ascending=False).head(n=10)
least_liked = user_df.sort_values(by=['rating'])

df = df.reset_index()
new_df = df.copy()

indices = []
for idx, row in df.iterrows():
    if row['movieId'] not in most_liked.index:
        continue
    if row['userId'] != 599:
        continue
    indices.append(idx)

new_df.drop(indices)
new_df.set_index('movieId')
cf = CollaborativeFiltering(new_df)

user_idx = cf.user_map[user_id]
rc = cf.score[user_idx].argsort()[-100:][::-1]
rc = [cf.movie_idx_map[idx] for idx in rc]
recommend = df.loc[rc]
recommend = recommend[~recommend.index.isin(user_df.index)]
gg = recommend.groupby('movieId')['rating'].mean()
gg = gg.to_frame('rating')
recommend = recommend[['imdbId', 'title']].drop_duplicates()
recommend = recommend.join(gg).head(n=100)

print(most_liked.to_string())
print(recommend.to_string())

cnt = [0]*100
for idx, row in most_liked.iterrows():
    i = 0
    for idx2, row2 in recommend.head(n=100).iterrows():
        if row['imdbId'] == row2['imdbId']:
            cnt[i] += 1
        i+= 1

print(sum(cnt[:10]), sum(cnt[:20]), sum(cnt[:30]), sum(cnt[:40]), sum(cnt[:50]), sum(cnt[:60]), sum(cnt[:70]), sum(cnt[:80]), sum(cnt[:90]), sum(cnt[:]))

