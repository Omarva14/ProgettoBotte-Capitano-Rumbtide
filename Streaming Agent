# Progetto_Stabile/streaming_agent.py

import asyncio
import queue
import sounddevice as sd
import numpy as np
from scipy.signal import resample
import threading
import time

from elevenlabs.client import ElevenLabs

from config import ELEVEN_API_KEY, AUDIO_CONFIG

# --- Costanti Audio ---
INPUT_SAMPLE_RATE = AUDIO_CONFIG['input_sample_rate']
OUTPUT_SAMPLE_RATE = AUDIO_CONFIG['output_sample_rate']
INPUT_CHANNELS = AUDIO_CONFIG['channels']
SILENCE_THRESHOLD_RMS = 0.01
SILENCE_DURATION_S = 1.0

class StreamingAgent:
    def __init__(self):
        print("🚀 Inizializzazione di StreamingAgent...")
        if not ELEVEN_API_KEY: raise ValueError("ELEVEN_API_KEY non trovato")
        self.client = ElevenLabs(api_key=ELEVEN_API_KEY)

        self.is_user_speaking = False
        self.is_agent_speaking = False
        self.conversation_active = True

        try:
            sd.check_input_settings()
            sd.check_output_settings()
            self.input_device = sd.default.device[0]
            self.output_device = sd.default.device[1]
            self.device_sample_rate = int(sd.query_devices(self.input_device)['default_samplerate'])
            print(f"✅ Microfono di default: {sd.query_devices(self.input_device)['name']}")
            print(f"✅ Output di default: {sd.query_devices(self.output_device)['name']}")
        except Exception as e:
            print(f"❌ Errore critico: Nessun dispositivo audio di input/output trovato. {e}")
            raise

        self.input_audio_queue = queue.Queue()
        self.input_stream = None
        print("✅ Agente inizializzato.")

    def _audio_callback(self, indata, frames, time, status):
        if status: print(f"Errore callback: {status}")
        self.input_audio_queue.put(indata.copy())

    def start_listening(self):
        if self.input_stream is None:
            try:
                self.input_stream = sd.InputStream(
                    device=self.input_device, channels=INPUT_CHANNELS,
                    samplerate=self.device_sample_rate, callback=self._audio_callback, dtype='float32'
                )
                self.input_stream.start()
                print(f"🎤 In ascolto da: {sd.query_devices(self.input_device)['name']}...")
            except sd.PortAudioError as e:
                print(f"❌ ERRORE: Impossibile usare il microfono. Un'altra applicazione potrebbe essere in esecuzione. ({e})")
                self.conversation_active = False
            except Exception as e:
                print(f"❌ Errore avvio ascolto: {e}")
                self.conversation_active = False

    async def listen_for_user_input(self):
        self.start_listening()
        if not self.conversation_active: return

        recorded_chunks = []
        silence_start_time = None
        chunk_counter = 0

        while self.conversation_active:
            try:
                audio_chunk = self.input_audio_queue.get_nowait()
                rms = np.sqrt(np.mean(audio_chunk**2))

                # REINTRODUCIAMO IL DEBUG
                chunk_counter += 1
                if chunk_counter % 20 == 0: # Stampa ogni ~secondo
                    print(f"  [DEBUG] Audio RMS: {rms:.6f}")

                is_speech = rms > SILENCE_THRESHOLD_RMS

                if is_speech:
                    silence_start_time = None
                    if not self.is_user_speaking:
                        print("\nL'utente ha iniziato a parlare...")
                        self.is_user_speaking = True
                        recorded_chunks = []
                    recorded_chunks.append(audio_chunk)
                elif self.is_user_speaking:
                    if silence_start_time is None:
                        silence_start_time = time.monotonic()

                    if time.monotonic() - silence_start_time > SILENCE_DURATION_S:
                        print("L'utente ha finito di parlare.")
                        self.is_user_speaking = False
                        full_audio_data = np.concatenate(recorded_chunks)
                        recorded_chunks = []
                        asyncio.create_task(self.respond_to_user(full_audio_data))

            except queue.Empty:
                await asyncio.sleep(0.05)

    async def respond_to_user(self, user_audio_data: np.ndarray):
        print("🤖 Invio audio a ElevenLabs...")
        self.is_agent_speaking = True
        try:
            target_len = int(len(user_audio_data) * INPUT_SAMPLE_RATE / self.device_sample_rate)
            resampled_audio = resample(user_audio_data, target_len).astype(np.float32)
            audio_bytes = (resampled_audio * 32767).astype(np.int16).tobytes()

            response_stream = self.client.generate(
                text="Ciao! Se mi senti e io ho risposto alla tua voce, la configurazione è finalmente corretta.",
                model="eleven_multilingual_v2", stream=True
            )
            print(f"▶️ Riproduzione risposta su: {sd.query_devices(self.output_device)['name']}")
            for audio_chunk in response_stream:
                if not self.is_agent_speaking:
                    print("⚡️ INTERRUZIONE!")
                    break
                if audio_chunk:
                    sd.play(np.frombuffer(audio_chunk, dtype=np.int16), samplerate=OUTPUT_SAMPLE_RATE, device=self.output_device)
            sd.wait()
        except Exception as e:
            print(f"❌ Errore durante la risposta: {e}")
        finally:
            print("Fine risposta agente.")
            self.is_agent_speaking = False

    def stop_conversation(self):
        print("\n🛑 Termino la conversazione...")
        self.conversation_active = False
        sd.stop()
        if self.input_stream and self.input_stream.active:
            self.input_stream.close()
            print("🎤 Microfono spento.")

async def main():
    agent = None
    try:
        agent = StreamingAgent()
        await agent.listen_for_user_input()
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"❌ Errore critico: {e}")
    finally:
        if agent:
            agent.stop_conversation()
        print("\n👋 Addio!")

if __name__ == "__main__":
    asyncio.run(main())
