import streamlit as st
import pandas as pd
from datetime import date, datetime
import json
import os
from streamlit_gsheets import GSheetsConnection  # <-- NIEUW: Voor de Google Sheets koppeling

st.set_page_config(page_title="⚽ BV O19-1 Dashboard", page_icon="⚽", layout="wide")

# Maak verbinding met Google Sheets (Streamlit pakt automatisch de Secrets die je net hebt ingevuld)
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    try:
        # Haal de data op uit de 3 verschillende tabbladen (ttl=0 zorgt dat de data altijd live is)
        df_spelers = conn.read(worksheet="spelers", ttl=0)
        df_trainingen = conn.read(worksheet="trainingen", ttl=0)
        df_opstelling = conn.read(worksheet="opstelling", ttl=0)
        
        # We starten met de basisstructuur van jouw app
        data = {"spelers": [], "trainingen": {}, "opstelling": {}}
        
        # 1. Spelers inladen
        if not df_spelers.empty:
            for _, row in df_spelers.iterrows():
                if pd.notna(row['naam']):
                    data["spelers"].append({
                        "naam": str(row['naam']),
                        "positie": str(row['positie']),
                        "nummer": int(row['nummer'])
                    })
                    
        # 2. Trainingen/Aanwezigheid inladen
        if not df_trainingen.empty:
            for _, row in df_trainingen.iterrows():
                if pd.notna(row['datum']):
                    d_key = str(row['datum'])
                    data["trainingen"][d_key] = {
                        "afwezig": json.loads(row['afwezig']) if pd.notna(row['afwezig']) else [],
                        "blessure": json.loads(row['blessure']) if pd.notna(row['blessure']) else []
                    }
                    # Als er een notitie in Google Sheets staat, laden we die ook netjes in
                    if 'notitie' in df_trainingen.columns and pd.notna(row['notitie']) and str(row['notitie']).strip():
                        data["trainingen"][f"{d_key}_notitie"] = str(row['notitie'])
                    
        # 3. Opstellingen inladen
        if not df_opstelling.empty:
            for _, row in df_opstelling.iterrows():
                if pd.notna(row['datum']):
                    d_key = str(row['datum'])
                    data["opstelling"][d_key] = {
                        "posities": json.loads(row['posities']) if pd.notna(row['posities']) else {},
                        "formatie": str(row['formatie']) if pd.notna(row['formatie']) else ""
                    }
        return data
        
    except Exception as e:
        # Als de sheet nog leeg is (eerste keer), starten we met een lege basis
        return {"spelers": [], "trainingen": {}, "opstelling": {}}

def save_data(data):
    # 1. Spelers omzetten naar een tabel voor Google Sheets
    spelers_rijen = []
    for s in data["spelers"]:
        spelers_rijen.append({"naam": s["naam"], "positie": s["positie"], "nummer": s["nummer"]})
    df_spelers = pd.DataFrame(spelers_rijen) if spelers_rijen else pd.DataFrame(columns=["naam", "positie", "nummer"])
    
    # 2. Trainingen/Aanwezigheid omzetten naar een tabel (inclusief de notities!)
    trainingen_rijen = []
    for datum, sessie in data["trainingen"].items():
        if not datum.endswith("_notitie"):
            notitie_key = f"{datum}_notitie"
            notitie_tekst = data["trainingen"].get(notitie_key, "")
            trainingen_rijen.append({
                "datum": datum,
                "afwezig": json.dumps(sessie.get("afwezig", [])),
                "blessure": json.dumps(sessie.get("blessure", [])),
                "notitie": notitie_tekst
            })
    df_trainingen = pd.DataFrame(trainingen_rijen) if trainingen_rijen else pd.DataFrame(columns=["datum", "afwezig", "blessure", "notitie"])
    
    # 3. Opstellingen omzetten naar een tabel
    opstelling_rijen = []
    for datum, opst in data["opstelling"].items():
        opstelling_rijen.append({
            "datum": datum,
            "posities": json.dumps(opst.get("posities", {})),
            "formatie": opst.get("formatie", "")
        })
    df_opstelling = pd.DataFrame(opstelling_rijen) if opstelling_rijen else pd.DataFrame(columns=["datum", "posities", "formatie"])
    
    # Schrijf de tabellen live naar de juiste tabbladen in Google Sheets
    conn.update(worksheet="spelers", data=df_spelers)
    conn.update(worksheet="trainingen", data=df_trainingen)
    conn.update(worksheet="opstelling", data=df_opstelling)


def list_opstelling_datums(data):
    return sorted(data.get("opstelling", {}).keys(), reverse=True)

if "data" not in st.session_state:
    st.session_state.data = load_data()
if "page" not in st.session_state:
    st.session_state.page = "team"
if "edit_speler" not in st.session_state:
    st.session_state.edit_speler = None
if "opstelling_datum" not in st.session_state:
    st.session_state.opstelling_datum = date.today()
# Bridge: JavaScript schrijft posities hierin via postMessage
if "opst_posities" not in st.session_state:
    st.session_state.opst_posities = {}
