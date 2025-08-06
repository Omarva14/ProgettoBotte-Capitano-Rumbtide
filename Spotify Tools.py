# Progetto_Stabile/spotify_tools.py
import logging
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from openai import OpenAI
import config
import re

logger = logging.getLogger("SpotifyTools")

# --- Autenticazione ---
try:
    SCOPE = "user-modify-playback-state user-read-playback-state playlist-read-private"
    auth_manager = SpotifyOAuth(
        client_id=config.SPOTIPY_CLIENT_ID,
        client_secret=config.SPOTIPY_CLIENT_SECRET,
        redirect_uri="http://127.0.0.1:8888/callback",
        scope=SCOPE,
        open_browser=False,
        cache_path=config.SPOTIFY_CACHE_PATH
    )
    spotify = spotipy.Spotify(auth_manager=auth_manager)
    spotify.current_user()
    logger.info("Autenticazione Spotify OAuth completata.")
except Exception as e:
    logger.error(f"!!! ERRORE CRITICO AUTENTICAZIONE SPOTIFY !!!: {e}")
    spotify = None

try:
    openai_client = OpenAI(api_key=config.OPENAI_API_KEY)
except Exception as e:
    logger.error(f"Errore inizializzazione OpenAI: {e}")
    openai_client = None

# --- NUOVA FUNZIONE: Pulizia della risposta di GPT ---
def _clean_gpt_response(response_text: str) -> str:
    """
    Pulisce la risposta di GPT per estrarre solo la query di ricerca,
    rimuovendo frasi di cortesia e formattazione markdown.
    """
    # Rimuove blocchi di codice markdown
    cleaned_text = re.sub(r"```[\w\s]*\n", "", response_text)
    cleaned_text = cleaned_text.replace("```", "")

    # Rimuove frasi comuni e virgolette
    phrases_to_remove = [
        "Certo! Ecco una query di ricerca concisa per Spotify:",
        "Ecco una query di ricerca per Spotify:",
        "Query di ricerca:",
        '"'
    ]
    for phrase in phrases_to_remove:
        cleaned_text = cleaned_text.replace(phrase, "")

    return cleaned_text.strip()

# --- Funzione helper: Trova e "sveglia" il dispositivo target ---
def _get_target_device_id():
    # ... (invariata)
    if not spotify: return None
    if not config.SPOTIFY_DEVICE_NAME or config.SPOTIFY_DEVICE_NAME == "...":
        logger.warning("Nome del dispositivo Spotify non configurato.")
        return None
    devices = spotify.devices()
    if not devices or not devices['devices']:
        logger.error("Nessun dispositivo Spotify trovato.")
        return None
    target_device_name = config.SPOTIFY_DEVICE_NAME.lower()
    for device in devices['devices']:
        if device['name'].lower() == target_device_name:
            device_id = device['id']
            logger.info(f"Dispositivo target '{device['name']}' trovato con ID: {device_id}")
            return device_id
    logger.warning(f"Dispositivo '{config.SPOTIFY_DEVICE_NAME}' non trovato. Disponibili: {[d['name'] for d in devices['devices']]}")
    return None

# --- Funzione helper aggiornata per la ricerca e riproduzione ---
def _search_and_play_track(query: str):
    # ... (invariata)
    if not spotify:
        return {"status": "error", "message": "Spotify non configurato."}
    try:
        target_device_id = _get_target_device_id()
        results = spotify.search(q=query, type='track', limit=1)
        tracks = results.get('tracks', {}).get('items', [])
        if not tracks:
            return {"status": "error", "message": f"Non ho trovato nulla per '{query}'."}
        top_track = tracks[0]
        track_name = top_track['name']
        artist_name = top_track['artists'][0]['name']
        track_uri = top_track['uri']
        logger.info(f"Traccia trovata: '{track_name}' di '{artist_name}'")
        if not target_device_id:
            return {"status": "error", "message": "Non trovo un dispositivo Spotify attivo su cui riprodurre."}

        try:
            spotify.start_playback(uris=[track_uri], device_id=target_device_id)
            logger.info(f"✅ COMANDO INVIATO: Riproduzione di '{track_name}' su dispositivo ID {target_device_id}.")
            return {"status": "success", "message": f"Perfetto, ho messo in play '{track_name}' di '{artist_name}'.", "track_uri": track_uri}
        except spotipy.exceptions.SpotifyException as e:
            logger.error(f"Errore durante la riproduzione: {e.reason}")
            return {"status": "error", "message": "Spotify ha rifiutato il comando. Assicurati di avere un account Premium."}
    except Exception as e:
        logger.error(f"Errore durante la ricerca: {e}", exc_info=True)
        return {"status": "error", "message": "Si è verificato un problema con Spotify."}


