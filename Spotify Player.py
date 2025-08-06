# Progetto_Stabile/spotify_player_controls.py
import logging
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import config

logger = logging.getLogger("SpotifyPlayerControls")

# --- Autenticazione (viene creato solo il gestore, non l'oggetto spotify) ---
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
    logger.info("Gestore autenticazione Spotify (Player Controls) inizializzato.")
except Exception as e:
    logger.error(f"!!! ERRORE CRITICO INIZIALIZZAZIONE AUTH MANAGER SPOTIFY!!!: {e}")
    auth_manager = None

# --- TOOL: PLAY/RESUME ---
async def resume_playback():
    """Riprende la riproduzione corrente su Spotify."""
    logger.info("TOOL ESEGUITO: resume_playback")
    if not auth_manager:
        return {"status": "error", "message": "Spotify non configurato."}
    try:
        spotify = spotipy.Spotify(auth_manager=auth_manager)
        spotify.start_playback()
        logger.info("✅ COMANDO INVIATO: Riproduzione ripresa.")
        return {"status": "success", "message": "Musica ripresa."}
    except spotipy.exceptions.SpotifyException as e:
        logger.error(f"Errore durante il comando di ripresa: {e.reason}")
        if e.reason == 'NO_ACTIVE_DEVICE':
            return {"status": "error", "message": "Non trovo un dispositivo attivo su cui riprendere, mozzo!"}
        return {"status": "error", "message": "Problema con Spotify."}
    except Exception as e:
        logger.error(f"Errore imprevisto in resume_playback: {e}", exc_info=True)
        return {"status": "error", "message": "Qualcosa è andato storto."}


# --- TOOL: PAUSA ---
async def pause_playback():
    """Mette in pausa la riproduzione corrente su Spotify."""
    logger.info("TOOL ESEGUITO: pause_playback")
    if not auth_manager:
        return {"status": "error", "message": "Spotify non configurato."}
    try:
        spotify = spotipy.Spotify(auth_manager=auth_manager)
        spotify.pause_playback()
        logger.info("✅ COMANDO INVIATO: Riproduzione messa in pausa.")
        return {"status": "success", "message": "Ok, ho messo in pausa la musica."}
    except spotipy.exceptions.SpotifyException as e:
        logger.error(f"Errore durante il comando di pausa: {e.reason}")
        if e.reason == 'NO_ACTIVE_DEVICE':
            return {"status": "success", "message": "Non c'è musica da mettere in pausa, mozzo!"}
        return {"status": "error", "message": "Problema con Spotify."}
    except Exception as e:
        logger.error(f"Errore imprevisto in pause_playback: {e}", exc_info=True)
        return {"status": "error", "message": "Qualcosa è andato storto."}

# --- TOOL: VOLUME ---
async def _change_volume(increment: int):
    """Funzione helper per modificare il volume."""
    if not auth_manager:
        return {"status": "error", "message": "Spotify non configurato."}
    try:
        spotify = spotipy.Spotify(auth_manager=auth_manager)
        playback = spotify.current_playback()
        if not playback or not playback.get('device'):
            return {"status": "success", "message": "Non c'è niente in riproduzione, quindi non posso regolare il volume."}

        current_volume = playback['device']['volume_percent']
        new_volume = max(0, min(100, current_volume + increment))

        spotify.volume(new_volume)
        logger.info(f"✅ COMANDO INVIATO: Volume impostato a {new_volume}%.")
        return {"status": "success", "message": f"Fatto! Volume impostato al {new_volume}%."}
    except spotipy.exceptions.SpotifyException as e:
        logger.error(f"Errore durante la modifica del volume: {e.reason}")
        return {"status": "error", "message": "Problema con Spotify durante la regolazione del volume."}
    except Exception as e:
        logger.error(f"Errore imprevisto in _change_volume: {e}", exc_info=True)
        return {"status": "error", "message": "Qualcosa è andato storto."}

async def volume_up():
    """Aumenta il volume di Spotify del 30%."""
    logger.info("TOOL ESEGUITO: volume_up")
    return await _change_volume(30)

async def volume_down():
    """Diminuisce il volume di Spotify del 30%."""
    logger.info("TOOL ESEGUITO: volume_down")
    return await _change_volume(-30)

