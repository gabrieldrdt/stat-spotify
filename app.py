import streamlit as st
import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from collections import Counter
import requests
from PIL import Image
from io import BytesIO

st.set_page_config(page_title="Stat Spotify", layout="wide")
st.title("🎧 Stat Spotify (pagination réelle)")

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

query_params = st.query_params
if "code" in query_params and st.session_state.token_info is None:
    code = query_params["code"]
    token_info = auth_manager.get_access_token(code, as_dict=False)
    if token_info:
        st.session_state.token_info = token_info
        st.rerun()

if st.session_state.token_info is None:
    if st.button("🔓 Se connecter à Spotify"):
        auth_url = auth_manager.get_authorize_url()
        st.markdown(f'<meta http-equiv="refresh" content="0;url={auth_url}">', unsafe_allow_html=True)
    st.stop()

# Déconnexion propre
logout = st.button("🚪 Se déconnecter")
if logout:
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

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
    st.session_state.page_index = 0

# Récupération brute
raw_tracks = sp.current_user_top_tracks(limit=50, time_range=selected_range)
if not raw_tracks["items"]:
    st.warning("Aucune donnée disponible.")
    st.stop()

# Nettoyage des doublons
unique = {}
albums = []

for track in raw_tracks["items"]:
    name = track["name"]
    artist = track["artists"][0]["name"]
    key = f"{name.lower()}::{artist.lower()}"
    if key not in unique:
        unique[key] = track
        albums.append(track["album"]["name"])

tracks = list(unique.values())
total = len(tracks)

# Pagination réelle
per_page = 10
start = st.session_state.page_index * per_page
end = start + per_page
visible_tracks = tracks[start:end]

st.header(f"🎧 Morceaux les plus écoutés ({period})")

for i, track in enumerate(visible_tracks, start + 1):
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
            img = Image.open(BytesIO(requests.get(images[0]["url"], timeout=5).content))
            st.image(img, width=150)
        except Exception:
            st.write("❌ Cover non dispo")
    else:
        st.write("🖼 Pas de cover")

    st.markdown(f"### {i}. [{name}]({url}) {'• ' + version_tag if version_tag else ''}")
    st.write(f"👤 {artist}")
    st.write(f"💿 {album}")
    st.markdown("---")

# Navigation entre les pages
col1, col2, col3 = st.columns([1, 1, 2])
with col1:
    if st.session_state.page_index > 0:
        if st.button("⬅ Page précédente"):
            st.session_state.page_index -= 1
            st.rerun()
with col2:
    if end < total:
        if st.button("➡ Page suivante"):
            st.session_state.page_index += 1
            st.rerun()
with col3:
    st.markdown(f"Page **{st.session_state.page_index + 1}** / {((total - 1) // per_page) + 1}")

# Albums les plus fréquents
st.subheader("📀 Albums les plus présents")
for i, (album, count) in enumerate(Counter(albums).most_common(3), 1):
    st.write(f"{i}. {album} ({count} fois)")

st.write(f"🎧 Morceaux uniques trouvés : **{total}**")