# --- TOOL 1: Ricerca Diretta (LOGICA DI PULIZIA AGGIUNTA) ---
async def play_song_by_title_and_artist(song_title: str, artist: str = None):
    logger.info(f"TOOL: play_song_by_title_and_artist, titolo='{song_title}', artista='{artist}'")
    if not openai_client: return {"status": "error", "message": "OpenAI non configurato."}

    artist_info = f"dell'artista '{artist}'" if artist else "dell'artista più probabile o famoso (anche se storpiato)"
    # --- PROMPT MIGLIORATO ---
    prompt = (
        f"Crea una query di ricerca per Spotify per la canzone '{song_title}' {artist_info}. Correggi eventuali errori nel nome dell'artista. "
        "La tua risposta DEVE contenere solo e unicamente il titolo e l'artista corretti, senza frasi di cortesia, spiegazioni o formattazione markdown."
    )

    try:
        response = openai_client.chat.completions.create(model="gpt-4o", messages=[{"role": "system", "content": "Sei un esperto di musica che ottimizza query per Spotify."}, {"role": "user", "content": prompt}], temperature=0.0)
        gpt_response = response.choices[0].message.content
        optimized_query = _clean_gpt_response(gpt_response) # <-- USA LA FUNZIONE DI PULIZIA
        logger.info(f"Query ottimizzata e pulita: '{optimized_query}'")
    except Exception as e:
        logger.error(f"Errore OpenAI: {e}. Uso la query originale.")
        optimized_query = f"{song_title} {artist}" if artist else song_title

    return _search_and_play_track(optimized_query)

# --- TOOL 2: Ricerca Descrittiva (LOGICA DI PULIZIA AGGIUNTA) ---
async def find_song_by_description(description: str):
    logger.info(f"TOOL: find_song_by_description, descrizione='{description}'")
    if not openai_client: return {"status": "error", "message": "OpenAI non configurato."}

    # --- PROMPT MIGLIORATO ---
    prompt = (
        "Analizza la seguente descrizione per identificare una canzone. Estrai il titolo esatto e l'artista originale. "
        "Se si riferisce a un film, cerca la colonna sonora principale ('main theme'). "
        "La tua risposta DEVE essere solo nel formato `Titolo: [titolo], Artista: [artista]`, senza frasi di cortesia o spiegazioni."
        f"\n\nDescrizione: \"{description}\""
    )

    try:
        response = openai_client.chat.completions.create(model="gpt-4o", messages=[{"role": "system", "content": "Sei un esperto di musica che identifica canzoni da descrizioni."}, {"role": "user", "content": prompt}], temperature=0.0)
        extracted_info = response.choices[0].message.content
        logger.info(f"Informazioni estratte da GPT: '{extracted_info}'")

        title_match = re.search(r"Titolo: (.+?),", extracted_info)
        artist_match = re.search(r"Artista: (.+)", extracted_info)

        if not title_match or not artist_match:
            logger.warning("GPT non ha restituito il formato atteso. Tento una ricerca generica.")
            return _search_and_play_track(description)

        extracted_title = title_match.group(1).strip()
        extracted_artist = artist_match.group(1).strip()
        search_query = f"{extracted_title} {extracted_artist}"
        logger.info(f"Query di ricerca costruita: '{search_query}'")
    except Exception as e:
        logger.error(f"Errore OpenAI: {e}. Uso la descrizione originale.")
        search_query = description

    return _search_and_play_track(search_query)


# --- TOOL 3: Riproduci Playlist per Nome ---
async def play_playlist_by_name(playlist_name: str):
    """
    Cerca una playlist dell'utente per nome e la mette in riproduzione.
    """
    logger.info(f"TOOL: play_playlist_by_name, nome playlist='{playlist_name}'")
    if not spotify:
        return {"status": "error", "message": "Spotify non configurato."}

    try:
        # Recupera tutte le playlist dell'utente loggato
        playlists = spotify.current_user_playlists()

        target_playlist = None
        # Cerca la playlist per nome (case-insensitive)
        for playlist in playlists['items']:
            if playlist['name'].lower() == playlist_name.lower():
                target_playlist = playlist
                break

        if not target_playlist:
            logger.warning(f"Playlist '{playlist_name}' non trovata nelle playlist dell'utente.")
            return {"status": "error", "message": f"Non ho trovato una playlist chiamata '{playlist_name}' nel tuo forziere, mozzo. Sei sicuro del nome?"}

        playlist_uri = target_playlist['uri']
        playlist_name_found = target_playlist['name']
        logger.info(f"Playlist trovata: '{playlist_name_found}' con URI: {playlist_uri}")

        target_device_id = _get_target_device_id()
        if not target_device_id:
            return {"status": "error", "message": "Non trovo un dispositivo Spotify attivo su cui riprodurre."}

        # Avvia la riproduzione della playlist
        spotify.start_playback(context_uri=playlist_uri, device_id=target_device_id)

        logger.info(f"✅ COMANDO INVIATO: Riproduzione della playlist '{playlist_name_found}' avviata.")
        return {"status": "success", "message": f"Perfetto, ho messo in play la playlist '{playlist_name_found}'. All'arrembaggio!"}

    except spotipy.exceptions.SpotifyException as e:
        logger.error(f"Errore Spotify durante la riproduzione della playlist: {e.reason}")
        return {"status": "error", "message": "Ho avuto un problema con Spotify mentre cercavo di avviare la tua playlist."}
    except Exception as e:
        logger.error(f"Errore imprevisto in play_playlist_by_name: {e}", exc_info=True)
        return {"status": "error", "message": "Qualcosa è andato storto, capitano."}


