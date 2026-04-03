# FILE: movie_recommend.py
# PURPOSE: Sylver Movies — personalised content-based movie recommendation app.
# Run with: streamlit run movie_recommend.py

import streamlit as st
from PIL import Image
import pickle
import pandas as pd
import numpy as np
import requests
import os
import json
import hashlib

# ── Page config ────────────────────────────────────────────────────────────────
logo = Image.open("images/SM.jpg")
st.set_page_config(page_title="Sylver Movies", page_icon=logo, layout="wide")

# ── TMDB API ───────────────────────────────────────────────────────────────────
TMDB_API_KEY    = "f9ecf55069d2ed1f79d0326c72107435"
TMDB_BASE_URL   = "https://api.themoviedb.org/3"
TMDB_POSTER_URL = "https://image.tmdb.org/t/p/w500"

# ── CSS ────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Lato:wght@300;400;700&display=swap');

    .stApp { background-color: #0a0a12; }
    html, body, [class*="css"] { font-family: 'Lato', sans-serif; }
    #MainMenu, footer, header { visibility: hidden; }
    hr { border-color: #1e1e35 !important; }

    /* ── Sidebar ── */
    section[data-testid="stSidebar"] {
        background-color: #08080f !important;
        border-right: 1px solid #1e1e35;
    }
    section[data-testid="stSidebar"] button,
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

    /* ── Navbar ── */
    .navbar-brand {
        font-family: 'Bebas Neue', sans-serif;
        font-size: 1.6em;
        letter-spacing: 4px;
        color: #ffffff;
        margin-bottom: 0;
    }
    .navbar-sub {
        color: #6666aa;
        font-size: 0.7em;
        letter-spacing: 2px;
        margin-top: -2px;
    }

    /* Nav buttons — default */
    div[data-testid="stHorizontalBlock"] .stButton > button {
        background:    transparent !important;
        border:        none !important;
        border-bottom: 2px solid transparent !important;
        color:         #8888aa !important;
        font-family:   'Lato', sans-serif !important;
        font-size:     0.78em !important;
        font-weight:   700 !important;
        letter-spacing: 1.5px !important;
        text-transform: uppercase !important;
        padding:       10px 6px !important;
        border-radius: 0 !important;
        width:         100% !important;
    }
    div[data-testid="stHorizontalBlock"] .stButton > button:hover {
        color: #ffffff !important;
        border-bottom: 2px solid #01b4e4 !important;
    }

    /* ── Active nav indicator ── */
    .nav-active-line {
        height: 2px;
        background: #01b4e4;
        border-radius: 1px;
        margin: -6px 0 10px 0;
    }
    .nav-inactive-line {
        height: 2px;
        background: transparent;
        margin: -6px 0 10px 0;
    }

    /* ── Page titles ── */
    .page-title {
        font-family: 'Bebas Neue', sans-serif;
        font-size: 2em;
        letter-spacing: 4px;
        color: #ffffff;
        margin-bottom: 4px;
    }
    .page-sub {
        color: #6666aa;
        font-size: 0.82em;
        letter-spacing: 1.5px;
        margin-bottom: 20px;
    }
    .section-heading {
        font-family: 'Bebas Neue', sans-serif;
        font-size: 1.3em;
        letter-spacing: 3px;
        color: #ffffff;
        margin: 14px 0 16px 0;
        padding-left: 12px;
        border-left: 3px solid #01b4e4;
    }

    /* ── Movie cards ── */
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
    .card-meta  { color: #7777a0; font-size: 0.76em; margin-bottom: 3px; }
    .card-rating{ color: #c9a84c; font-weight: 700; font-size: 0.76em; }
    .poster-placeholder {
        width: 100%; padding-bottom: 148%; position: relative;
        border-radius: 6px;
        background: linear-gradient(160deg, #1a1a2e 0%, #16213e 100%);
        border: 1px solid #2a2a45; margin-bottom: 8px;
    }
    .poster-placeholder-inner {
        position: absolute; top:0; left:0; right:0; bottom:0;
        display: flex; align-items: center; justify-content: center;
        font-family: 'Bebas Neue', sans-serif; font-size: 3em; color: #3a3a5c;
    }

    /* ── Genre / country chips ── */
    .genre-chip {
        display: inline-block;
        background: #12122a;
        border: 1px solid #2a2a45;
        color: #aaaacc;
        border-radius: 20px;
        padding: 6px 16px;
        font-size: 0.82em;
        letter-spacing: 1px;
        cursor: pointer;
        margin: 4px;
    }

    /* ── User badge ── */
    .user-badge {
        background: #12122a; border: 1px solid #2a2a45;
        border-radius: 8px; padding: 10px 14px; margin-bottom: 10px;
    }
    .user-name  { color: #c0c0e0; font-weight: 700; font-size: 0.9em; letter-spacing: 1px; }
    .user-stats { color: #555577; font-size: 0.78em; margin-top: 3px; }

    /* ── Watchlist empty state ── */
    .empty-state {
        text-align: center; padding: 60px 20px;
        color: #444466; font-size: 0.95em; letter-spacing: 1px;
    }
    .empty-state-icon { font-size: 3em; margin-bottom: 12px; }
</style>
""", unsafe_allow_html=True)



# DATA & MODELS

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


# User Management (JSON file)
USERS_FILE = "users.json"

def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    return {}

def save_users(u):
    with open(USERS_FILE, "w") as f:
        json.dump(u, f, indent=2)

def _key(username): return username.strip().lower()

def hash_password(p): return hashlib.sha256(p.encode()).hexdigest()

def attempt_login(username, password):
    users = load_users()
    k = _key(username)
    if k in users and users[k]["password"] == hash_password(password):
        return users[k]["watched"]
    return None

def attempt_register(username, password):
    users = load_users()
    k = _key(username)
    if len(username.strip()) < 3:
        return False, "Username must be at least 3 characters."
    if len(password) < 6:
        return False, "Password must be at least 6 characters."
    if k in users:
        return False, "That username is already taken."
    users[k] = {"password": hash_password(password), "watched": []}
    save_users(users)
    return True, "Account created! You can now sign in."

def mark_watched(username, movie_id):
    users = load_users()
    k = _key(username)
    if k in users and movie_id not in users[k]["watched"]:
        users[k]["watched"].append(movie_id)
        save_users(users)
        st.session_state.watched = list(users[k]["watched"])

def unmark_watched(username, movie_id):
    users = load_users()
    k = _key(username)
    if k in users and movie_id in users[k]["watched"]:
        users[k]["watched"].remove(movie_id)
        save_users(users)
        st.session_state.watched = list(users[k]["watched"])


# SESSION STATE
_defaults = {
    "logged_in":    False,
    "username":     "",
    "watched":      [],
    "page":         "Home",
    "genre_id":     None,
    "genre_name":   "",
    "country_code": None,
    "country_name": "",
}
for _k, _v in _defaults.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v


# TMDB API HELPERS
@st.cache_data(ttl=3600)
def tmdb_get(endpoint, **params):
    try:
        r = requests.get(
            f"{TMDB_BASE_URL}{endpoint}",
            params={"api_key": TMDB_API_KEY, **params},
            timeout=6
        )
        return r.json()
    except Exception:
        return {}

@st.cache_data(ttl=86400)
def fetch_movie_details(movie_id):
    data = tmdb_get(f"/movie/{movie_id}")
    return {
        "poster_url": (TMDB_POSTER_URL + data["poster_path"]) if data.get("poster_path") else None,
        "year":       data.get("release_date", "")[:4],
        "rating":     round(data.get("vote_average", 0), 1),
        "genres":     [g["name"] for g in data.get("genres", [])[:2]],
        "overview":   data.get("overview", ""),
    }

@st.cache_data(ttl=3600)
def fetch_genre_list():
    return tmdb_get("/genre/movie/list").get("genres", [])

@st.cache_data(ttl=3600)
def fetch_popular(page=1):
    return tmdb_get("/movie/popular", page=page).get("results", [])

@st.cache_data(ttl=3600)
def fetch_top_rated(page=1):
    return tmdb_get("/movie/top_rated", page=page).get("results", [])

@st.cache_data(ttl=3600)
def fetch_by_genre(genre_id, page=1):
    return tmdb_get("/discover/movie", with_genres=genre_id,
                    sort_by="popularity.desc", page=page).get("results", [])

@st.cache_data(ttl=3600)
def fetch_by_country(country_code, page=1):
    return tmdb_get("/discover/movie", with_origin_country=country_code,
                    sort_by="popularity.desc", page=page).get("results", [])



# Recommendation Logic
def recommend(movie, top_n=5):
    if movie not in movies["title"].values:
        return [], []
    idx = movies[movies["title"] == movie].index[0]
    dists = sorted(enumerate(similarity[idx]), key=lambda x: x[1], reverse=True)[1:top_n+1]
    return [movies.iloc[i].title for i, _ in dists], [int(movies.iloc[i].movie_id) for i, _ in dists]

def recommend_for_user(watched_ids, top_n=5):
    indices = []
    for mid in watched_ids:
        m = movies[movies["movie_id"] == mid]
        if not m.empty:
            indices.append(m.index[0])
    if not indices:
        return [], []
    blended = np.mean([similarity[i] for i in indices], axis=0)
    ranked  = sorted(enumerate(blended), key=lambda x: x[1], reverse=True)
    titles, ids = [], []
    for i, _ in ranked:
        mid = int(movies.iloc[i].movie_id)
        if mid not in watched_ids:
            titles.append(movies.iloc[i].title)
            ids.append(mid)
        if len(titles) == top_n:
            break
    return titles, ids



# CARD RENDERERS
def _watched_button(movie_id, key_prefix):
    if not st.session_state.logged_in:
        return
    is_watched = movie_id in st.session_state.watched
    label = "✓ Watched" if is_watched else "+ Watched"
    if st.button(label, key=f"wb_{key_prefix}_{movie_id}", use_container_width=True):
        (unmark_watched if is_watched else mark_watched)(st.session_state.username, movie_id)
        st.rerun()

def render_card(title, movie_id, key_prefix):
    """Render a card for a movie from the local pkl (fetches details from TMDB)."""
    d = fetch_movie_details(movie_id)
    if d.get("poster_url"):
        st.image(d["poster_url"], use_container_width=True)
    else:
        st.markdown(
            f'<div class="poster-placeholder"><div class="poster-placeholder-inner">'
            f'{title[0].upper()}</div></div>', unsafe_allow_html=True
        )
    st.markdown(f'<div class="card-title">{title[:31] + "..." if len(title) > 34 else title}</div>',
                unsafe_allow_html=True)
    meta = d.get("year", "")
    if d.get("genres"):
        meta += (" · " if meta else "") + " · ".join(d["genres"])
    if meta:
        st.markdown(f'<div class="card-meta">{meta}</div>', unsafe_allow_html=True)
    if d.get("rating"):
        st.markdown(f'<div class="card-meta card-rating">⭐ {d["rating"]}/10</div>',
                    unsafe_allow_html=True)
    _watched_button(movie_id, key_prefix)

def render_tmdb_card(movie, key_prefix):
    """Render a card for a raw TMDB API result dict."""
    mid    = movie.get("id")
    title  = movie.get("title", "Unknown")
    poster = movie.get("poster_path")
    year   = movie.get("release_date", "")[:4]
    rating = round(movie.get("vote_average", 0), 1)

    if poster:
        st.image(TMDB_POSTER_URL + poster, use_container_width=True)
    else:
        st.markdown(
            f'<div class="poster-placeholder"><div class="poster-placeholder-inner">'
            f'{title[0].upper()}</div></div>', unsafe_allow_html=True
        )
    st.markdown(f'<div class="card-title">{title[:31] + "..." if len(title) > 34 else title}</div>',
                unsafe_allow_html=True)
    if year:
        st.markdown(f'<div class="card-meta">{year}</div>', unsafe_allow_html=True)
    if rating:
        st.markdown(f'<div class="card-meta card-rating">⭐ {rating}/10</div>',
                    unsafe_allow_html=True)
    _watched_button(mid, key_prefix)

def movie_grid(items, key_prefix, is_tmdb=True, cols_per_row=5):
    """Render a list of movies as a responsive grid."""
    for row_start in range(0, len(items), cols_per_row):
        batch = items[row_start:row_start + cols_per_row]
        cols  = st.columns(cols_per_row)
        for col, item in zip(cols, batch):
            with col:
                if is_tmdb:
                    render_tmdb_card(item, key_prefix=f"{key_prefix}_{item['id']}")
                else:
                    title, mid = item
                    render_card(title, mid, key_prefix=f"{key_prefix}_{mid}")
        st.markdown("<br>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# LOGIN / REGISTER PAGE
# ══════════════════════════════════════════════════════════════════════════════
if not st.session_state.logged_in:

    with st.sidebar:
        st.image(logo, use_container_width=True)
        st.markdown(
            "<p style='color:#7777a0;font-size:0.82em;line-height:1.6;margin-top:16px;'>"
            "Sign in to get personalised recommendations based on your watch history."
            "</p>", unsafe_allow_html=True
        )

    st.markdown(
        "<div class='page-title'>SYLVER MOVIES</div>"
        "<div class='page-sub'>CONTENT-BASED MOVIE RECOMMENDER</div>",
        unsafe_allow_html=True
    )
    st.markdown("---")

    _, col, _ = st.columns([1, 1.4, 1])
    with col:
        tab_login, tab_reg = st.tabs(["  Sign In  ", "  Create Account  "])

        with tab_login:
            st.markdown("<br>", unsafe_allow_html=True)
            with st.form("login_form"):
                username  = st.text_input("Username")
                password  = st.text_input("Password", type="password")
                submitted = st.form_submit_button("Sign In", use_container_width=True, type="primary")
                if submitted:
                    result = attempt_login(username, password)
                    if result is not None:
                        st.session_state.logged_in = True
                        st.session_state.username  = _key(username)
                        st.session_state.watched   = result
                        st.rerun()
                    else:
                        st.error("Incorrect username or password.")

        with tab_reg:
            st.markdown("<br>", unsafe_allow_html=True)
            with st.form("register_form"):
                new_user  = st.text_input("Choose a username")
                new_pass  = st.text_input("Choose a password",  type="password")
                confirm   = st.text_input("Confirm password",   type="password")
                submitted = st.form_submit_button("Create Account", use_container_width=True, type="primary")
                if submitted:
                    if new_pass != confirm:
                        st.error("Passwords do not match.")
                    else:
                        ok, msg = attempt_register(new_user, new_pass)
                        if ok:
                            st.success(msg)
                        else:
                            st.error(msg)

    st.stop()


# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR  (shown when logged in)
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.image(logo, use_container_width=True)
    st.markdown("<br>", unsafe_allow_html=True)

    watched_count = len(st.session_state.watched)
    st.markdown(
        f"<div class='user-badge'>"
        f"<div class='user-name'>👤 {st.session_state.username}</div>"
        f"<div class='user-stats'>🎬 {watched_count} movie{'s' if watched_count != 1 else ''} watched</div>"
        f"</div>", unsafe_allow_html=True
    )
    if st.button("Sign Out", use_container_width=True):
        for k in ["logged_in", "username", "watched", "page", "genre_id", "genre_name",
                  "country_code", "country_name"]:
            st.session_state[k] = _defaults[k]
        st.rerun()

    st.markdown("---")
    st.markdown("<p style='color:#333355;font-size:0.72em;letter-spacing:2px;'>METHOD</p>",
                unsafe_allow_html=True)
    st.markdown("<p style='color:#7777a0;font-size:0.82em;'>TF-IDF · Porter Stemming · Cosine Similarity</p>",
                unsafe_allow_html=True)
    st.markdown("<p style='color:#333355;font-size:0.72em;letter-spacing:2px;margin-top:10px;'>DATASET</p>",
                unsafe_allow_html=True)
    st.markdown(f"<p style='color:#7777a0;font-size:0.82em;'>{len(movies):,} movies · TMDB 5000</p>",
                unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# TOP NAVIGATION BAR
# ══════════════════════════════════════════════════════════════════════════════
st.markdown(
    "<div class='navbar-brand'>SYLVER MOVIES</div>"
    "<div class='navbar-sub'>CONTENT-BASED MOVIE RECOMMENDER</div>",
    unsafe_allow_html=True
)

NAV_ITEMS = ["Home", "Popular", "Top Rated", "Genres", "Country", "My Watchlist"]
nav_cols  = st.columns(len(NAV_ITEMS))

for col, item in zip(nav_cols, NAV_ITEMS):
    with col:
        if st.button(item, key=f"nav_{item}", use_container_width=True):
            st.session_state.page         = item
            st.session_state.genre_id     = None
            st.session_state.genre_name   = ""
            st.session_state.country_code = None
            st.session_state.country_name = ""
            st.rerun()
        # Active page underline indicator
        is_active = st.session_state.page == item
        st.markdown(
            f'<div class="{"nav-active-line" if is_active else "nav-inactive-line"}"></div>',
            unsafe_allow_html=True
        )

st.markdown("---")
page = st.session_state.page


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: HOME
# ══════════════════════════════════════════════════════════════════════════════
if page == "Home":

    # For You section
    if st.session_state.watched:
        st.markdown("<div class='section-heading'>For You — Based on Your Watch History</div>",
                    unsafe_allow_html=True)
        per_titles, per_ids = recommend_for_user(st.session_state.watched)
        if per_titles:
            movie_grid(list(zip(per_titles, per_ids)), key_prefix="fy", is_tmdb=False)
        st.markdown("---")

    # Search & recommend
    st.markdown("<div class='section-heading'>Find a Movie</div>", unsafe_allow_html=True)
    selected = st.selectbox(
        "Choose a movie:", movies["title"].values,
        label_visibility="collapsed", placeholder="Search or select a movie..."
    )
    if st.button("Get Recommendations", type="primary"):
        titles, ids = recommend(selected)
        if not titles:
            st.warning("No recommendations found for this movie.")
        else:
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown(
                f"<div class='section-heading'>Because you watched — {selected}</div>",
                unsafe_allow_html=True
            )
            movie_grid(list(zip(titles, ids)), key_prefix="rec", is_tmdb=False)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: POPULAR
# ══════════════════════════════════════════════════════════════════════════════
elif page == "Popular":
    st.markdown("<div class='page-title'>MOST POPULAR</div>"
                "<div class='page-sub'>WHAT EVERYONE IS WATCHING RIGHT NOW</div>",
                unsafe_allow_html=True)

    results = fetch_popular(page=1)
    if results:
        movie_grid(results, key_prefix="pop")
    else:
        st.warning("Could not load popular movies. Check your TMDB API key.")


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: TOP RATED
# ══════════════════════════════════════════════════════════════════════════════
elif page == "Top Rated":
    st.markdown("<div class='page-title'>TOP RATED</div>"
                "<div class='page-sub'>THE HIGHEST RATED FILMS OF ALL TIME</div>",
                unsafe_allow_html=True)

    results = fetch_top_rated(page=1)
    if results:
        movie_grid(results, key_prefix="tr")
    else:
        st.warning("Could not load top rated movies. Check your TMDB API key.")


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: GENRES
# ══════════════════════════════════════════════════════════════════════════════
elif page == "Genres":

    if st.session_state.genre_id is None:
        # Show genre grid
        st.markdown("<div class='page-title'>BROWSE BY GENRE</div>"
                    "<div class='page-sub'>PICK A GENRE TO EXPLORE</div>",
                    unsafe_allow_html=True)

        genres = fetch_genre_list()
        if genres:
            cols = st.columns(4)
            for i, g in enumerate(genres):
                with cols[i % 4]:
                    if st.button(g["name"], key=f"genre_{g['id']}", use_container_width=True):
                        st.session_state.genre_id   = g["id"]
                        st.session_state.genre_name = g["name"]
                        st.rerun()
        else:
            st.warning("Could not load genres.")

    else:
        # Show movies in selected genre
        if st.button("← Back to Genres"):
            st.session_state.genre_id   = None
            st.session_state.genre_name = ""
            st.rerun()

        st.markdown(
            f"<div class='page-title'>{st.session_state.genre_name.upper()}</div>"
            f"<div class='page-sub'>POPULAR {st.session_state.genre_name.upper()} FILMS</div>",
            unsafe_allow_html=True
        )
        results = fetch_by_genre(st.session_state.genre_id)
        if results:
            movie_grid(results, key_prefix=f"g{st.session_state.genre_id}")
        else:
            st.warning("No results found for this genre.")


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: COUNTRY
# ══════════════════════════════════════════════════════════════════════════════
elif page == "Country":

    COUNTRIES = [
        ("🇺🇸", "US",  "United States"),
        ("🇬🇧", "GB",  "United Kingdom"),
        ("🇫🇷", "FR",  "France"),
        ("🇯🇵", "JP",  "Japan"),
        ("🇰🇷", "KR",  "South Korea"),
        ("🇮🇳", "IN",  "India"),
        ("🇩🇪", "DE",  "Germany"),
        ("🇪🇸", "ES",  "Spain"),
        ("🇮🇹", "IT",  "Italy"),
        ("🇨🇳", "CN",  "China"),
        ("🇦🇺", "AU",  "Australia"),
        ("🇲🇽", "MX",  "Mexico"),
    ]

    if st.session_state.country_code is None:
        st.markdown("<div class='page-title'>BROWSE BY COUNTRY</div>"
                    "<div class='page-sub'>EXPLORE CINEMA FROM AROUND THE WORLD</div>",
                    unsafe_allow_html=True)

        cols = st.columns(4)
        for i, (flag, code, name) in enumerate(COUNTRIES):
            with cols[i % 4]:
                if st.button(f"{flag}  {name}", key=f"country_{code}", use_container_width=True):
                    st.session_state.country_code = code
                    st.session_state.country_name = f"{flag} {name}"
                    st.rerun()
    else:
        if st.button("← Back to Countries"):
            st.session_state.country_code = None
            st.session_state.country_name = ""
            st.rerun()

        name_clean = st.session_state.country_name
        st.markdown(
            f"<div class='page-title'>{name_clean}</div>"
            f"<div class='page-sub'>POPULAR FILMS FROM THIS COUNTRY</div>",
            unsafe_allow_html=True
        )
        results = fetch_by_country(st.session_state.country_code)
        if results:
            movie_grid(results, key_prefix=f"c{st.session_state.country_code}")
        else:
            st.warning("No results found for this country.")


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: MY WATCHLIST
# ══════════════════════════════════════════════════════════════════════════════
elif page == "My Watchlist":
    st.markdown("<div class='page-title'>MY WATCHLIST</div>"
                "<div class='page-sub'>MOVIES YOU'VE MARKED AS WATCHED</div>",
                unsafe_allow_html=True)

    watched = st.session_state.watched
    if not watched:
        st.markdown(
            "<div class='empty-state'>"
            "<div class='empty-state-icon'>🎬</div>"
            "You haven't marked any movies as watched yet.<br>"
            "Browse movies and click <b>+ Watched</b> to add them here."
            "</div>", unsafe_allow_html=True
        )
    else:
        # Fetch TMDB details for each watched movie
        watched_items = []
        for mid in watched:
            d = fetch_movie_details(mid)
            watched_items.append({
                "id":            mid,
                "title":         next((movies.iloc[i].title for i in movies[movies["movie_id"] == mid].index), f"Movie #{mid}"),
                "poster_path":   d.get("poster_url", "").replace(TMDB_POSTER_URL, "") if d.get("poster_url") else None,
                "release_date":  d.get("year", "") + "-01-01" if d.get("year") else "",
                "vote_average":  d.get("rating", 0),
            })

        st.markdown(
            f"<p style='color:#7777a0;font-size:0.82em;margin-bottom:20px;'>"
            f"{len(watched)} movie{'s' if len(watched) != 1 else ''} watched</p>",
            unsafe_allow_html=True
        )
        movie_grid(watched_items, key_prefix="wl")