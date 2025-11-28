import streamlit as st
import pandas as pd
import numpy as np
import requests
import json
import time

#CONFIGURAZIONE GLOBALE E API
#streamlit: configurazione della pagina
st.set_page_config(
    page_title="Eco-Analyst: Simulatore Energetico e Consigli di Sostenibilità",
    layout="wide",
    initial_sidebar_state="expanded"
)

#variabili globali per l'API di Gemini
API_KEY = ""  #IMPORTANTE inserire la propria chiave API Gemini e runnare il file con streamlit dal terminale!
API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-09-2025:generateContent"

#costanti fittizie per i calcoli energetici
#proprietà rinnovabile
FACTORS = {
    "Solare": {"CO2_kg_per_MWh": 50, "Costo_per_MWh": 40, "Capacità_Base_MW": 300, "Rinnovabile": True},
    "Vento": {"CO2_kg_per_MWh": 15, "Costo_per_MWh": 60, "Capacità_Base_MW": 500, "Rinnovabile": True},
    "Idrico": {"CO2_kg_per_MWh": 10, "Costo_per_MWh": 55, "Capacità_Base_MW": 400, "Rinnovabile": True},
    "Gas_Fossile": {"CO2_kg_per_MWh": 490, "Costo_per_MWh": 120, "Capacità_Base_MW": 800, "Rinnovabile": False},
    "Carbone": {"CO2_kg_per_MWh": 820, "Costo_per_MWh": 150, "Capacità_Base_MW": 600, "Rinnovabile": False},
}


#FUNZIONI DATI E CALCOLO

def simulate_energy(mix_percentages):
    """
    Esegue la simulazione del mix energetico utilizzando NumPy e Pandas.
    Calcola la percentuale di energia rinnovabile.
    """
    sources = list(FACTORS.keys())
    
    #1. crea un DataFrame con i fattori e le percentuali attuali
    df_factors = pd.DataFrame.from_dict(FACTORS, orient='index')
    
    #mappa le percentuali di input ai fattori
    df_factors['Mix_Pct'] = [mix_percentages[source] for source in sources]
    
    #normalizza le percentuali per garantire che sommino a 100
    total_pct = df_factors['Mix_Pct'].sum()
    if total_pct > 0:
        df_factors['Mix_Pct_Normalizzata'] = df_factors['Mix_Pct'] / total_pct
    else:
        df_factors['Mix_Pct_Normalizzata'] = 0
        
    #la capacità totale generata è arbitraria
    total_base_capacity = df_factors['Capacità_Base_MW'].sum()
    
    #2. calcoli basati sul mix (uso di numpy per operazioni vettoriali)
    
    #Capacità Attuale = Percentuale Normalizzata * Capacità Totale
    #NumPy per il calcolo vettoriale:
    capacity_array = df_factors['Mix_Pct_Normalizzata'].to_numpy() * total_base_capacity
    df_factors['Capacità_MW'] = capacity_array
    
    #energia generata (assumiamo un fattore di carico costante per semplicità)
    energy_MWh = df_factors['Capacità_MW'] * 24 * 365 / 1000 #esempio
    df_factors['Energia_GWh_Annuale'] = energy_MWh
    
    #emissioni CO2 totali (NumPy)
    co2_array = df_factors['CO2_kg_per_MWh'].to_numpy() * energy_MWh.to_numpy()
    df_factors['CO2_Totale_Tonnellate'] = co2_array / 1000
    
    #costo totale (NumPy)
    cost_array = df_factors['Costo_per_MWh'].to_numpy() * energy_MWh.to_numpy()
    df_factors['Costo_Totale_Milioni_EUR'] = cost_array / 1000000
    
    #energia rinnovabile
    renewable_energy = df_factors[df_factors['Rinnovabile'] == True]['Energia_GWh_Annuale'].sum()
    total_energy = df_factors['Energia_GWh_Annuale'].sum()
    
    if total_energy > 0:
        renewable_pct = (renewable_energy / total_energy) * 100
    else:
        renewable_pct = 0
    
    #preparazione output
    
    results_df = df_factors[[
        'Mix_Pct_Normalizzata', 'Energia_GWh_Annuale', 'CO2_Totale_Tonnellate', 'Costo_Totale_Milioni_EUR'
    ]].copy()
    
    results_df.columns = [
        'Mix (%)', 'Energia (GWh/anno)', 'Emissioni CO2 (Tonn.)', 'Costo Totale (Mln €)'
    ]
    results_df['Mix (%)'] = (results_df['Mix (%)'] * 100).round(2)
    
    #restituisce il DataFrame e la metrica
    return results_df.round(2), renewable_pct


