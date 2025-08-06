# Progetto_Stabile/spotify_client.py
import logging
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import config

logger = logging.getLogger("SpotifyClient")

spotify_instance = None
try:
    SCOPE = "user-modify-playback-state user-read-playback-state user-read-currently-playing playlist-read-private"
    auth_manager = SpotifyOAuth(
        client_id=config.SPOTIPY_CLIENT_ID,
        client_secret=config.SPOTIPY_CLIENT_SECRET,
        redirect_uri="http://127.0.0.1:8888/callback",
        scope=SCOPE,
        open_browser=False,
        cache_path=config.SPOTIFY_CACHE_PATH
    )
    spotify_instance = spotipy.Spotify(auth_manager=auth_manager)
    # Eseguiamo una chiamata leggera per forzare l'autenticazione all'avvio
    spotify_instance.current_user()
    logger.info("✅ Cliente Spotify Unificato inizializzato e autenticato con successo.")

except Exception as e:
    logger.error(f"!!! ERRORE CRITICO NELL'INIZIALIZZAZIONE DEL CLIENTE SPOTIFY UNIFICATO !!!: {e}")
    spotify_instance = None

def get_spotify_client():
    """
    Restituisce l'istanza unica e autenticata del client Spotify.
    """
    return spotify_instance
