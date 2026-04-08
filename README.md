# Sylver Movies

A content-based movie recommender built with Python and Streamlit. Pick any movie from the TMDB 5000 dataset and get 5 similar recommendations, with posters and metadata fetched live from the TMDB API.

## How it works

Each movie is represented as a bag of tags — drawn from its overview, genres, keywords, top 3 cast members, and director. Multi-word names are collapsed into single tokens (`SamWorthington`) to prevent false matches. The tags are lowercased, stemmed with Porter Stemmer, then vectorized using TF-IDF. Cosine similarity across all 4,806 movies is precomputed and saved to disk. At runtime the app loads those artifacts and slices the similarity matrix to find the top 5 closest matches.

## Setup

**1. Install dependencies**
```bash
pip install -r requirements.txt
```

**2. Download the dataset**

Download `tmdb_5000_movies.csv` and `tmdb_5000_credits.csv` from [Kaggle](https://www.kaggle.com/datasets/tmdb/tmdb-movie-metadata) and place them in a `dataset/` folder at the project root.

**3. Build the model**
```bash
python notebooks/processing.py
```
This produces `artifacts/movie_list.pkl` and `artifacts/similarity.pkl`. Only needs to run once.

**4. Add your TMDB API key**

Get a free key from [themoviedb.org](https://www.themoviedb.org/settings/api) and set it in `movie_recommend.py`:
```python
TMDB_API_KEY = f9ecf55069d2ed1f79d0326c72107435
```

**5. Run the app**
```bash
streamlit run movie_recommend.py
```

## Project structure

```
├── artifacts/              # Saved model files (generated)
│   ├── movie_list.pkl
│   └── similarity.pkl
├── dataset/                # Raw CSVs (not tracked)
├── images/
│   └── SM.jpg
├── notebooks/
│   └── processing.py       # Preprocessing + model building
├── movie_recommend.py      # Streamlit app
└── requirements.txt
```

## Stack

| | |
|---|---|
| UI | Streamlit |
| Vectorizer | TF-IDF (scikit-learn, 5000 features) |
| Stemmer | NLTK Porter Stemmer |
| Similarity | Cosine similarity |
| Poster/metadata | TMDB REST API |
| Dataset | TMDB 5000 (Kaggle) |
