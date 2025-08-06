import logging
import threading
import time
from spotify_client import get_spotify_client
from background_music_manager import music_manager

logger = logging.getLogger("SpotifyWatcher")

class SpotifyWatcher:
    def __init__(self, check_interval=1):
        self.spotify = get_spotify_client()
        self.interval = check_interval
        self.stop_event = threading.Event()
        self.watcher_thread = None
        self.is_spotify_playing = False

    def _watcher_loop(self):
        """Il ciclo principale che controlla lo stato di Spotify."""
        logger.info("Il 'Guardiano' di Spotify è attivo.")
        while not self.stop_event.is_set():
            try:
                # Controlliamo lo stato solo se il client Spotify è valido
                if self.spotify:
                    current_playback = self.spotify.current_playback()
                    # Spotify è considerato 'attivo' se c'è una sessione di riproduzione, anche se in pausa
                    if current_playback and current_playback.get('is_playing'):
                        if not self.is_spotify_playing:
                            logger.info("Il Guardiano ha rilevato che Spotify ha iniziato a suonare.")
                            self.is_spotify_playing = True
                            if music_manager:
                                music_manager.pause()
                    else:
                        if self.is_spotify_playing:
                            logger.info("Il Guardiano ha rilevato che Spotify ha smesso di suonare.")
                            self.is_spotify_playing = False
                            if music_manager:
                                music_manager.resume()

                else:
                    logger.warning("Il client Spotify non è disponibile per il Guardiano.")

            except Exception as e:
                # Gestiamo gli errori di rete senza bloccare il guardiano
                logger.error(f"Errore nel Guardiano di Spotify: {e}", exc_info=False)
                # Se c'è un errore (es. rete), consideriamo Spotify non in riproduzione
                if self.is_spotify_playing:
                    self.is_spotify_playing = False
                    if music_manager:
                        music_manager.resume()

            # Aspettiamo per l'intervallo specificato prima del prossimo controllo
            time.sleep(self.interval)

        logger.info("Il 'Guardiano' di Spotify è stato fermato.")


    def start(self):
        """Avvia il thread del guardiano."""
        if not self.watcher_thread or not self.watcher_thread.is_alive():
            self.stop_event.clear()
            self.watcher_thread = threading.Thread(target=self._watcher_loop, daemon=True)
            self.watcher_thread.start()
            logger.info("Thread del Guardiano di Spotify avviato.")

    def stop(self):
        """Ferma il thread del guardiano."""
        logger.info("Richiesta di arresto per il Guardiano di Spotify.")
        self.stop_event.set()
        if self.watcher_thread:
            self.watcher_thread.join(timeout=self.interval + 1) # Aspetta che il thread termini
            if self.watcher_thread.is_alive():
                logger.warning("Il thread del Guardiano non si è fermato correttamente.")

# Creiamo un'istanza unica che verrà usata in tutto il progetto
try:
    spotify_watcher = SpotifyWatcher()
except Exception as e:
    logger.error(f"Impossibile creare l'istanza di SpotifyWatcher: {e}")
    spotify_watcher = None
