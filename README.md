🌱 Eco-Analyst: Simulatore Energetico e Agente di Sostenibilità

Autori: Gruppo 2 (Natale D'Esposito, Natalia Pasquetto, Diego Cibin e Viviana Di Domenico)

Eco-Analyst è un'applicazione web interattiva sviluppata in Python con Streamlit. Il progetto unisce la simulazione di Data Science con un agente di Intelligenza Artificiale (AI) basato sull'API di Gemini per fornire agli utenti strumenti per analizzare l'impatto del mix energetico e ricevere consigli pratici di sostenibilità.

⚙️ Architettura e Componenti Chiave

L'applicazione è contenuta in un unico file, eco_analyst.py, e si basa su due moduli principali che lavorano in parallelo.

1. Modulo di Simulazione Energetica (Data Science)

Questo modulo gestisce l'analisi quantitativa dell'impatto ambientale.

⦁	Funzionalità: Permette agli utenti di regolare le percentuali di diverse fonti energetiche (Solare, Vento, Idrico, Gas Fossile, Carbone) tramite slider laterali.

⦁	Calcoli: Utilizza Pandas e NumPy per eseguire calcoli vettoriali rapidi che determinano in modo fittizzio, generico e semplice:
   - L'energia totale generata (GWh/anno).
   - Le emissioni totali di CO2 (Tonnellate).
   - I costi totali stimati (Milioni di €).

⦁	Metriche: Include un Indicatore Chiave di Performance (KPI) che calcola e visualizza in tempo reale la percentuale di energia rinnovabile nel mix complessivo.

2. Modulo Agente AI (Intelligenza Artificiale)

Questo modulo risponde alle domande degli utenti su smaltimento, riciclo e strategie ecologiche.

⦁	Tecnologia AI: La logica è gestita dalla funzione call_gemini, che interagisce con l'API di Gemini 2.5 Flash.

⦁	Prompt Engineering: Un'istruzione di sistema (System Prompt) definisce la persona dell'AI come "esperto di sostenibilità ambientale", garantendo risposte pertinenti, chiare e pratiche.

⦁	Grounding (Verifica Fonti): L'integrazione con il Google Search Grounding è abilitata. Questo assicura che le risposte siano fondate su informazioni attuali e verificate dal web, con le relative citazioni fornite direttamente sotto la risposta.

🚀 Guida all'Installazione e Setup Locale

Per eseguire Eco-Analyst sul tuo computer, segui questi passaggi:

Prerequisiti

È necessario avere Python installato.


1. Clonare la Repository

git clone [INSERIRE QUI IL TUO URL GITHUB]
cd eco-analyst


2. Installare le Dipendenze

Crea un ambiente virtuale (consigliato) e installa le librerie necessarie:

pip install streamlit pandas numpy requests


3. Configurazione dell'API di Gemini

Il codice utilizza l'API di Gemini per l'Agente AI.

Ottieni la tua chiave API di Gemini.

Apri il file eco_analyst.py e, se necessario per il tuo ambiente, inserisci la chiave nella variabile API_KEY (anche se l'ambiente di esecuzione finale potrebbe fornirla automaticamente).


4. Esecuzione dell'App

Avvia l'applicazione dal terminale Streamlit:

streamlit run eco_analyst.py


L'app si aprirà automaticamente nel tuo browser, di solito all'indirizzo http://localhost:8501.

📝 Licenza

Questo progetto utilizza il framework Streamlit, distribuito sotto Licenza Apache 2.0 (Copyright 2025 Snowflake Inc.). Il codice specifico del progetto (eco_analyst.py) è rilasciato sotto Licenza MIT.
