import streamlit as st
import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from urllib.parse import urlparse, parse_qs

# Config Streamlit
st.set_page_config(page_title="Spotify Stats", layout="centered")
st.title("🎧 Mes Stats Spotify")

# Variables d'environnement Render
SPOTIPY_CLIENT_ID = os.getenv("SPOTIPY_CLIENT_ID")
SPOTIPY_CLIENT_SECRET = os.getenv("SPOTIPY_CLIENT_SECRET")
SPOTIPY_REDIRECT_URI = os.getenv("SPOTIPY_REDIRECT_URI")

if not all([SPOTIPY_CLIENT_ID, SPOTIPY_CLIENT_SECRET, SPOTIPY_REDIRECT_URI]):
    st.error("❌ Variables d'environnement manquantes")
    st.stop()

# Gérer l'état
if "token_info" not in st.session_state:
    st.session_state.token_info = None

auth_manager = SpotifyOAuth(
    client_id=SPOTIPY_CLIENT_ID,
    client_secret=SPOTIPY_CLIENT_SECRET,
    redirect_uri=SPOTIPY_REDIRECT_URI,
    scope="user-top-read"
)

# 🔁 Gérer le retour de Spotify (/callback?code=...)
query_params = st.experimental_get_query_params()
if "code" in query_params:
    code = query_params["code"][0]
    token_info = auth_manager.get_access_token(code, as_dict=False)
    if token_info:
        st.session_state.token_info = token_info
        st.experimental_rerun()

# 🔓 Si pas encore connecté
if st.session_state.token_info is None:
    auth_url = auth_manager.get_authorize_url()
    st.markdown(f"[🔓 Se connecter à Spotify]({auth_url})", unsafe_allow_html=True)
    st.stop()

# ✅ Si connecté → afficher les données Spotify
sp = spotipy.Spotify(auth=st.session_state.token_info)
user = sp.current_user()
st.success(f"✅ Connecté : {user['display_name']}")

st.subheader("🎵 Tes 10 titres les plus écoutés récemment :")
top_tracks = sp.current_user_top_tracks(limit=10)

for i, track in enumerate(top_tracks["items"], 1):
    name = track["name"]
    artist = track["artists"][0]["name"]
    st.write(f"{i}. {name} – {artist}")
