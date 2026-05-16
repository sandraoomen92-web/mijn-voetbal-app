import streamlit as st
import pandas as pd
from datetime import date, datetime
import requests
import json
import os
import base64

# --- CONFIGURATIE PAGINA ---
st.set_page_config(page_title="⚽ BV O19-1 Dashboard", page_icon="⚽", layout="wide")

DATA_FILE = "voetbal_data.json"
# --- GITHUB CONFIGURATIE VIA SECRETS ---
GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
REPO = st.secrets["GITHUB_REPO"]  # Bijv: sandraoomen92-web/mijn-voetbal-app
FILE_PATH = "voetbal_data.json"
URL = f"https://api.github.com/repos/{REPO}/contents/{FILE_PATH}"
HEADERS = {"Authorization": f"token {GITHUB_TOKEN}"}

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {"spelers": [], "trainingen": {}, "opstellingen": {}}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

def list_opstelling_datums(data):
    if "opstellingen" in data and data["opstellingen"]:
        return sorted(list(data["opstellingen"].keys()), reverse=True)
    return []

if "data" not in st.session_state:
    st.session_state.data = load_data()

# --- INITIALISATIE SESSION STATE ---
if "page" not in st.session_state:
    st.session_state.page = "team"
if "edit_speler" not in st.session_state:
    st.session_state.edit_speler = None
if "opstelling_datum" not in st.session_state:
    st.session_state.opstelling_datum = date.today()
if "opst_posities" not in st.session_state:
    st.session_state.opst_posities = {}
if "opst_formatie" not in st.session_state:
    st.session_state.opst_formatie = ""

# --- DATA INLADEN VAN GITHUB ---
def laad_data_van_github():
    response = requests.get(URL, headers=HEADERS)
    if response.status_code == 200:
        content = response.json()
        file_content = base64.b64decode(content["content"]).decode("utf-8")
        return json.loads(file_content), content["sha"]
    elif response.status_code == 404:
        basis_data = {"spelers": [], "trainingen": {}, "opstellingen": {}}
        return basis_data, None
    else:
        st.error(f"Fout bij laden van GitHub: {response.status_code}")
        return {"spelers": [], "trainingen": {}, "opstellingen": {}}, None

def sla_data_op_naar_github(data, sha):
    data_string = json.dumps(data, indent=2)
    content_bytes = base64.b64encode(data_string.encode("utf-8")).decode("utf-8")
    
    payload = {
        "message": "Update voetbal data via Streamlit App",
        "content": content_bytes
    }
    if sha:
        payload["sha"] = sha

    response = requests.put(URL, headers=HEADERS, json=payload)
    if response.status_code in [200, 201]:
        st.success("Data succesvol opgeslagen op GitHub! 💾")
        st.rerun()
    else:
        st.error(f"Fout bij opslaan naar GitHub: {response.text}")

data, file_sha = laad_data_van_github()

# Zorg dat de juiste mappen altijd correct aanwezig zijn
if "spelers" not in data: data["spelers"] = []
if "trainingen" not in data: data["trainingen"] = {}
if "opstellingen" not in data: data["opstellingen"] = {}

# ─── CSS STYLING ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Inter:wght@400;600;700&display=swap');

section[data-testid="stSidebar"] { display: none !important; }