# --- TOOL: SKIP AVANTI E INDIETRO ---
async def next_track():
    """Salta alla traccia successiva su Spotify."""
    logger.info("TOOL ESEGUITO: next_track")
    if not auth_manager:
        return {"status": "error", "message": "Spotify non configurato."}
    try:
        spotify = spotipy.Spotify(auth_manager=auth_manager)
        spotify.next_track()
        logger.info("✅ COMANDO INVIATO: Saltato alla traccia successiva.")
        return {"status": "success", "message": "Aye aye! Canzone successiva!"}
    except spotipy.exceptions.SpotifyException as e:
        logger.error(f"Errore durante lo skip avanti: {e.reason}")
        if e.reason == 'NO_ACTIVE_DEVICE':
            return {"status": "success", "message": "Non c'è niente in riproduzione da saltare, mozzo!"}
        return {"status": "error", "message": "Problema con Spotify."}
    except Exception as e:
        logger.error(f"Errore imprevisto in next_track: {e}", exc_info=True)
        return {"status": "error", "message": "Qualcosa è andato storto."}

async def previous_track():
    """
    Torna alla traccia precedente su Spotify.
    Esegue il comando due volte per garantire il salto alla traccia precedente
    invece di riavviare semplicemente quella corrente.
    """
    logger.info("TOOL ESEGUITO: previous_track (con doppio comando)")
    if not auth_manager:
        return {"status": "error", "message": "Spotify non configurato."}
    try:
        spotify = spotipy.Spotify(auth_manager=auth_manager)
        # Esegui il comando due volte per forzare il salto alla traccia precedente
        spotify.previous_track()
        spotify.previous_track()
        logger.info("✅ COMANDO INVIATO: Tornato alla traccia precedente (doppio tocco).")
        return {"status": "success", "message": "Subito! Torniamo a quella di prima."}
    except spotipy.exceptions.SpotifyException as e:
        logger.error(f"Errore durante lo skip indietro: {e.reason}")
        if e.reason == 'NO_ACTIVE_DEVICE':
            return {"status": "success", "message": "Non posso tornare indietro se non stiamo andando da nessuna parte, mozzo!"}
        return {"status": "error", "message": "Problema con Spotify."}
    except Exception as e:
        logger.error(f"Errore imprevisto in previous_track: {e}", exc_info=True)
        return {"status": "error", "message": "Qualcosa è andato storto."}

# --- TOOL: RICONOSCI CANZONE ---
async def get_current_song():
    """Recupera la canzone e l'artista attualmente in riproduzione su Spotify."""
    logger.info("TOOL ESEGUITO: get_current_song (con refresh forzato)")
    if not auth_manager:
        return {"status": "error", "message": "Spotify non configurato."}
    try:
        # **LA MODIFICA CHIAVE È QUI**
        # Creiamo un'istanza "fresca" di Spotify ogni volta per evitare la cache.
        spotify = spotipy.Spotify(auth_manager=auth_manager)

        playback = spotify.current_playback()
        if playback and playback.get('item'): # Rimosso is_playing per avere info anche in pausa
            track_name = playback['item']['name']
            artist_name = playback['item']['artists'][0]['name']
            logger.info(f"✅ Canzone corrente recuperata: '{track_name}' di {artist_name}.")
            status_riproduzione = "in riproduzione" if playback['is_playing'] else "in pausa"
            # RISPOSTA ASSERTIVA (come da raccomandazione ElevenLabs)
            return {
                "status": "CURRENT_STATE_UPDATE",
                "message": "SISTEMA: Lo stato della riproduzione è cambiato. Le informazioni precedenti sono obsolete.",
                "current_song": track_name,
                "current_artist": artist_name,
                "playback_status": status_riproduzione,
                "override_context": True
            }
        else:
            logger.info("Nessuna canzone attualmente in riproduzione o in coda.")
            return {"status": "success", "message": "Al momento non c'è nessuna canzone in riproduzione, mozzo."}
    except spotipy.exceptions.SpotifyException as e:
        logger.error(f"Errore durante il recupero della canzone corrente: {e.reason}")
        return {"status": "error", "message": "Problema con Spotify."}
    except Exception as e:
        logger.error(f"Errore imprevisto in get_current_song: {e}", exc_info=True)
        return {"status": "error", "message": "Qualcosa è andato storto."}
omar@Omar:~/ProgettoBotte/ProgettoModulare_Funzionante/Progetto_Stabile$
