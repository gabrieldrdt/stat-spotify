import streamlit as st
import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from collections import Counter
import requests
from PIL import Image
from io import BytesIO

# Configuration de la page
st.set_page_config(page_title="Stat Spotify", layout="wide")
st.title("🎧 Stat Spotify")

# Lecture des variables d’environnement
SPOTIPY_CLIENT_ID = os.getenv("SPOTIPY_CLIENT_ID")
SPOTIPY_CLIENT_SECRET = os.getenv("SPOTIPY_CLIENT_SECRET")
SPOTIPY_REDIRECT_URI = os.getenv("SPOTIPY_REDIRECT_URI")

# Auth manager
auth_manager = SpotifyOAuth(
    client_id=SPOTIPY_CLIENT_ID,
    client_secret=SPOTIPY_CLIENT_SECRET,
    redirect_uri=SPOTIPY_REDIRECT_URI,
    scope="user-top-read"
)

# Initialiser l'état de session
if "token_info" not in st.session_state:
    st.session_state.token_info = None

# Gérer le retour Spotify (/callback)
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

# Connexion OK → Spotify API
sp = spotipy.Spotify(auth=st.session_state.token_info)
user = sp.current_user()
st.success(f"Connecté : **{user['display_name']}**")

# Sélection de période
range_map = {
    "🎯 Dernier mois (4 semaines)": "short_term",
    "📈 6 derniers mois": "medium_term",
    "📊 1 an ou plus": "long_term"
}
period = st.selectbox("📅 Choisis une période :", options=list(range_map.keys()))
selected_range = range_map[period]

# Récupération des morceaux
top_tracks = sp.current_user_top_tracks(limit=10, time_range=selected_range)

if not top_tracks["items"]:
    st.warning("Aucune donnée disponible pour cette période.")
    st.stop()

# Affichage top morceaux
st.header("🎵 Top morceaux")
albums = []

for i, track in enumerate(top_tracks["items"], 1):
    name = track["name"]
    artist = track["artists"][0]["name"]
    album = track["album"]["name"]
    image_url = track["album"]["images"][0]["url"]
    albums.append(album)

    col1, col2 = st.columns([1, 5])
    with col1:
        try:
            response = requests.get(image_url)
            img = Image.open(BytesIO(response.content))
            st.image(img, width=80)
        except Exception:
            st.write("❌ Cover indisponible")
    with col2:
        st.markdown(f"**{i}. {name}**  \n👤 {artist}  \n💿 {album}")

# Statistiques supplémentaires
st.divider()
st.subheader("📀 Albums les plus présents")
top_albums = Counter(albums).most_common(3)
for i, (album, count) in enumerate(top_albums, 1):
    st.write(f"{i}. {album} ({count} apparition{'s' if count > 1 else ''})")

st.write(f"🎧 Nombre de titres analysés : **{len(top_tracks['items'])}**")