#FUNZIONE AGENTE AI (LLM)

def call_gemini(prompt: str):
    """
    Chiama l'API di Gemini per ottenere consigli di sostenibilità.
    Utilizza Google Search Grounding e Exponential Backoff.
    """
    
    #istruzione di sistema per l'Agente AI (Prompt Engineering)
    system_prompt = (
        "Agisci come un esperto di sostenibilità ambientale e gestione dei rifiuti, denominato 'Eco-Analyst'."
        "Fornisci consigli pratici e fondati su come smaltire, riciclare o riutilizzare oggetti, o rispondi a domande su strategie di sostenibilità ed efficienza energetica."
        "La risposta deve essere chiara, concisa e basata su informazioni attuali e verificate (citazioni necessarie). Rispondi sempre in italiano."
    )
    
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "tools": [{"google_search": {}}],  #abilita Google Search Grounding
        "systemInstruction": {"parts": [{"text": system_prompt}]}
    }

    headers = {'Content-Type': 'application/json'}
    
    #tentativi e backoff esponenziale
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = requests.post(
                f"{API_URL}?key={API_KEY}", 
                headers=headers, 
                data=json.dumps(payload),
                timeout=15 #timeout per la richiesta
            )
            response.raise_for_status() #solleva un errore per codici di stato HTTP non 2xx
            
            result = response.json()
            
            #estrazione del testo
            text = result.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', 'Errore: Risposta AI non valida o vuota.')
            
            #estrazione delle fonti (grounding)
            sources = []
            grounding_metadata = result.get('candidates', [{}])[0].get('groundingMetadata')
            if grounding_metadata and grounding_metadata.get('groundingAttributions'):
                sources = [{
                    'uri': attr.get('web', {}).get('uri'),
                    'title': attr.get('web', {}).get('title')
                } for attr in grounding_metadata['groundingAttributions'] if attr.get('web', {}).get('uri')]
            
            return text, sources

        except requests.exceptions.RequestException as e:
            if attempt < max_retries - 1:
                #aspetta e riprova
                sleep_time = 2 ** attempt
                #st.warning(f"Tentativo {attempt + 1} fallito. Riprovo in {sleep_time} secondi... ({e})")
                time.sleep(sleep_time)
            else:
                return f"Errore: Impossibile contattare l'API dopo {max_retries} tentativi. Dettagli: {e}", []
        except Exception as e:
            return f"Errore imprevisto durante l'elaborazione della risposta: {e}", []

    return "Errore sconosciuto durante la chiamata API.", []


#INTERFACCIA UTENTE STREAMLIT

