# FILE: notebooks/preprocessing.py
# PURPOSE: Builds the recommendation model from the TMDB dataset.
# Run this ONCE before launching the app.
# Output: artifacts/movie_list.pkl and artifacts/similarity.pkl
#
# How to run:
#   python notebooks/preprocessing.py

import numpy as np
import pandas as pd
import ast
import pickle
import os
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from nltk.stem import PorterStemmer

DATASET_DIR   = os.path.join(os.path.dirname(__file__), '..', 'dataset')
ARTIFACTS_DIR = os.path.join(os.path.dirname(__file__), '..', 'artifacts')
os.makedirs(ARTIFACTS_DIR, exist_ok=True)

print("Loading datasets...")
movies  = pd.read_csv(os.path.join(DATASET_DIR, 'tmdb_5000_movies.csv'))
credits = pd.read_csv(os.path.join(DATASET_DIR, 'tmdb_5000_credits.csv'))

# Merge on title
movies = movies.merge(credits, on='title')
print(f"  Merged shape: {movies.shape}")

# Keep only the columns we need for building tags
movies = movies[['movie_id', 'title', 'overview', 'genres', 'keywords', 'cast', 'crew']]

# Drop nulls
movies.dropna(inplace=True)
print(f"  After cleaning: {movies.shape}")

# Extract name list from JSON string
def convert(text):
    return [i['name'] for i in ast.literal_eval(text)]

# Extract top 3 cast names only
def convert_cast(text):
    return [i['name'] for i in ast.literal_eval(text)[:3]]

# Extract director name from crew JSON
def fetch_director(text):
    for i in ast.literal_eval(text):
        if i['job'] == 'Director':
            return [i['name']]
    return []

# Remove spaces so multi-word names become single tokens
# e.g. "Sam Worthington" becomes "SamWorthington"
def remove_space(items):
    return [i.replace(' ', '') for i in items]

print("Processing fields...")
movies['genres'] = movies['genres'].apply(convert).apply(remove_space)
movies['keywords'] = movies['keywords'].apply(convert).apply(remove_space)
movies['cast'] = movies['cast'].apply(convert_cast).apply(remove_space)
movies['crew'] = movies['crew'].apply(fetch_director).apply(remove_space)
movies['overview'] = movies['overview'].apply(lambda x: x.split())

# Combine all fields into one tags list then join to a string
movies['tags'] = (
    movies['overview'] + movies['genres'] +
    movies['keywords'] + movies['cast'] + movies['crew']
)

new_df = movies[['movie_id', 'title', 'tags']].copy()
new_df['tags'] = new_df['tags'].apply(lambda x: ' '.join(x)).str.lower()

# Stemming reduces words to their root form
# e.g. "running" and "runner" both become "run" — improves matching
ps = PorterStemmer()
def stem(text):
    return ' '.join([ps.stem(word) for word in text.split()])

print("Stemming tags (this takes a moment)...")
new_df['tags'] = new_df['tags'].apply(stem)

# Vectorise using TF-IDF (Term Frequency–Inverse Document Frequency)
# TF-IDF down-weights very common words across all movies, giving more
# importance to terms that are distinctive to each film.
# max_features=5000 keeps the 5000 most informative terms.
# stop_words removes filler words like 'the', 'and', 'is'.
print("Vectorising with TF-IDF...")
cv = TfidfVectorizer(max_features=5000, stop_words='english')
vectors = cv.fit_transform(new_df['tags']).toarray()
print(f"  Vector shape: {vectors.shape}")

# Cosine similarity measures the angle between two movie vectors
# Score 1.0 = identical, 0.0 = nothing in common
print("Computing cosine similarity (this may take ~30 seconds)...")
similarity = cosine_similarity(vectors)
print(f"  Similarity matrix shape: {similarity.shape}")

# Save both model files to artifacts/
pickle.dump(new_df,     open(os.path.join(ARTIFACTS_DIR, 'movie_list.pkl'), 'wb'))
pickle.dump(similarity, open(os.path.join(ARTIFACTS_DIR, 'similarity.pkl'), 'wb'))