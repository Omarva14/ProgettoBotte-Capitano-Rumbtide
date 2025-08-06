# Progetto_Stabile/agent.py
import asyncio
import base64
import json
import logging
import threading

import numpy as np
import sounddevice as sd
import websockets
from websockets.exceptions import ConnectionClosed

# Importa i nuovi moduli
import config
import spotify_tools
import spotify_player_controls

# --- CONFIGURAZIONE ---
# Ora leggiamo la configurazione dal file config.py
ELEVEN_API_KEY = config.ELEVEN_API_KEY
ELEVEN_AGENT_ID = config.ELEVEN_AGENT_ID

INPUT_DEVICE_INDEX = None
OUTPUT_DEVICE_INDEX = 1

API_INPUT_RATE = 16000
TTS_OUTPUT_RATE = 24000

# --- Parametri Tecnici ---
WEBSOCKET_URL = (
    f"wss://api.elevenlabs.io/v1/convai/conversation"
    f"?agent_id={ELEVEN_AGENT_ID}"
    f"&output_format=pcm_{TTS_OUTPUT_RATE}"
    f"&enable_visemes=true"
)
RECONNECT_DELAY = 5

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)-15s - %(levelname)-8s - %(message)s')
logger = logging.getLogger("Agent")


class AudioPlayer:
    # ... (Classe AudioPlayer invariata) ...
    def __init__(self):
        self._queue = asyncio.Queue()
        self._play_task = None
        self.stop_event = threading.Event()

    def add_chunk(self, chunk):
        self._queue.put_nowait(chunk)

    async def _play_audio(self):
        loop = asyncio.get_event_loop()
        try:
            with sd.OutputStream(samplerate=TTS_OUTPUT_RATE, channels=1, dtype='int16', device=OUTPUT_DEVICE_INDEX) as stream:
                logger.info(f"Stream di output avviato su dispositivo {stream.device} a {stream.samplerate}Hz.")
                while not self.stop_event.is_set():
                    chunk = await self._queue.get()
                    if chunk is None: break
                    await loop.run_in_executor(None, stream.write, np.frombuffer(chunk, dtype=np.int16))
        except Exception as e:
            logger.error(f"Errore critico nello stream di output: {e}", exc_info=True)
        finally:
            logger.info("Stream di output audio fermato.")

    def start(self):
        self.stop_event.clear()
        self._play_task = asyncio.get_event_loop().create_task(self._play_audio())

    def stop(self):
        self.stop_event.set()
        if self._play_task: self._play_task.cancel()

    def interrupt(self):
        while not self._queue.empty(): self._queue.get_nowait()


