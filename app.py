import streamlit as st
import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from collections import Counter
import requests
from PIL import Image
from io import BytesIO

# ⚙️ Config
st.set_page_config(page_title="Stat Spotify", layout="wide")
st.title("🎧 Stat Spotify")

# 🔐 Auth Spotify
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

# 🔁 Callback
query_params = st.query_params
if "code" in query_params and st.session_state.token_info is None:
    code = query_params["code"]
    token_info = auth_manager.get_access_token(code, as_dict=False)
    if token_info:
        st.session_state.token_info = token_info
        st.rerun()

# 🔓 Connexion
if st.session_state.token_info is None:
    if st.button("🔓 Se connecter à Spotify"):
        auth_url = auth_manager.get_authorize_url()
        st.markdown(f'<meta http-equiv="refresh" content="0;url={auth_url}">', unsafe_allow_html=True)
    st.stop()

# 🚪 Déconnexion
if st.button("🚪 Se déconnecter"):
    st.session_state.token_info = None
    st.experimental_rerun()

# ✅ Connecté
sp = spotipy.Spotify(auth=st.session_state.token_info)
user = sp.current_user()
st.success(f"Connecté : **{user['display_name']}**")

# ⏳ Sélection période
range_map = {
    "🎯 Dernier mois (4 semaines)": "short_term",
    "📈 6 derniers mois": "medium_term",
    "📊 1 an ou plus": "long_term"
}
period = st.selectbox("📅 Choisis une période :", list(range_map.keys()))
selected_range = range_map[period]

# 🎵 Récupération des morceaux
raw_tracks = sp.current_user_top_tracks(limit=50, time_range=selected_range)
if not raw_tracks["items"]:
    st.warning("Aucune donnée disponible.")
    st.stop()

# 🔁 Suppression des doublons
unique_tracks = {}
for track in raw_tracks["items"]:
    name = track["name"]
    artist = track["artists"][0]["name"]
    key = f"{name.lower()}::{artist.lower()}"
    if key not in unique_tracks:
        unique_tracks[key] = track

# 🎧 Affichage
st.header("🎵 Tes morceaux les plus écoutés")
albums = []

for i, track in enumerate(unique_tracks.values(), 1):
    name = track["name"]
    artist = track["artists"][0]["name"]
    album = track["album"]["name"]
    url = track["external_urls"]["spotify"]
    image_url = track["album"]["images"][0]["url"]
    albums.append(album)

    version_tag = ""
    lowered = name.lower()
    if "remix" in lowered:
        version_tag = "🌀 Remix"
    elif "live" in lowered:
        version_tag = "🎤 Live"
    elif "version" in lowered:
        version_tag = "🎧 Version spéciale"

    # 💡 Affichage simple et robuste
    st.markdown(f"### {i}. [{name}]({url}) {'• ' + version_tag if version_tag else ''}")
    try:
        img = Image.open(BytesIO(requests.get(image_url).content))
        st.image(img, width=150)
    except Exception:
        st.write("❌ Pas de cover")
    st.write(f"👤 {artist}  \n💿 {album}")
    st.divider()

# 📀 Statistiques albums
st.subheader("📀 Albums les plus présents")
top_albums = Counter(albums).most_common(3)
for i, (album, count) in enumerate(top_albums, 1):
    st.write(f"{i}. {album} ({count} apparition{'s' if count > 1 else ''})")

st.write(f"🎧 Titres uniques analysés : **{len(unique_tracks)}**")
