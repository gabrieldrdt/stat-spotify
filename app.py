import streamlit as st
import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth

# Config de la page Streamlit
st.set_page_config(page_title="Spotify Stats", layout="centered")
st.title("🎧 Mes Stats Spotify")

# Lire les variables d’environnement depuis Render
SPOTIPY_CLIENT_ID = os.getenv("SPOTIPY_CLIENT_ID")
SPOTIPY_CLIENT_SECRET = os.getenv("SPOTIPY_CLIENT_SECRET")
SPOTIPY_REDIRECT_URI = os.getenv("SPOTIPY_REDIRECT_URI")

# DEBUG : afficher ce que ton app lit
st.write("🧠 redirect_uri utilisée :", SPOTIPY_REDIRECT_URI)
st.write("🧠 client_id utilisé :", SPOTIPY_CLIENT_ID)

# Vérifie que toutes les variables sont bien définies
if not SPOTIPY_CLIENT_ID or not SPOTIPY_CLIENT_SECRET or not SPOTIPY_REDIRECT_URI:
    st.error("❌ Erreur : certaines variables d’environnement sont manquantes.")
    st.stop()

# Initialisation de la session
if "token_info" not in st.session_state:
    st.session_state.token_info = None

# Création du gestionnaire d'authentification Spotify
auth_manager = SpotifyOAuth(
    client_id=SPOTIPY_CLIENT_ID,
    client_secret=SPOTIPY_CLIENT_SECRET,
    redirect_uri=SPOTIPY_REDIRECT_URI,
    scope="user-top-read"
)

# Si l’utilisateur n’est pas encore connecté
if st.session_state.token_info is None:
    st.write("Connecte-toi pour voir tes stats 👇")

    # Générer l’URL d’autorisation Spotify
    auth_url = auth_manager.get_authorize_url()

    # Afficher le lien cliquable
    st.markdown(f"[🔓 Se connecter à Spotify]({auth_url})", unsafe_allow_html=True)

    # DEBUG : afficher l’URL brute
    st.write("🔗 Lien direct d’auth Spotify :", auth_url)

    # Vérifier si un token est déjà dispo dans le cache
    token_info = auth_manager.get_cached_token()
    if token_info:
        st.session_state.token_info = token_info
        st.rerun()

# Si déjà connecté à Spotify
else:
    try:
        sp = spotipy.Spotify(auth_manager=auth_manager)
        user = sp.current_user()
        st.success(f"✅ Connecté en tant que : {user['display_name']}")

        st.subheader("🎵 Tes 10 titres les plus écoutés récemment :")
        top_tracks = sp.current_user_top_tracks(limit=10)

        for i, track in enumerate(top_tracks['items'], 1):
            name = track['name']
            artist = track['artists'][0]['name']
            st.write(f"{i}. {name} – {artist}")

    except Exception as e:
        st.error("❌ Erreur lors de la récupération des données Spotify :")
        st.exception(e)
