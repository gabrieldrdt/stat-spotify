import streamlit as st
import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from collections import Counter
from PIL import Image
import requests
from io import BytesIO

# Configuration Streamlit
st.set_page_config(page_title="Stat Spotify", layout="centered")
st.title("🎧 Bienvenue sur Stat Spotify")

# Récupération des variables Render
SPOTIPY_CLIENT_ID = os.getenv("SPOTIPY_CLIENT_ID")
SPOTIPY_CLIENT_SECRET = os.getenv("SPOTIPY_CLIENT_SECRET")
SPOTIPY_REDIRECT_URI = os.getenv("SPOTIPY_REDIRECT_URI")

# Auth Spotify
auth_manager = SpotifyOAuth(
    client_id=SPOTIPY_CLIENT_ID,
    client_secret=SPOTIPY_CLIENT_SECRET,
    redirect_uri=SPOTIPY_REDIRECT_URI,
    scope="user-top-read"
)

# Initialisation de session
if "token_info" not in st.session_state:
    st.session_state.token_info = None

# 🔁 Gérer le retour de Spotify (callback)
query_params = st.query_params
if "code" in query_params and st.session_state.token_info is None:
    code = query_params["code"]
    token_info = auth_manager.get_access_token(code, as_dict=False)
    if token_info:
        st.session_state.token_info = token_info
        st.rerun()

# 🔓 Pas encore connecté
if st.session_state.token_info is None:
    st.info("Connecte-toi pour voir tes stats Spotify :")
    if st.button("🔓 Se connecter à Spotify"):
        auth_url = auth_manager.get_authorize_url()
        st.markdown(f'<meta http-equiv="refresh" content="0;url={auth_url}">', unsafe_allow_html=True)
    st.stop()

# 🔴 Déconnexion
if st.button("🚪 Se déconnecter"):
    st.session_state.token_info = None
    st.experimental_rerun()

# ✅ Connecté → affichage
sp = spotipy.Spotify(auth=st.session_state.token_info)
user = sp.current_user()
st.success(f"🎉 Connecté : **{user['display_name']}**")

# Choix de la période
time_range = st.selectbox(
    "Choisis la période :",
    options=["4 dernières semaines", "6 derniers mois", "Année passée"],
    index=0
)

range_map = {
    "4 dernières semaines": "short_term",
    "6 derniers mois": "medium_term",
    "Année passée": "long_term"
}

selected_range = range_map[time_range]

# Récupération des données
top_tracks = sp.current_user_top_tracks(limit=20, time_range=selected_range)

st.header("🎵 Top morceaux")

albums = []
for i, track in enumerate(top_tracks["items"], 1):
    name = track["name"]
    artist = track["artists"][0]["name"]
    album = track["album"]["name"]
    albums.append(album)

    image_url = track["album"]["images"][0]["url"]
    response = requests.get(image_url)
    image = Image.open(BytesIO(response.content))

    with st.container():
        cols = st.columns([1, 4])
        with cols[0]:
            st.image(image, width=80)
        with cols[1]:
            st.markdown(f"**{i}. {name}**  \n👤 {artist}  \n💿 {album}")

# Affichage des stats supplémentaires
st.divider()
st.header("📊 Statistiques supplémentaires")

# Top albums
album_counts = Counter(albums)
top_albums = album_counts.most_common(3)

st.subheader("🏆 Top albums")
for i, (album, count) in enumerate(top_albums, 1):
    st.write(f"{i}. {album} ({count} apparitions)")

# Nombre total de morceaux
total_tracks = len(top_tracks["items"])
st.write(f"🎧 Nombre total de morceaux analysés : **{total_tracks}**")

# Suggestion future : top artistes, genres, etc.