def main():
    st.title("🌱 Eco-Analyst: Simulazione Energetica e Agente di Sostenibilità")
    st.markdown("""
        Benvenut* nel tuo strumento di analisi ambientale! 
        Esplora l'impatto del tuo mix energetico e ottieni consigli pratici di sostenibilità.
    """)

    st.sidebar.header("Imposta il tuo Mix Energetico")
    
    # ------------------------------------------------
    # SEZIONE 1: SIMULATORE DI MIX ENERGETICO (Pandas/NumPy)
    # ------------------------------------------------

    st.header("1. Simulatore di Mix Energetico")
    st.info("Regola la percentuale di partecipazione di ciascuna fonte energetica per vedere l'impatto su emissioni e costi.")

    #inizializza o recupera lo stato delle percentuali
    if 'mix_percentages' not in st.session_state:
        st.session_state['mix_percentages'] = {source: FACTORS[source]['Capacità_Base_MW'] / sum(f['Capacità_Base_MW'] for f in FACTORS.values()) * 100 for source in FACTORS}
    
    current_mix = {}
    
    #slider per l'input utente
    for source in FACTORS:
        #usare un input numerico per maggiore precisione, ma manteniamo la logica semplice
        factor = st.sidebar.slider(
            f"{source}",
            min_value=0,
            max_value=100,
            value=int(st.session_state['mix_percentages'].get(source, 0)),
            step=5,
            key=f"slider_{source}"
        )
        current_mix[source] = factor

    #ricalcolo dei risultati
    results_df, renewable_pct = simulate_energy(current_mix)

    #output del simulatore
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Dati di Output Dettagliati (DataFrame)")
        st.dataframe(results_df, use_container_width=True)
        
    with col2:
        st.subheader("Ripartizione Mix Energetico")
        #grafico a torta per il mix di energia (GWh)
        st.bar_chart(results_df['Energia (GWh/anno)'])

    #riepilogo KPI Globali
    st.markdown("---")
    st.subheader("Indicatori di Performance Totali")
    
    total_gwh = results_df['Energia (GWh/anno)'].sum()
    total_co2 = results_df['Emissioni CO2 (Tonn.)'].sum()
    total_cost = results_df['Costo Totale (Mln €)'].sum()
    
    #area in 4 colonne per far stare la metrica rinnovabili
    kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)
    
    kpi_col1.metric("Energia Totale Generata", f"{total_gwh:,.0f} GWh/anno")
    kpi_col2.metric("Emissioni CO2 Totali", f"{total_co2:,.0f} Tonnellate", delta=f"Media CO2: {total_co2 / total_gwh:.2f} kg/MWh" if total_gwh > 0 else "0", delta_color="inverse")
    kpi_col3.metric("Costo Totale Stimato", f"€{total_cost:,.2f} Milioni")
    
    #st.metric per visualizzare la percentuale di rinnovabili
    kpi_col4.metric(
        "Rinnovabili nel Mix", 
        f"{renewable_pct:.1f}%", 
        delta=f"Obiettivo: {100.0 - renewable_pct:.1f}% per 100%", 
        delta_color="normal" if renewable_pct < 50 else "inverse"
    )

    # ------------------------------------------------
    # SEZIONE 2: AGENTE AI ECO-ANALYST (LLM/Agentic AI)
    # ------------------------------------------------
    
    st.header("2. AI Eco-Analyst: Consigli di Sostenibilità")
    st.markdown("Chiedi all'agente AI come smaltire un oggetto, come ridurre il tuo impatto energetico, o qualsiasi domanda pratica sulla sostenibilità. (Esempio: 'Come devo smaltire un vecchio monitor?').")

    #input dell'utente per l'agente
    user_query = st.text_input(
        "La tua Domanda di Sostenibilità:",
        placeholder="Ad esempio: Qual è il modo migliore per riutilizzare i fondi di caffè in giardino?",
        key="ai_prompt"
    )

    #bottone per l'azione
    if st.button("Chiedi all'Eco-Analyst", use_container_width=True):
        if user_query:
            #mostra un indicatore di caricamento
            with st.spinner('L\'Eco-Analyst sta consultando le informazioni più recenti...'):
                ai_response, sources = call_gemini(user_query)
            
            #visualizza la risposta
            st.subheader("Risposta dell'Eco-Analyst")
            st.markdown(ai_response)
            
            #visualizza le fonti (Grounding)
            if sources:
                st.subheader("Fonti (Verificato con Google Search)")
                source_markdown = ""
                for i, source in enumerate(sources):
                    if source['uri'] and source['title']:
                        source_markdown += f"- **[{source['title']}](<{source['uri']}>)**\n"
                st.markdown(source_markdown)
            else:
                st.markdown("_Nessuna fonte esterna trovata per questa risposta._")
        else:
            st.warning("Per favore, inserisci una domanda prima di chiedere all'Eco-Analyst.")

    st.markdown("---")
    st.caption("Progetto Eco-Analyst del Gruppo 2 (Natale D'Esposito, Natalia Pasquetto, Diego Cibin e Viviana Di Domenico) | Utilizza Streamlit, Pandas, NumPy e l'API di Gemini.")
    
    #debug info per l'user per capire l'autenticazione
    st.sidebar.markdown("---")
    st.sidebar.subheader("Informazioni di Sistema")
    st.sidebar.code(f"App ID (Simulazione): {__app_id if '__app_id' in globals() else 'N/A'}")
    st.sidebar.markdown("L'integrazione con l'API di Gemini è gestita automaticamente dall'ambiente (se non è stata inserita la chiave API)")

#eseguire l'app streamlit
if __name__ == "__main__":
    main()