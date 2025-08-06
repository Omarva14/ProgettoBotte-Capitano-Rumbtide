DOWNLOAD DA YOU TUBE , URL 

https://www.youtube.com/watch?v=ljTfHitG0eA&list=RDljTfHitG0eA&start_radio=1 

############################################################################

GESTIONE DELLA TRACCIA DI SOTTOFONDO (LOGICA DI RIPRODUZIONE)
OBIETTIVO:
Integrare una traccia audio di sottofondo rilassante che:

Si avvia in automatico all’avvio dell’esperienza (insieme al main).

Ha un volume iniziale impostato al 60% (parametro sperimentale).

Si sospende automaticamente quando viene riprodotto un brano o una playlist da Spotify.

Riprende automaticamente, in loop, non appena la traccia Spotify termina.

FLUSSO LOGICO:
Avvio Esperienza:

La traccia di sottofondo si carica e parte in riproduzione automatica.

Volume iniziale impostato al 60%.

Monitoraggio Stato Spotify:

Il sistema deve monitorare continuamente lo stato di riproduzione di Spotify.

Condizione:

Se Spotify inizia la riproduzione (brano o playlist):

Pausa immediata della traccia di sottofondo.

Se Spotify termina la riproduzione (fine brano/playlist o stop manuale):

La traccia di sottofondo riprende in loop.

Canale Dedicato (FASE FINALE):

Nella fase di assemblaggio definitivo, la traccia di sottofondo verrà assegnata ad un canale audio dedicato per una gestione più precisa e professionale del mix sonoro.

NOTE TECNICHE:
Il loop della traccia di sottofondo deve essere fluido e senza interruzioni percepibili.

Il volume del sottofondo può essere soggetto a ulteriori regolazioni in fase di testing (parametro sperimentale).

La gestione delle transizioni (pausa/ripresa) deve essere immediata e senza ritardi per evitare sovrapposizioni o silenzi innaturali.

È consigliato prevedere un leggero fade-in / fade-out (es. 0.5s-1s) per migliorare la percezione naturale dei passaggi.

