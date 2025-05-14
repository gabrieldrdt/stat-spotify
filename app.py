import streamlit as st
import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from collections import Counter
import requests
from PIL import Image
from io import BytesIO

# Config
st.set_page_config(page_title="Stat Spotify", layout="wide")
st.title("🎧 Stat Spotify (pagination)")

# Auth Spotify
SPOTIPY_CLIENT_ID = os.getenv("SPOTIPY_CLIENT_ID")
SPOTIPY_CLIENT_SECRET = os.getenv("SPOTIPY_CLIENT_SECRET")
SPOTIPY_REDIRECT_URI = os.getenv("SPOTIPY_REDIRECT_URI")

auth_manager = SpotifyOAuth(
    client_id=SPOTIPY_CLIENT_ID,
    client_secret=SPOTIPY_CLIENT_SECRET,
    redirect_uri=SPOTIPY_REDIRECT_URI,
    scope="user-top-read"
)

if "token_info" not in st.session_state:
    st.session_state.token_info = None

# Callback Spotify
query_params = st.query_params
if "code" in query_params and st.session_state.token_info is None:
    code = query_params["code"]
    token_info = auth_manager.get_access_token(code, as_dict=False)
    if token_info:
        st.session_state.token_info = token_info
        st.rerun()

# Connexion
if st.session_state.token_info is None:
    if st.button("🔓 Se connecter à Spotify"):
        auth_url = auth_manager.get_authorize_url()
        st.markdown(f'<meta http-equiv="refresh" content="0;url={auth_url}">', unsafe_allow_html=True)
    st.stop()

# Déconnexion
if st.button("🚪 Se déconnecter"):
    st.session_state.token_info = None
    st.experimental_rerun()

sp = spotipy.Spotify(auth=st.session_state.token_info)
user = sp.current_user()
st.success(f"Connecté : **{user['display_name']}**")

# Choix de période
range_map = {
    "🎯 Dernier mois (4 semaines)": "short_term",
    "📈 6 derniers mois": "medium_term",
    "📊 1 an ou plus": "long_term"
}
period = st.selectbox("📅 Choisis une période :", list(range_map.keys()))
selected_range = range_map[period]

# Reset pagination si période changée
if "last_period" not in st.session_state or st.session_state.last_period != selected_range:
    st.session_state.last_period = selected_range
    st.session_state.tracks_shown = 10

# Récupération des morceaux
raw_tracks = sp.current_user_top_tracks(limit=50, time_range=selected_range)
if not raw_tracks["items"]:
    st.warning("Aucune donnée disponible.")
    st.stop()

albums = []
seen_keys = set()
tracks = []

# Nettoyage des doublons
for track in raw_tracks["items"]:
    name = track["name"]
    artist = track["artists"][0]["name"]
    key = f"{name.lower()}::{artist.lower()}"
    if key not in seen_keys:
        seen_keys.add(key)
        tracks.append(track)
        albums.append(track["album"]["name"])

# Affichage avec pagination
st.header(f"🎧 Morceaux les plus écoutés ({period})")

to_display = tracks[:st.session_state.tracks_shown]

for i, track in enumerate(to_display, 1):
    name = track["name"]
    artist = track["artists"][0]["name"]
    album = track["album"]["name"]
    url = track["external_urls"]["spotify"]
    images = track["album"]["images"]

    version_tag = ""
    if "remix" in name.lower():
        version_tag = "🌀 Remix"
    elif "live" in name.lower():
        version_tag = "🎤 Live"
    elif "version" in name.lower():
        version_tag = "🎧 Version spéciale"

    if images:
        try:
            response = requests.get(images[0]["url"], timeout=5)
            img = Image.open(BytesIO(response.content))
            st.image(img, width=150)
        except Exception:
            st.write("❌ Cover non dispo")
    else:
        st.write("🖼 Pas de cover")

    st.markdown(f"### {i}. [{name}]({url}) {'• ' + version_tag if version_tag else ''}")
    st.write(f"👤 {artist}")
    st.write(f"💿 {album}")
    st.markdown("---")

# Bouton pour afficher plus
if st.session_state.tracks_shown < len(tracks):
    if st.button("🔽 Afficher plus de morceaux"):
        st.session_state.tracks_shown += 10
        st.experimental_rerun()

# Stat albums
st.subheader("📀 Albums les plus présents")
for i, (album, count) in enumerate(Counter(albums).most_common(3), 1):
    st.write(f"{i}. {album} ({count} fois)")

st.write(f"🎧 Morceaux affichés : {min(st.session_state.tracks_shown, len(tracks))}/{len(tracks)}")
