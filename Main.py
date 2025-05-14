import os
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyOAuth

# Charger les variables d'environnement depuis le fichier .env
load_dotenv()

# Authentification avec Spotify
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    scope="user-top-read"
))

# Récupérer les 20 morceaux les plus écoutés sur le court terme
top_tracks = sp.current_user_top_tracks(limit=20, time_range='short_term')

# Afficher les résultats dans la console
print("\n🎧 Top 20 morceaux (court terme) :\n")
for i, track in enumerate(top_tracks['items']):
    name = track['name']
    artist = track['artists'][0]['name']
    print(f"{i + 1}. {name} - {artist}")