class ConversationalAgent:
    def __init__(self):
        self.audio_player = AudioPlayer()
        self.stop_flag = asyncio.Event()
        self.user_can_speak = asyncio.Event()
        self.user_can_speak.set()
        logger.info("Agente conversazionale stabile inizializzato.")

    async def _microphone_handler(self, websocket):
        # ... (Funzione _microphone_handler invariata) ...
        loop = asyncio.get_event_loop()
        audio_queue = asyncio.Queue()

        def audio_callback(indata, frames, time, status):
            if status: logger.warning(f"Errore stream microfono: {status}")
            if self.user_can_speak.is_set():
                loop.call_soon_threadsafe(audio_queue.put_nowait, indata.copy())

        with sd.InputStream(samplerate=API_INPUT_RATE, device=INPUT_DEVICE_INDEX, channels=1, dtype='int16', callback=audio_callback):
            logger.info(f"Avvio stream di input dal dispositivo di default a {API_INPUT_RATE}Hz.")
            while not self.stop_flag.is_set():
                await self.user_can_speak.wait()
                audio_data_np = await audio_queue.get()
                audio_bytes = audio_data_np.tobytes()
                encoded_data = base64.b64encode(audio_bytes).decode('utf-8')
                await websocket.send(json.dumps({ "user_audio_chunk": encoded_data }))


    async def _message_handler(self, websocket):
        async for message_str in websocket:
            message = json.loads(message_str)
            msg_type = message.get("type")

            if msg_type == "audio":
                if not self.audio_player._play_task: self.audio_player.start()
                self.audio_player.add_chunk(base64.b64decode(message["audio_event"]["audio_base_64"]))

            elif msg_type == "user_transcript":
                transcript = message['user_transcription_event']['user_transcript']
                if transcript: logger.info(f"🗣️  Trascrizione: '{transcript}'")

            elif msg_type == "agent_response_start":
                logger.info("L'agente sta per parlare, microfono in pausa.")
                self.user_can_speak.clear()
                self.audio_player.interrupt()

            elif msg_type == "agent_response":
                logger.info(f"🤖 Risposta: '{message['agent_response_event']['agent_response'].strip()}'")
                self.user_can_speak.set()
                logger.info(">> Turno dell'utente. Microfono attivo.")

            # --- NUOVA LOGICA PER LA GESTIONE DEI TOOL ---
            elif msg_type == "client_tool_call":
                logger.info("🛠️  Agente richiede esecuzione di un tool. Microfono in pausa.")
                self.user_can_speak.clear()
                await self.handle_tool_call(websocket, message.get('client_tool_call', {}))

            elif msg_type == "ping":
                await websocket.send(json.dumps({"type": "pong", "event_id": message["ping_event"]["event_id"]}))

    async def handle_tool_call(self, websocket, tool_call_data):
        tool_name = tool_call_data.get('tool_name')
        parameters = tool_call_data.get('parameters', {})
        tool_call_id = tool_call_data.get('tool_call_id')

        logger.info(f"Esecuzione tool '{tool_name}' con parametri: {parameters}")

        tool_result = {"status": "error", "message": f"Tool '{tool_name}' non trovato."}

        # Cerca il tool prima nei controlli del player, poi negli strumenti di ricerca
        tool_function = None
        if hasattr(spotify_player_controls, tool_name):
            tool_function = getattr(spotify_player_controls, tool_name)
        elif hasattr(spotify_tools, tool_name):
            tool_function = getattr(spotify_tools, tool_name)

        if tool_function:
            try:
                # Esegui la funzione del tool
                tool_result = await tool_function(**parameters)
            except Exception as e:
                logger.error(f"Errore durante l'esecuzione del tool '{tool_name}': {e}", exc_info=True)
                tool_result = {"status": "error", "message": str(e)}
        else:
            logger.warning(f"Tentativo di chiamare un tool non definito: '{tool_name}'")

        # Invia il risultato al server
        response_msg = {
            "type": "client_tool_response",
            "client_tool_response": {
                "tool_call_id": tool_call_id,
                "result": json.dumps(tool_result),
                "is_error": tool_result.get("status") not in ["success", "CURRENT_STATE_UPDATE"]
            }
        }
        await websocket.send(json.dumps(response_msg))
        logger.info(f"Risultato del tool '{tool_name}' inviato al server: {json.dumps(tool_result)}")


        # Riattiva il microfono dopo l'esecuzione del tool
        self.user_can_speak.set()
        logger.info(">> Turno dell'utente. Microfono riattivato dopo esecuzione tool.")

    async def _run_session(self):
        # ... (Funzione _run_session invariata) ...
        headers = {"xi-api-key": ELEVEN_API_KEY}
        while not self.stop_flag.is_set():
            try:
                logger.info("Tentativo di connessione a ElevenLabs...")
                async with websockets.connect(WEBSOCKET_URL, extra_headers=headers) as websocket:
                    logger.info("✅ Connessione stabilita. In attesa di audio...")
                    tasks = [
                        asyncio.create_task(self._microphone_handler(websocket)),
                        asyncio.create_task(self._message_handler(websocket)),
                    ]
                    done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
                    for task in pending: task.cancel()

            except ConnectionClosed as e:
                logger.warning(f"Connessione chiusa ({e.code}). Riconnessione tra {RECONNECT_DELAY}s.")
            except Exception as e:
                logger.error(f"Errore imprevisto: {e}. Riconnessione tra {RECONNECT_DELAY}s.", exc_info=True)

            if not self.stop_flag.is_set(): await asyncio.sleep(RECONNECT_DELAY)

    async def start(self):
        self.stop_flag.clear()
        try: await self._run_session()
        except asyncio.CancelledError: logger.info("Task principale cancellato.")

    def stop(self):
        logger.info("🛑 Richiesta di arresto...")
        self.stop_flag.set()
        self.audio_player.stop()
