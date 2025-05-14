import streamlit as st
import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from collections import Counter
import requests
from PIL import Image
from io import BytesIO

st.set_page_config(page_title="Stat Spotify", layout="wide")
st.title("🎧 Stat Spotify (version stabilisée)")

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

if st.button("🚪 Se déconnecter"):
    st.session_state.token_info = None
    st.experimental_rerun()

sp = spotipy.Spotify(auth=st.session_state.token_info)
user = sp.current_user()
st.success(f"Connecté : **{user['display_name']}**")

# Sélection de période
range_map = {
    "🎯 Dernier mois (4 semaines)": "short_term",
    "📈 6 derniers mois": "medium_term",
    "📊 1 an ou plus": "long_term"
}
period = st.selectbox("📅 Choisis une période :", list(range_map.keys()))
selected_range = range_map[period]

# Limite allégée à 30 morceaux
raw_tracks = sp.current_user_top_tracks(limit=50, time_range=selected_range)
if not raw_tracks["items"]:
    st.warning("Aucune donnée disponible.")
    st.stop()

albums = []
seen_keys = set()
track_displayed = 0
MAX_TRACKS = 30

st.header(f"🎧 Morceaux les plus écoutés ({period})")

for track in raw_tracks["items"]:
    if track_displayed >= MAX_TRACKS:
        break

    name = track["name"]
    artist = track["artists"][0]["name"]
    album = track["album"]["name"]
    url = track["external_urls"]["spotify"]
    image_list = track["album"]["images"]

    # doublon ?
    key = f"{name.lower()}::{artist.lower()}"
    if key in seen_keys:
        continue
    seen_keys.add(key)
    albums.append(album)

    # version ?
    version_tag = ""
    if "remix" in name.lower():
        version_tag = "🌀 Remix"
    elif "live" in name.lower():
        version_tag = "🎤 Live"
    elif "version" in name.lower():
        version_tag = "🎧 Version spéciale"

    # cover ?
    image_displayed = False
    if image_list and isinstance(image_list, list) and len(image_list) > 0:
        try:
            response = requests.get(image_list[0]["url"], timeout=5)
            img = Image.open(BytesIO(response.content))
            st.image(img, width=160)
            image_displayed = True
        except Exception:
            st.warning("❌ Cover non disponible")

    if not image_displayed:
        st.write("🖼 Pas de cover valide")

    st.markdown(f"### [{name}]({url}) {'• ' + version_tag if version_tag else ''}")
    st.write(f"👤 {artist}")
    st.write(f"💿 {album}")
    st.markdown("---")
    st.write("")
    st.write("")

    track_displayed += 1

# Top albums
st.subheader("📀 Albums les plus présents")
for i, (album, count) in enumerate(Counter(albums).most_common(3), 1):
    st.write(f"{i}. {album} ({count} fois)")

st.write(f"🎧 Morceaux affichés : **{track_displayed}** (sur {len(raw_tracks['items'])})")
