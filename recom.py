import numpy as np

class CollaborativeFiltering:
    def __init__(self, df):
        n_users = df.userId.unique().shape[0]
        n_movies = df.index.unique().shape[0]

        self.ratings = np.zeros((n_users, n_movies))
        self.movie_idx, self.user_idx = 0, 0
        self.movie_map = {}
        self.user_map = {}
        self.movie_idx_map = {}
        for idx, r in df.iterrows():
            if idx not in self.movie_map:
                self.movie_map[idx] = self.movie_idx
                self.movie_idx_map[self.movie_idx] = idx
                self.movie_idx += 1
            if r['userId'] not in self.user_map:
                self.user_map[r['userId']] = self.user_idx
                self.user_idx += 1

            self.ratings[self.user_map[r['userId']], self.movie_map[idx]] = r['rating']

        self.weight = self.calc_similarity(self.ratings)
        self.score = self.calc_predicted_score(self.ratings, self.weight)

    def calc_similarity(self, ratings):
        s = ratings.dot(ratings.T) + 1e-9
        norms = np.array([np.sqrt(np.diagonal(s))])
        s = s / norms
        s = s / norms.T
        return s

    def calc_predicted_score(self, ratings, weight):
        avg = ratings.mean(axis=1)
        nratings = (ratings - avg[:, np.newaxis]).copy()
        score = np.divide(weight.dot(nratings), np.array(np.abs(weight).sum(axis=1)).reshape((weight.shape[0], 1)))
        score += avg[:, np.newaxis]
        return score