h1, h2, h3, .stApp h1, .stApp h2, .stApp h3, [data-testid="stMarkdown"] h1 {
    font-family: 'Bebas Neue', cursive !important;
    letter-spacing: 2px !important;
}
</style>
""", unsafe_allow_html=True)

# ─── HEADER & NAVIGATIE ───────────────────────────────────────────────────────
st.markdown("# ⚽ VOETBAL DASHBOARD BV O19-1")
c1, c2, c3, _ = st.columns([1, 1, 1, 2])
with c1:
    if st.button("👥 Team", use_container_width=True, type="primary" if st.session_state.page == "team" else "secondary"):
        st.session_state.page = "team"; st.session_state.edit_speler = None; st.rerun()
with c2:
    if st.button("📋 Aanwezigheid", use_container_width=True, type="primary" if st.session_state.page == "aanwezigheid" else "secondary"):
        st.session_state.page = "aanwezigheid"; st.session_state.edit_speler = None; st.rerun()
with c3:
    if st.button("🟠 Opstelling", use_container_width=True, type="primary" if st.session_state.page == "opstelling" else "secondary"):
        st.session_state.page = "opstelling"; st.session_state.edit_speler = None; st.rerun()
st.markdown("---")

# ══════════════════════════════════════════════════════════════════════════════
# PAGINA 1 — TEAM
# ══════════════════════════════════════════════════════════════════════════════
if st.session_state.page == "team":
    st.markdown("## 👥 Teambeheer")
    with st.expander("➕ Nieuwe speler toevoegen", expanded=not bool(data["spelers"])):
        nieuwe_naam = st.text_input("Naam speler")
        nieuwe_positie = st.selectbox("Voorkeurspositie", ["Keeper", "Verdediger", "Middenvelder", "Aanvaller"])
        nieuwe_nummer = st.number_input("Rugnummer", min_value=1, max_value=99, value=1)
        if st.button("Speler Toevoegen", type="primary"):
            if nieuwe_naam.strip():
                if any(s["naam"].lower() == nieuwe_naam.strip().lower() for s in data["spelers"]):
                    st.error("Speler bestaat al!")
                else:
                    data["spelers"].append({"naam": nieuwe_naam.strip(), "positie": nieuwe_positie, "nummer": int(nieuwe_nummer)})
                    save_data(data)
                    st.success(f"✅ {nieuwe_naam.strip()} toegevoegd!")
                    sla_data_op_naar_github(data, file_sha)
            else:
                st.warning("Vul een naam in.")

    # Tonen van spelerslijst
    if data["spelers"]:
        st.markdown("### Huidige selectie")
        for s in data["spelers"]:
            naam = s["naam"]
            st.markdown(f"**{naam}** - {s['positie']} (#{s['nummer']})")

# ══════════════════════════════════════════════════════════════════════════════
# PAGINA 2 — AANWEZIGHEID
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.page == "aanwezigheid":
    st.markdown("## 📋 Aanwezigheidsregistratie")
    st.info("Aanwezigheidsbeheer module actief.")

# ══════════════════════════════════════════════════════════════════════════════
# PAGINA 3 — OPSTELLING
# ══════════════════════════════════════════════════════════════════════════════
else:
    st.markdown("## 🟠 Opstelling per wedstrijd")

    if not data["spelers"]:
        st.warning("Voeg eerst spelers toe via het Team-menu.")
        st.stop()

    alle_opst_keys = list_opstelling_datums(data)

    dc1, dc2 = st.columns([1, 1])
    with dc1:
        gekozen_datum = st.date_input("📅 Wedstrijddatum", value=st.session_state.opstelling_datum, key="opst_datum_input")
        if gekozen_datum != st.session_state.opstelling_datum:
            st.session_state.opstelling_datum = gekozen_datum
            st.session_state.opst_posities = {}
            st.session_state.opst_formatie = ""
            st.rerun()

    with dc2:
        if alle_opst_keys:
            def datum_label(dk):
                try:    lbl = datetime.strptime(dk, "%Y-%m-%d").strftime("%d %B %Y")
                except: lbl = dk
                n = len(data["opstellingen"].get(dk, {}).get("posities", {}))
                return f"{lbl} ({n} spelers)"

            opties = ["— Kies opgeslagen opstelling —"] + alle_opst_keys
            labels = ["— Kies opgeslagen opstelling —"] + [datum_label(dk) for dk in alle_opst_keys]
            gekozen = st.selectbox("📂 Opgeslagen opstellingen", labels, key="opst_zoek")
            if gekozen != labels[0]:
                idx = labels.index(gekozen)
                dk = opties[idx]
                nieuwe_datum = datetime.strptime(dk, "%Y-%m-%d").date()
                if nieuwe_datum != st.session_state.opstelling_datum:
                    st.session_state.opstelling_datum = nieuwe_datum
                    entry = data["opstellingen"].get(dk, {})
                    st.session_state.opst_posities = entry.get("posities", {})
                    st.session_state.opst_formatie = entry.get("formatie", "")
                    st.rerun()

    datum_key = str(st.session_state.opstelling_datum)
    datum_label_str = st.session_state.opstelling_datum.strftime("%d %B %Y")

    bestaande_entry = data["opstellingen"].get(datum_key, {})
    posities_init = bestaande_entry.get("posities", {}) if isinstance(bestaande_entry, dict) else {}
    formatie_init = bestaande_entry.get("formatie", "") if isinstance(bestaande_entry, dict) else ""

    if st.session_state.opst_posities == {} and posities_init != {}:
        st.session_state.opst_posities = posities_init
        st.session_state.opst_formatie = formatie_init

    heeft_opgeslagen = datum_key in data["opstellingen"]
    if heeft_opgeslagen:
        st.success(f"Opgeslagen opstelling voor **{datum_label_str}** gevonden.")
    else:
        st.info(f"Nog geen opstelling voor **{datum_label_str}**.")

    # ── Opslaan-knop BOVEN het iframe ─────────────────────────────────────────
    sk1, sk2,