# --- TOOL 4: Riproduci Classifica (APPROCCIO TRAMITE PLAYLIST PUBBLICHE) ---
async def play_top_charts(playlist_name: str = "Hit Del Momento 2025", owner_name: str = "peermusic"):
    """
    Approccio di fallback: Cerca una playlist pubblica di alta qualità per nome
    (es. "Hit Del Momento 2025" di "peermusic"), e tenta di riprodurne le tracce.
    Questo evita il blocco delle playlist editoriali di Spotify.
    """
    logger.info(f"TOOL (Ricerca Fallback): Avvio ricerca per playlist '{playlist_name}' di '{owner_name}'.")
    if not spotify:
        return {"status": "error", "message": "Spotify non configurato."}

    target_device_id = _get_target_device_id()
    if not target_device_id:
        return {"status": "error", "message": "Non trovo un dispositivo Spotify attivo su cui riprodurre."}

    try:
        # 1. Cerca la playlist per nome
        results = spotify.search(q=playlist_name, type="playlist", limit=10)

        if not results or not results['playlists']['items']:
            logger.warning(f"Nessuna playlist trovata con il nome '{playlist_name}'.")
            return {"status": "error", "message": f"Non ho trovato nessuna playlist chiamata '{playlist_name}'."}

        # 2. Filtra per trovare quella del proprietario specificato
        target_playlist = None
        for playlist in results['playlists']['items']:
            if not playlist:
                continue

            if 'owner' in playlist and playlist.get('owner') and playlist['owner']['display_name'] == owner_name:
                target_playlist = playlist
                break

        if not target_playlist:
            logger.warning(f"Trovate playlist chiamate '{playlist_name}', ma nessuna è di '{owner_name}'.")
            return {"status": "error", "message": f"Non ho trovato la classifica '{playlist_name}' di '{owner_name}'."}

        playlist_id = target_playlist['id']
        found_name = target_playlist['name']
        logger.info(f"Trovata playlist target: '{found_name}' (ID: {playlist_id})")

        # 3. Tenta di leggere le tracce
        logger.info(f"Tento di leggere le tracce dalla playlist ID: {playlist_id}...")
        tracks_response = spotify.playlist_tracks(playlist_id, limit=10, fields='items(track(uri))')

        if not tracks_response or not tracks_response['items']:
             logger.warning(f"La playlist '{found_name}' sembra essere vuota o illeggibile.")
             return {"status": "error", "message": f"La classifica '{found_name}' è vuota o non sono riuscito a leggerla."}

        track_uris = [item['track']['uri'] for item in tracks_response['items'] if item.get('track')]
        if not track_uris:
            logger.warning(f"Nessuna traccia valida trovata nella playlist '{found_name}'.")
            return {"status": "error", "message": "Non ho trovato canzoni valide nella classifica."}

        # 4. Avvia la riproduzione
        spotify.start_playback(uris=track_uris, device_id=target_device_id)

        logger.info(f"✅ COMANDO INVIATO: Riproduzione delle top 10 da '{found_name}' avviata.")
        return {"status": "success", "message": f"Perfetto! Ecco le canzoni da '{found_name}'."}

    except spotipy.exceptions.SpotifyException as e:
        logger.error(f"Errore Spotify: {e.reason} (Status: {e.http_status})")
        if e.http_status in [403, 404]:
             return {"status": "error", "message": "Anche questa playlist è bloccata. Incredibile."}
        return {"status": "error", "message": "Ho avuto un problema con Spotify mentre cercavo la playlist."}
    except Exception as e:
        logger.error(f"Errore imprevisto in play_top_charts: {e}", exc_info=True)
        return {"status": "error", "message": "Qualcosa è andato storto, capitano."}

