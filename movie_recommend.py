# FILE: movie_recommend.py
# PURPOSE: Sylver Movies — content-based movie recommendation app.
# Run with: streamlit run movie_recommend.py

import streamlit as st
from PIL import Image
import pickle
import pandas as pd
import requests
import os

# Page config must be the very first Streamlit call
logo = Image.open("images/SM.jpg")
st.set_page_config(
    page_title="Sylver Movies",
    page_icon=logo,
    layout="wide"
)

# TMDB API settings
# Your API key from themoviedb.org → Settings → API → API Key (v3 auth)
TMDB_API_KEY    = "f9ecf55069d2ed1f79d0326c72107435"
TMDB_POSTER_URL = "https://image.tmdb.org/t/p/w500"
TMDB_SEARCH_URL = "https://api.themoviedb.org/3/search/movie"

# CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Lato:wght@300;400;700&display=swap');

    .stApp { background-color: #0a0a12; }
    html, body, [class*="css"] { font-family: 'Lato', sans-serif; }

    #MainMenu { visibility: hidden; }
    footer    { visibility: hidden; }
    header    { visibility: hidden; }

    hr { border-color: #1e1e35 !important; }

    section[data-testid="stSidebar"] {
        background-color: #08080f !important;
        border-right: 1px solid #1e1e35;
    }
    section[data-testid="stSidebar"] button,
    section[data-testid="stSidebar"] .stButton button,
    section[data-testid="stSidebar"] .stButton > button {
        background: transparent !important;
        border: none !important;
        color: #aaaacc !important;
        text-align: left !important;
        font-family: 'Lato', sans-serif !important;
        font-size: 0.92em !important;
        letter-spacing: 1px !important;
        padding: 10px 12px !important;
        width: 100% !important;
        border-radius: 6px !important;
    }
    section[data-testid="stSidebar"] button:hover {
        background: #1a1a2e !important;
        color: #ffffff !important;
    }

    .main-title {
        font-family: 'Bebas Neue', sans-serif;
        font-size: 3em;
        letter-spacing: 5px;
        color: #ffffff;
        margin-bottom: 2px;
    }
    .sub-title {
        color: #6666aa;
        font-size: 0.9em;
        letter-spacing: 2px;
        margin-top: 0;
        margin-bottom: 20px;
    }
    .section-heading {
        font-family: 'Bebas Neue', sans-serif;
        font-size: 1.4em;
        letter-spacing: 3px;
        color: #ffffff;
        margin: 14px 0 16px 0;
        padding-left: 12px;
        border-left: 3px solid #c0c0d0;
    }
    .card-title {
        font-family: 'Lato', sans-serif;
        font-weight: 700;
        font-size: 0.83em;
        color: #eeeef5;
        line-height: 1.3;
        margin-bottom: 4px;
        min-height: 2.4em;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
    }
    .card-meta {
        color: #7777a0;
        font-size: 0.76em;
        margin-bottom: 6px;
    }
    .card-rating { color: #c9a84c; font-weight: 700; }
    .poster-placeholder {
        width: 100%;
        padding-bottom: 148%;
        position: relative;
        border-radius: 6px;
        background: linear-gradient(160deg, #1a1a2e 0%, #16213e 100%);
        border: 1px solid #2a2a45;
        margin-bottom: 8px;
    }
    .poster-placeholder-inner {
        position: absolute;
        top: 0; left: 0; right: 0; bottom: 0;
        display: flex;
        align-items: center;
        justify-content: center;
        font-family: 'Bebas Neue', sans-serif;
        font-size: 3em;
        color: #3a3a5c;
    }
</style>
""", unsafe_allow_html=True)


# Load model files
@st.cache_resource
def load_data():
    movies     = pickle.load(open("artifacts/movie_list.pkl", "rb"))
    similarity = pickle.load(open("artifacts/similarity.pkl", "rb"))
    return movies, similarity

try:
    movies, similarity = load_data()
except FileNotFoundError:
    st.error("Model files not found. Run preprocessing first:")
    st.code("python notebooks/preprocessing.py")
    st.stop()


# Fetch full movie details (poster, year, rating, genres, overview) by TMDB movie_id
@st.cache_data(ttl=86400)
def fetch_movie_details(movie_id):
    if not TMDB_API_KEY or TMDB_API_KEY == "your_api_key_here":
        return {}
    try:
        resp = requests.get(
            f"https://api.themoviedb.org/3/movie/{movie_id}",
            params={"api_key": TMDB_API_KEY},
            timeout=4
        )
        data = resp.json()
        return {
            "poster_url":  (TMDB_POSTER_URL + data["poster_path"]) if data.get("poster_path") else None,
            "year":        data.get("release_date", "")[:4],
            "rating":      round(data.get("vote_average", 0), 1),
            "genres":      [g["name"] for g in data.get("genres", [])[:2]],
            "overview":    data.get("overview", ""),
        }
    except Exception:
        pass
    return {}


# Get top 5 recommendations for a given movie title
def recommend(movie):
    if movie not in movies["title"].values:
        return [], []

    index     = movies[movies["title"] == movie].index[0]
    distances = sorted(
        list(enumerate(similarity[index])),
        key=lambda x: x[1],
        reverse=True
    )[1:6]

    rec_titles   = []
    rec_movie_ids = []
    for i in distances:
        rec_titles.append(movies.iloc[i[0]].title)
        rec_movie_ids.append(int(movies.iloc[i[0]].movie_id))

    return rec_titles, rec_movie_ids


# Render a single movie card with poster, title, year, rating, and genres
def render_card(title, movie_id, key_prefix):
    details    = fetch_movie_details(movie_id)
    poster_url = details.get("poster_url")

    if poster_url:
        st.image(poster_url, use_container_width=True)
    else:
        initial = title[0].upper() if title else "?"
        st.markdown(
            f'<div class="poster-placeholder">'
            f'<div class="poster-placeholder-inner">{initial}</div>'
            f'</div>',
            unsafe_allow_html=True
        )

    display = title if len(title) <= 34 else title[:31] + "..."
    st.markdown(f'<div class="card-title">{display}</div>', unsafe_allow_html=True)

    year   = details.get("year", "")
    rating = details.get("rating", 0)
    genres = details.get("genres", [])

    if year or genres:
        meta = year
        if genres:
            meta = (meta + " · " if meta else "") + " · ".join(genres)
        st.markdown(f'<div class="card-meta">{meta}</div>', unsafe_allow_html=True)

    if rating:
        st.markdown(f'<div class="card-meta card-rating">⭐ {rating}/10</div>', unsafe_allow_html=True)


# Sidebar
with st.sidebar:
    st.image(logo, use_container_width=True)
    st.markdown("<br>", unsafe_allow_html=True)

    st.markdown(
        "<p style='color:#333355; font-size:0.72em; letter-spacing:2px;'>ABOUT</p>",
        unsafe_allow_html=True
    )
    st.markdown(
        "<p style='color:#7777a0; font-size:0.82em; line-height:1.6;'>"
        "Select any movie to discover 5 personalised content-based recommendations "
        "powered by TF-IDF and cosine similarity."
        "</p>",
        unsafe_allow_html=True
    )
    st.markdown("---")

    st.markdown(
        "<p style='color:#333355; font-size:0.72em; letter-spacing:2px;'>DATASET</p>",
        unsafe_allow_html=True
    )
    st.markdown(
        f"<p style='color:#7777a0; font-size:0.82em;'>{len(movies):,} movies · TMDB 5000</p>",
        unsafe_allow_html=True
    )

    st.markdown(
        "<p style='color:#333355; font-size:0.72em; letter-spacing:2px; margin-top:12px;'>METHOD</p>",
        unsafe_allow_html=True
    )
    st.markdown(
        "<p style='color:#7777a0; font-size:0.82em;'>"
        "TF-IDF Vectorizer · Porter Stemming · Cosine Similarity"
        "</p>",
        unsafe_allow_html=True
    )

    st.markdown(
        "<p style='color:#333355; font-size:0.72em; letter-spacing:2px; margin-top:12px;'>FEATURES USED</p>",
        unsafe_allow_html=True
    )
    st.markdown(
        "<p style='color:#7777a0; font-size:0.82em; line-height:1.7;'>"
        "Overview · Genres · Keywords<br>Top 3 Cast · Director"
        "</p>",
        unsafe_allow_html=True
    )


# Main page header
st.markdown(
    "<div class='main-title'>SYLVER MOVIES</div>"
    "<div class='sub-title'>CONTENT-BASED MOVIE RECOMMENDER</div>",
    unsafe_allow_html=True
)
st.markdown("---")

# Movie selector dropdown
selected_movie = st.selectbox(
    "Choose a movie to get recommendations:",
    movies["title"].values,
    label_visibility="collapsed",
    placeholder="Search or select a movie..."
)

# Recommend button
if st.button("Get Recommendations", type="primary", use_container_width=False):
    titles, movie_ids = recommend(selected_movie)

    if not titles:
        st.warning("No recommendations found for this movie.")
    else:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(
            f"<div class='section-heading'>Because you watched — {selected_movie}</div>",
            unsafe_allow_html=True
        )

        cols = st.columns(5)
        for idx, (title, movie_id) in enumerate(zip(titles, movie_ids)):
            with cols[idx]:
                render_card(title, movie_id, key_prefix=f"rec_{idx}")