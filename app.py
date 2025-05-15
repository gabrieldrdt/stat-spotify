import streamlit as st
import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from collections import Counter
import requests
from PIL import Image
from io import BytesIO

st.set_page_config(page_title="Stat Spotify", layout="wide")
st.title("🎧 Stat Spotify (safe mode)")

# Auth Spotify (en variables d’environnement)
SPOTIPY_CLIENT_ID = os.getenv("SPOTIPY_CLIENT_ID")
SPOTIPY_CLIENT_SECRET = os.getenv("SPOTIPY_CLIENT_SECRET")
SPOTIPY_REDIRECT_URI = os.getenv("SPOTIPY_REDIRECT_URI")

# Init session
if "token_info" not in st.session_state:
    st.session_state.token_info = None

query_params = st.query_params

# Authentification Spotify (code reçu)
if "code" in query_params and st.session_state.token_info is None:
    auth_manager = SpotifyOAuth(
        client_id=SPOTIPY_CLIENT_ID,
        client_secret=SPOTIPY_CLIENT_SECRET,
        redirect_uri=SPOTIPY_REDIRECT_URI,
        scope="user-top-read",
        cache_path=None
    )
    try:
        token_info = auth_manager.get_access_token(query_params["code"], as_dict=True)
        if token_info:
            st.session_state.token_info = token_info
            st.rerun()
    except spotipy.exceptions.SpotifyOauthError:
        st.error("⛔ Le code d'autorisation a expiré. Clique à nouveau sur le bouton pour te reconnecter.")
        st.stop()

# Connexion Spotify
if st.session_state.token_info is None:
    if st.button("🔓 Se connecter à Spotify"):
        auth_manager = SpotifyOAuth(
            client_id=SPOTIPY_CLIENT_ID,
            client_secret=SPOTIPY_CLIENT_SECRET,
            redirect_uri=SPOTIPY_REDIRECT_URI,
            scope="user-top-read",
            cache_path=None
        )
        auth_url = auth_manager.get_authorize_url()
        st.markdown(f'<meta http-equiv="refresh" content="0;url={auth_url}">', unsafe_allow_html=True)
    st.stop()

# Déconnexion
if st.button("🚪 Se déconnecter"):
    for k in list(st.session_state.keys()):
        del st.session_state[k]
    st.rerun()

# Client Spotify
token = st.session_state.token_info["access_token"]
sp = spotipy.Spotify(auth=token)

# Tentative récupération de l'utilisateur
try:
    user = sp.current_user()
    st.success(f"Connecté : **{user['display_name']}**")
except spotipy.exceptions.SpotifyException:
    st.error("❌ Erreur : l'utilisateur n'est pas autorisé à accéder à l'API Spotify (403).")
    st.stop()

# Choix période
range_map = {
    "🎯 Dernier mois": "short_term",
    "📈 6 mois": "medium_term",
    "📊 1 an": "long_term"
}
period = st.selectbox("📅 Période :", list(range_map.keys()))
selected_range = range_map[period]

if "last_period" not in st.session_state or st.session_state.last_period != selected_range:
    st.session_state.last_period = selected_range
    st.session_state.page_index = 0

# Récupération des titres
raw_tracks = sp.current_user_top_tracks(limit=50, time_range=selected_range)
if not raw_tracks["items"]:
    st.warning("Aucune donnée disponible.")
    st.stop()

# Nettoyage
unique = {}
albums = []

for track in raw_tracks["items"]:
    try:
        name = track["name"]
        artist = track["artists"][0]["name"]
        album = track["album"]["name"]
        url = track["external_urls"]["spotify"]
        images = track["album"]["images"]

        if not images or not url:
            continue

        key = f"{name.lower()}::{artist.lower()}"
        if key not in unique:
            unique[key] = track
            albums.append(album)
    except Exception:
        continue

tracks = list(unique.values())
total = len(tracks)

# Pagination
per_page = 10
start = st.session_state.page_index * per_page
end = start + per_page
visible = tracks[start:end]

st.header(f"🎵 Morceaux écoutés ({period})")

for i, track in enumerate(visible, start + 1):
    try:
        name = track["name"]
        artist = track["artists"][0]["name"]
        album = track["album"]["name"]
        url = track["external_urls"]["spotify"]
        image_url = track["album"]["images"][0]["url"]

        response = requests.get(image_url, timeout=4)
        img = Image.open(BytesIO(response.content))
        st.image(img, width=150)

        version_tag = ""
        lowered = name.lower()
        if "remix" in lowered:
            version_tag = "🌀 Remix"
        elif "live" in lowered:
            version_tag = "🎤 Live"
        elif "version" in lowered:
            version_tag = "🎧 Version spéciale"

        st.markdown(f"### {i}. [{name}]({url}) {'• ' + version_tag if version_tag else ''}")
        st.write(f"👤 {artist}")
        st.write(f"💿 {album}")
        st.markdown("---")
    except Exception:
        continue

# Pagination boutons optimisés
col1, col2, col3 = st.columns([1, 1, 2])
with col1:
    if st.session_state.page_index > 0 and st.button("⬅ Page précédente"):
        st.session_state.page_index -= 1
        st.rerun()
with col2:
    if end < total and st.button("➡ Page suivante"):
        st.session_state.page_index += 1
        st.rerun()
with col3:
    st.markdown(f"Page **{st.session_state.page_index + 1}** / {((total - 1) // per_page) + 1}")

# Albums
st.subheader("📀 Albums les plus présents")
for i, (album, count) in enumerate(Counter(albums).most_common(3), 1):
    st.write(f"{i}. {album} ({count} fois)")

st.write(f"🎧 Total morceaux valides : **{len(tracks)}**")
