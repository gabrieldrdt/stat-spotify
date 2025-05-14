import streamlit as st
import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from collections import Counter
import requests
from PIL import Image
from io import BytesIO

st.set_page_config(page_title="Stat Spotify", layout="wide")
st.title("🎧 Stat Spotify - Debug")

# Auth config
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

range_map = {
    "🎯 Dernier mois (4 semaines)": "short_term",
    "📈 6 derniers mois": "medium_term",
    "📊 1 an ou plus": "long_term"
}
period = st.selectbox("📅 Choisis une période :", list(range_map.keys()))
selected_range = range_map[period]

raw_tracks = sp.current_user_top_tracks(limit=50, time_range=selected_range)
if not raw_tracks["items"]:
    st.warning("Aucune donnée disponible.")
    st.stop()

# Debug : affichage simple + espacé + stable
albums = []
seen_keys = set()

st.header(f"🎧 Analyse pour : {period}")
for i, track in enumerate(raw_tracks["items"], 1):
    name = track["name"]
    artist = track["artists"][0]["name"]
    album = track["album"]["name"]
    url = track["external_urls"]["spotify"]
    image_url = track["album"]["images"][0]["url"]

    # éviter doublons
    key = f"{name.lower()}::{artist.lower()}"
    if key in seen_keys:
        continue
    seen_keys.add(key)
    albums.append(album)

    # Version spéciale ?
    version_tag = ""
    if "remix" in name.lower():
        version_tag = "🌀 Remix"
    elif "live" in name.lower():
        version_tag = "🎤 Live"
    elif "version" in name.lower():
        version_tag = "🎧 Version spéciale"

    # Affichage sécurisé
    try:
        response = requests.get(image_url)
        img = Image.open(BytesIO(response.content))
        st.image(img, width=180)
    except Exception:
        st.write("❌ Pas de cover")

    st.markdown(f"**{i}. [{name}]({url})** {'• ' + version_tag if version_tag else ''}")
    st.write(f"👤 {artist}")
    st.write(f"💿 {album}")
    st.markdown(f"🔗 Lien brut : {url}")
    st.markdown(f"📁 Image URL : {image_url}")
    st.markdown(f"🧪 ID cache : {track['id']}")
    st.markdown("---")
    st.write("")  # espacement
    st.write("")  # double espace

# Albums stats
st.subheader("📀 Albums les plus présents")
from collections import Counter
for i, (album, count) in enumerate(Counter(albums).most_common(3), 1):
    st.write(f"{i}. {album} ({count} fois)")

st.write(f"🎧 Nombre de morceaux uniques affichés : **{len(seen_keys)}**")
