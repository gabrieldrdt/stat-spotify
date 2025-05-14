import streamlit as st
import os
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyOAuth

# Configuration Streamlit
st.set_page_config(page_title="Spotify Stats", layout="centered")
st.title("🎧 Mes Stats Spotify")

# Charger les variables d'environnement
load_dotenv()

# Initialisation de l'état de session
if "token_info" not in st.session_state:
    st.session_state.token_info = None

# Configuration de l'auth Spotify
def get_auth_manager():
    return SpotifyOAuth(scope="user-top-read")

auth_manager = get_auth_manager()

# Si l'utilisateur n'est pas encore connecté
if st.session_state.token_info is None:
    st.write("Connecte-toi pour voir tes stats 👇")

    # Génération du lien d'authentification
    auth_url = auth_manager.get_authorize_url()

    # Lien cliquable
    st.markdown(f"[🔓 Se connecter à Spotify]({auth_url})", unsafe_allow_html=True)

    # Lien brut affiché en dessous pour test manuel
    st.write("🔗 Lien direct Spotify :", auth_url)

    # Si l'utilisateur a validé l'auth et le token est stocké
    token_info = auth_manager.get_cached_token()
    if token_info:
        st.session_state.token_info = token_info
        st.rerun()

# Si l'utilisateur est connecté
else:
    try:
        sp = spotipy.Spotify(auth_manager=auth_manager)
        user = sp.current_user()
        st.success(f"✅ Connecté à Spotify : **{user['display_name']}**")

        st.subheader("🎵 Tes 10 titres les plus écoutés récemment :")

        top_tracks = sp.current_user_top_tracks(limit=10)

        for i, track in enumerate(top_tracks['items'], 1):
            name = track['name']
            artist = track['artists'][0]['name']
            st.write(f"{i}. {name} – {artist}")

    except Exception as e:
        st.error("❌ Erreur lors de la récupération des données Spotify :")
        st.exception(e)
