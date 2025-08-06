# Progetto_Stabile/audio_manager.py

import asyncio
import base64

# Valori basati su AUDIO_CONFIG in config.py
# 'output_sample_rate': 24000, 'channels': 1, 'format': 'pcm16' (2 bytes)
OUTPUT_SAMPLE_RATE = 24000
OUTPUT_CHANNELS = 1
OUTPUT_BYTES_PER_SAMPLE = 2  # pcm16 = 16 bits = 2 bytes

class AudioManager:
    """
    Gestisce la ricezione e la riproduzione dell'audio in streaming.
    Utilizza una coda per bufferizzare i chunk audio in arrivo e un loop
    asincrono per la riproduzione.
    """

    def __init__(self):
        """Inizializza l'AudioManager."""
        self.audio_queue = asyncio.Queue()
        self.is_playing = False
        self.interruption_event = asyncio.Event()
        self._playback_task = None

    async def queue_audio_chunk(self, audio_base64: str):
        """
        Decodifica un chunk audio da base64 e lo aggiunge alla coda di riproduzione.

        Args:
            audio_base64: Il chunk audio codificato in base64.
        """
        try:
            # Il padding base64 è a volte necessario per una decodifica corretta
            missing_padding = len(audio_base64) % 4
            if missing_padding:
                audio_base64 += '=' * (4 - missing_padding)
            audio_data = base64.b64decode(audio_base64)
            await self.audio_queue.put(audio_data)
        except (ValueError, TypeError) as e:
            print(f"Errore durante la decodifica del chunk audio base64: {e}")

    async def audio_playback_loop(self):
        """
        Esegue un ciclo per prelevare i chunk audio dalla coda e "riprodurli".
        La riproduzione è simulata da una stampa e da un'attesa calcolata
        in base alla durata del chunk audio.
        """
        while True:
            try:
                audio_chunk = await self.audio_queue.get()

                # Simula la riproduzione del chunk
                print(f"--- Riproduzione di un chunk audio di {len(audio_chunk)} bytes ---")

                # Calcola la durata per una simulazione realistica
                bytes_per_second = OUTPUT_SAMPLE_RATE * OUTPUT_CHANNELS * OUTPUT_BYTES_PER_SAMPLE
                duration_seconds = len(audio_chunk) / bytes_per_second

                await asyncio.sleep(duration_seconds)

                self.audio_queue.task_done()
            except asyncio.CancelledError:
                # Il task è stato cancellato, esce dal loop
                self.is_playing = False
                break
            except Exception as e:
                print(f"Errore inatteso nel ciclo di riproduzione: {e}")
                self.is_playing = False
                break
        print("Loop di riproduzione terminato.")

    def start_playback(self):
        """Avvia il loop di riproduzione audio come task in background."""
        if not self.is_playing:
            self.is_playing = True
            self._playback_task = asyncio.create_task(self.audio_playback_loop())
            print("Loop di riproduzione avviato.")

    async def stop_playback(self):
        """Ferma il loop di riproduzione audio e attende la sua terminazione."""
        if self.is_playing and self._playback_task:
            self._playback_task.cancel()
            try:
                await self._playback_task
            except asyncio.CancelledError:
                pass  # L'eccezione di cancellazione è prevista e gestita
            self.is_playing = False
            print("Loop di riproduzione fermato.")

    async def clear_audio_queue(self):
        """
        Svuota la coda audio.
        Essenziale per il barge-in, per evitare di riprodurre audio vecchio
        dopo che l'utente ha interrotto l'agente.
        """
        print("Svuotamento della coda audio...")
        while not self.audio_queue.empty():
            try:
                self.audio_queue.get_nowait()
                self.audio_queue.task_done()
            except asyncio.QueueEmpty:
                continue
        print("Coda audio svuotata.")
