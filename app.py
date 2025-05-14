import streamlit as st
import os
import webbrowser
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyOAuth

st.set_page_config(page_title="Stats Spotify", layout="centered")
st.title("🎧 Mes Stats Spotify")

# Charger les variables d'environnement
load_dotenv()

# Initialiser l'état si besoin
if "token_info" not in st.session_state:
    st.session_state.token_info = None

# Fonction de création d'auth manager
def get_auth_manager():
    return SpotifyOAuth(scope="user-top-read")

# Si l'utilisateur n'est pas connecté
if st.session_state.token_info is None:
    st.write("Connecte-toi pour voir tes stats 👇")
    if st.button("🔓 Se connecter à Spotify"):
        try:
            auth_manager = get_auth_manager()
            auth_url = auth_manager.get_authorize_url()
            webbrowser.open(auth_url)  # 🔥 Force l’ouverture de la page Spotify
            st.info("👉 Une fenêtre s’est ouverte. Connecte-toi à Spotify, puis reviens ici.")
        except Exception as e:
            st.error("❌ Erreur de connexion à Spotify :")
            st.exception(e)

    # Attendre que le token soit en cache
    if get_auth_manager().get_cached_token():
        st.session_state.token_info = get_auth_manager().get_cached_token()
        st.rerun()

# Si connecté
else:
    st.success("✅ Connecté à Spotify !")
    try:
        sp = spotipy.Spotify(auth_manager=get_auth_manager())
        user = sp.current_user()
        st.write(f"Bienvenue **{user['display_name']}** 👋")

        top_tracks = sp.current_user_top_tracks(limit=10, time_range='short_term')
        st.subheader("🎵 Tes 10 titres les plus écoutés récemment :")

        for i, track in enumerate(top_tracks['items'], start=1):
            st.write(f"{i}. {track['name']} - {track['artists'][0]['name']}")

    except Exception as e:
        st.error("Erreur lors de la récupération des données Spotify :")
        st.exception(e)
