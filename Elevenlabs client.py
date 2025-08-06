# Progetto_Stabile/elevenlabs_client.py

import asyncio
import json
import time
import websockets
from typing import Optional

from config import ELEVEN_API_KEY, AUDIO_CONFIG, VAD_THRESHOLD, BARGE_IN_ENABLED
from audio_manager import AudioManager

ELEVENLABS_WS_URI = "wss://api.elevenlabs.io/v1/convai/conversation"

class ElevenLabsClient:
    def __init__(self, agent_id: str, audio_manager: AudioManager, voice_id: Optional[str] = None):
        self.agent_id = agent_id
        self.voice_id = voice_id
        self.audio_manager = audio_manager
        self.websocket: Optional[websockets.WebSocketClientProtocol] = None

        # Stato per la gestione del barge-in
        self.last_user_activity = 0.0
        self.is_interrupted = False

    async def connect_dashboard_style(self):
        print("Tentativo di connessione a ElevenLabs...")
        headers = {
            "xi-api-key": ELEVEN_API_KEY,
            "User-Agent": "ElevenLabs-Dashboard-Replica/1.0"
        }

        try:
            self.websocket = await websockets.connect(
                ELEVENLABS_WS_URI, extra_headers=headers
            )
            print("✅ Connessione WebSocket stabilita.")

            conversation_initiation_data = {
                "type": "conversation_initiation_client_data",
                "agent_id": self.agent_id,
                "user_config": {"language_code": "it-IT"},
                "audio_config": {
                    "input_sample_rate": AUDIO_CONFIG['input_sample_rate'],
                    "output_sample_rate": AUDIO_CONFIG['output_sample_rate'],
                    "input_encoding": AUDIO_CONFIG['format'],
                    "output_encoding": "ulaw"
                }
            }

            if self.voice_id:
                conversation_initiation_data["user_config"]["voice_id"] = self.voice_id

            await self.websocket.send(json.dumps(conversation_initiation_data))
            print("📤 Messaggio di inizializzazione inviato.")

        except Exception as e:
            print(f"❌ Errore durante la connessione: {e}")

    async def handle_messages(self):
        if not self.websocket:
            print("Errore: la connessione WebSocket non è attiva.")
            return

        print("👂 In ascolto dei messaggi dal server...")
        try:
            async for message in self.websocket:
                try:
                    data = json.loads(message)
                    event_type = data.get("type")

                    if event_type == "conversation_initiation_metadata":
                        print("🎉 Ricevuto evento: METADATI CONVERSAZIONE")

                    elif event_type == "vad_score":
                        await self.process_vad_dashboard_style(data.get("score", 0.0))

                    elif event_type == "agent_response_correction":
                        print("🔄 Ricevuto evento: CORREZIONE RISPOSTA AGENTE")
                        await self.handle_dashboard_interruption()

                    elif event_type == "agent_response":
                        if self.is_interrupted:
                            print("🤖 Risposta agente ignorata a causa di interruzione.")
                            continue

                        print("🤖 Ricevuto evento: RISPOSTA AGENTE")
                        if "audio" in data:
                            await self.audio_manager.queue_audio_chunk(data["audio"])

                    else:
                        print(f"❓ Ricevuto evento non gestito: {event_type}")

                except json.JSONDecodeError:
                    print(f"⚠️ Messaggio non JSON ricevuto: {message[:100]}...")

        except websockets.exceptions.ConnectionClosed as e:
            print(f"🔌 Connessione WebSocket chiusa: {e.code} {e.reason}")
        except Exception as e:
            print(f"Errore irreversibile nel gestore messaggi: {e}")

    async def process_vad_dashboard_style(self, vad_score: float):
        """
        Processa il punteggio VAD. Se l'utente sta parlando mentre l'agente
        è in riproduzione, attiva il barge-in.
        """
        if self.audio_manager.is_playing and BARGE_IN_ENABLED:
            if vad_score > VAD_THRESHOLD:
                print(f"VAD score ({vad_score:.2f}) > soglia ({VAD_THRESHOLD}). Utente sta parlando.")
                self.last_user_activity = time.time()
                await self.prepare_barge_in()
            else:
                # Se l'utente smette di parlare, resetta il flag di interruzione
                if self.is_interrupted:
                    self.is_interrupted = False
                    print("Utente ha smesso di parlare, interruzione resettata.")

    async def prepare_barge_in(self):
        """
        Prepara l'interruzione (barge-in) fermando la riproduzione audio
        e impostando il flag di interruzione.
        """
        if not self.is_interrupted:
            print("⚡️ INTERRUZIONE! L'utente sta parlando sopra l'agente.")
            self.is_interrupted = True
            await self.audio_manager.stop_playback()
            await self.audio_manager.clear_audio_queue()

    async def handle_dashboard_interruption(self):
        """
        Gestisce il reset dopo che un'interruzione è stata completamente
        processata (es. ricevendo agent_response_correction).
        """
        print(" resettando lo stato dopo l'interruzione.")
        await self.audio_manager.stop_playback()
        await self.audio_manager.clear_audio_queue()
        self.is_interrupted = False # Resetta il flag
        # Ri-avvia il loop di playback, sarà in attesa di nuovi chunk
        self.audio_manager.start_playback()

    async def close(self):
        if self.websocket and self.websocket.open:
            await self.websocket.close()
            print("🔌 Connessione WebSocket chiusa.")