if "opst_formatie" not in st.session_state:
    st.session_state.opst_formatie = ""

data = st.session_state.data
if "opstelling" not in data:
    data["opstelling"] = {}

# ─── CSS ──────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Inter:wght@400;600;700&display=swap');

:root {
    --oranje:      #C44A00;
    --oranje-dim:  #FFF0E6;
    --zwart:       #111111;
    --tekst:       #111111;
    --tekst-mid:   #333333;
    --tekst-zacht: #555555;
    --bg:          #FFFFFF;
    --bg-subtle:   #F5F5F5;
    --bg-muted:    #EBEBEB;
    --rand:        #BBBBBB;
    --rand-sterk:  #555555;
}

html, body, .stApp,
[data-testid="stAppViewContainer"],
[data-testid="stMain"],
[data-testid="block-container"],
[class*="css"] {
    background-color: var(--bg) !important;
    color: var(--tekst) !important;
    font-family: 'Inter', sans-serif !important;
}

section[data-testid="stSidebar"] { display: none !important; }

/* Koppen */
h1, h2, h3,
.stApp h1, .stApp h2, .stApp h3,
[data-testid="stMarkdown"] h1,
[data-testid="stMarkdown"] h2,
[data-testid="stMarkdown"] h3,
[data-testid="stMarkdownContainer"] h1,
[data-testid="stMarkdownContainer"] h2,
[data-testid="stMarkdownContainer"] h3 {
    font-family: 'Bebas Neue', sans-serif !important;
    letter-spacing: 2px !important;
    color: var(--zwart) !important;
    -webkit-text-fill-color: var(--zwart) !important;
    opacity: 1 !important;
}
h1, .stApp h1,
[data-testid="stMarkdown"] h1,
[data-testid="stMarkdownContainer"] h1 {
    font-size: clamp(1.8rem, 6vw, 3rem) !important;
    color: var(--oranje) !important;
    -webkit-text-fill-color: var(--oranje) !important;
}

/* Labels & tekst */
label, p, span,
[data-testid="stWidgetLabel"],
[data-testid="stExpander"] > details > summary,
[data-testid="stExpander"] > details > summary *,
.streamlit-expanderHeader,
.streamlit-expanderHeader * {
    color: var(--tekst) !important;
    -webkit-text-fill-color: var(--tekst) !important;
    opacity: 1 !important;
}
[data-testid="stExpander"] > details > summary,
.streamlit-expanderHeader {
    background-color: var(--bg-subtle) !important;
    font-weight: 600 !important;
}

/* Inputs */
input, textarea,
.stTextInput input, .stNumberInput input, .stDateInput input {
    color: var(--tekst) !important;
    -webkit-text-fill-color: var(--tekst) !important;
    background-color: var(--bg) !important;
    border-color: var(--rand-sterk) !important;
}
[data-baseweb="select"],
[data-baseweb="select"] div,
[data-baseweb="select"] span {
    color: var(--tekst) !important;
    -webkit-text-fill-color: var(--tekst) !important;
    background-color: var(--bg) !important;
}
[data-baseweb="menu"] li { color: var(--tekst) !important; background: var(--bg) !important; }
[data-baseweb="menu"] li:hover { background: var(--oranje-dim) !important; }

/* Multiselect tags */
[data-baseweb="tag"] {
    background-color: var(--oranje-dim) !important;
    border: 1px solid var(--oranje) !important;
    border-radius: 6px !important;
}
[data-baseweb="tag"] span {
    color: var(--oranje) !important;
    -webkit-text-fill-color: var(--oranje) !important;
    font-weight: 700 !important;
}
[data-baseweb="tag"] svg { fill: var(--oranje) !important; }

/* Knoppen */
.stButton > button {
    font-family: 'Inter', sans-serif !important;
    font-weight: 700 !important;
    font-size: 0.9rem !important;
    border-radius: 8px !important;
    min-height: 2.75rem !important;
    border-width: 2px !important;
}
.stButton > button[kind="primary"] {
    background-color: var(--oranje) !important;
    color: #FFFFFF !important;
    -webkit-text-fill-color: #FFFFFF !important;
    border-color: var(--oranje) !important;
}
.stButton > button[kind="secondary"] {
    background-color: var(--bg-subtle) !important;
    color: var(--zwart) !important;
    -webkit-text-fill-color: var(--zwart) !important;
    border-color: var(--rand-sterk) !important;
}

/* Alerts */
[data-testid="stAlert"] p,
[data-testid="stAlert"] span {
    color: var(--tekst) !important;
    -webkit-text-fill-color: var(--tekst) !important;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    background: var(--bg-subtle) !important;
    border: 1px solid var(--rand) !important;
    border-radius: 8px; padding: 4px; gap: 4px;
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    color: var(--tekst-mid) !important;
    -webkit-text-fill-color: var(--tekst-mid) !important;
    font-family: 'Bebas Neue', sans-serif;
    letter-spacing: 1px; font-size: 1rem; border-radius: 6px;
}
.stTabs [aria-selected="true"] {
    background: var(--oranje) !important;
    color: #FFFFFF !important;
