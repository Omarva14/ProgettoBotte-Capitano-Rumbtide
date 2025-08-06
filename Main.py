# Progetto_Stabile/main.py
import asyncio
import signal

from agent import ConversationalAgent, logger

async def main():
    """
    Funzione principale per avviare e gestire l'agente conversazionale.
    """
    agent = ConversationalAgent()

    # Gestione dell'arresto pulito con Ctrl+C
    loop = asyncio.get_running_loop()
    stop = loop.create_future()
    loop.add_signal_handler(signal.SIGINT, stop.set_result, None)

    # Avvia i task principali
    agent_task = asyncio.create_task(agent.start())

    logger.info("Sistema avviato. Premi Ctrl+C per terminare.")

    # Attende il segnale di stop o il completamento del task dell'agente
    await asyncio.wait([stop, agent_task], return_when=asyncio.FIRST_COMPLETED)

    logger.info("Segnale di arresto ricevuto. Pulizia in corso...")

    # Ferma l'agente e cancella il task
    await agent.stop()
    agent_task.cancel()

    try:
        await agent_task
    except asyncio.CancelledError:
        logger.info("Task dell'agente terminato correttamente.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Programma terminato.")
omar@Omar:~/ProgettoBotte/ProgettoModulare_Funzionante/Progetto_Stabile$
