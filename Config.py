# Progetto_Stabile/config.py

# --- Chiavi API ElevenLabs ---
# Le teniamo qui per coerenza, anche se agent.py le ha hardcodate
ELEVEN_API_KEY = "sk_758bf839aaéééébc571cc5aa"
ELEVEN_AGENT_ID = "agent_94*******tf6"

# --- Chiavi API OpenAI ---
# PER FAVORE, INSERISCI LA TUA CHIAVE API DI OPENAI QUI
OPENAI_API_KEY = "sk-proj-m4****

# --- Credenziali API Spotify ---
# PER FAVORE, INSERISCI LE TUE CREDENZIALI DALLA DASHBOARD SPOTIFY DEVELOPER
SPOTIPY_CLIENT_ID = "5d33d****
SPOTIPY_CLIENT_SECRET = "d98220d1***"

# --- Nome del Dispositivo Spotify Target ---
# Inserisci qui il nome esatto del dispositivo su cui vuoi che la musica venga riprodotta
# (es. "Web Player", "Il mio PC", "Echo Dot di Omar").
# Lo trovi nell'elenco dei dispositivi di Spotify.
SPOTIFY_DEVICE_NAME = "iPhone"

# --- Percorso per la Cache di Autenticazione Spotify ---
# Questo file memorizza il token di accesso per evitare di dover fare il login ogni volta.
# Lo impostiamo esplicitamente per assicurarci che sia sempre trovato.
SPOTIFY_CACHE_PATH = ".spotify_cache"

# Questo non è necessario per il flusso 'client_credentials'
# SPOTIPY_REDIRECT_URI = "http://localhost:**
