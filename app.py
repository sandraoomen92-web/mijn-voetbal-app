import streamlit as st
import pandas as pd
import requests
import json
import base64
import datetime

# --- GITHUB CONFIGURATIE VIA SECRETS ---
GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
REPO = st.secrets["GITHUB_REPO"]  # sandraoomen92-web/mijn-voetbal-app
FILE_PATH = "voetbal_data.json"
URL = f"https://api.github.com/repos/{REPO}/contents/{FILE_PATH}"
HEADERS = {"Authorization": f"token {GITHUB_TOKEN}"}

# --- INITIALISATIE SESSION STATE ---
if "opstelling_datum" not in st.session_state:
    st.session_state.opstelling_datum = datetime.date.today()
if "opst_posities" not in st.session_state:
    st.session_state.opst_posities = {}
if "opst_formatie" not in st.session_state:
    st.session_state.opst_formatie = ""

# --- FUNCTIES VOOR DATA-BEHEER VIA GITHUB ---
def laad_data_van_github():
    response = requests.get(URL, headers=HEADERS)
    if response.status_code == 200:
        content = response.json()
        file_content = base64.b64decode(content["content"]).decode("utf-8")
        return json.loads(file_content), content["sha"]
    elif response.status_code == 404:
        basis_data = {"spelers": [], "trainingen": [], "opstellingen": {}}
        return basis_data, None
    else:
        st.error(f"Fout bij laden van GitHub: {response.status_code}")
        return {"spelers": [], "trainingen": [], "opstellingen": {}}, None

def sla_data_op_naar_github(data, sha):
    data_string = json.dumps(data, indent=4)
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

def list_opstelling_datums(data):
    if "opstellingen" in data and data["opstellingen"]:
        return sorted(list(data["opstellingen"].keys()), reverse=True)
    return []

# --- DATA INLADEN ---
data, file_sha = laad_data_van_github()

# Zorg dat de juiste mappen altijd bestaan in de data
if "spelers" not in data: data["spelers"] = []
if "trainingen" not in data: data["trainingen"] = []
if "opstellingen" not in data: data["opstellingen"] = {}

df_spelers = pd.DataFrame(data.get("spelers", []))

# --- STREAMLIT INTERFACE ---
st.title("⚽ Mijn Voetbal App")

tab1, tab2, tab3 = st.tabs(["📋 Spelersbeheer", "⏱️ Trainingen", "🧠 Opstelling"])

# === TAB 1: SPELERSBEHEER ===
with tab1:
    st.header("Spelerslijst")
    if not df_spelers.empty:
        st.dataframe(df_spelers, use_container_width=True)
    else:
        st.info("Er zijn nog geen spelers toegevoegd.")
        
    st.subheader("Nieuwe speler toevoegen")
    nieuwe_speler = st.text_input("Naam van de speler:")
    nieuw_nummer = st.number_input("Rugnummer:", min_value=1, max_value=99, value=1)
    
    if st.button("Speler Opslaan"):
        if nieuwe_speler:
            data["spelers"].append({"naam": nieuwe_speler, "nummer": int(nieuw_nummer), "Aanwezig": True})
            sla_data_op_naar_github(data, file_sha)
        else:
            st.warning("Vul eerst een naam in.")

# === TAB 2: TRAININGEN ===
with tab2:
    st.header("Trainingen")
    st.info("Hier kun je later trainingen beheren.")

# === TAB 3: OPSTELLING ===
with tab3:
    st.markdown("## 🟠 Opstelling per wedstrijd")
 
    if not data["spelers"]:
        st.warning("Voeg eerst spelers toe via het Team-menu.")
    else:
        alle_opst_keys = list_opstelling_datums(data)
 
        dc1, dc2 = st.columns([1, 1])
        with dc1:
            gekozen_datum = st.date_input(
                "📅 Wedstrijddatum",
                value=st.session_state.opstelling_datum,
                key="opst_datum_input"
            )
            if gekozen_datum != st.session_state.opstelling_datum:
                st.session_state.opstelling_datum = gekozen_datum
                st.session_state.opst_posities    = {}
                st.session_state.opst_formatie    = ""
                st.rerun()
 
        with dc2:
            if alle_opst_keys:
                def datum_label(dk):
                    try:    lbl = datetime.datetime.strptime(dk, "%Y-%m-%d").strftime("%d %B %Y")
                    except: lbl = dk
                    n  = len(data["opstellingen"][dk].get("posities", {}))
                    return f"{lbl} ({n} spelers)"
 
                opties   = ["— Kies opgeslagen opstelling —"] + alle_opst_keys
                labels   = ["— Kies opgeslagen opstelling —"] + [datum_label(dk) for dk in alle_opst_keys]
                gekozen  = st.selectbox("📂 Opgeslagen opstellingen", labels, key="opst_zoek")
                if gekozen != labels[0]:
                    idx = labels.index(gekozen)
                    dk  = opties[idx]
                    nieuwe_datum = datetime.datetime.strptime(dk, "%Y-%m-%d").date()
                    if nieuwe_datum != st.session_state.opstelling_datum:
                        st.session_state.opstelling_datum = nieuwe_datum
                        st.session_state.opst_posities    = {}
                        st.session_state.opst_formatie    = ""
                        st.rerun()
 
        datum_key   = str(st.session_state.opstelling_datum)
        datum_label_str = st.session_state.opstelling_datum.strftime("%d %B %Y")
 
        bestaande_entry = data["opstellingen"].get(datum_key, {})
        posities_init   = bestaande_entry.get("posities", {}) if isinstance(bestaande_entry, dict) else {}
        formatie_init   = bestaande_entry.get("formatie", "")  if isinstance(bestaande_entry, dict) else ""
 
        heeft_opgeslagen = datum_key in data["opstellingen"]
        if heeft_opgeslagen:
            st.success(f"Opgeslagen opstelling voor **{datum_label_str}** — {len(posities_init)} spelers op het veld.")
        else:
            st.info(f"Nog geen opstelling voor **{datum_label_str}**.")
 
        sk1, sk2, sk3 = st.columns([2, 1, 1])
        with sk1:
            pass  
        with sk2:
            opslaan_clicked = st.button("💾 Opstelling opslaan", type="primary", use_container_width=True, key="opst_opslaan")
        with sk3:
            reset_clicked = st.button("🔄 Reset veld", use_container_width=True, key="opst_reset")
 
        if reset_clicked:
            st.session_state.opst_posities = {}
            st.session_state.opst_formatie = ""
            st.rerun()
 
        if opslaan_clicked:
            posities_te_slaan = st.session_state.get("opst_posities", {})
            formatie_te_slaan = st.session_state.get("opst_formatie", "")
            if not posities_te_slaan:
                st.warning("⚠️ Er staan geen spelers op het veld. Plaats eerst spelers en klik dan op opslaan.")
            else:
                data["opstellingen"][datum_key] = {
                    "posities": posities_te_slaan,
                    "formatie": formatie_te_slaan,
                }
                sla_data_op_naar_github(data, file_sha)
 
        # --- VERBORGEN BRUG ---
        # (De CSS en HTML-componenten zoals in jouw originele code)
        brug_css = """
        <style>
        div[data-testid="stTextInput"]:has(input[aria-label="opst_brug_input"]) {
            position: absolute !important;
            opacity: 0 !important;
            pointer-events: none !important;
            height: 0 !important;
            overflow: hidden !important;
            top: -9999px !important;
        }
        </style>
        """
        st.markdown(brug_css, unsafe_allow_html=True)
        brug_waarde = st.text_input("opst_brug_input", value="", key="opst_brug", label_visibility="hidden")
 
        if brug_waarde and brug_waarde.strip():
            try:
                payload = json.loads(brug_waarde)
                st.session_state.opst_posities = payload.get("posities", {})
                st.session_state.opst_formatie = payload.get("formatie", "")
                st.session_state.opst_brug = ""
            except json.JSONDecodeError:
                pass
 
        # --- JOUW VELD-IFRAME HTML ---
        spelers_json      = json.dumps(data["spelers"], ensure_ascii=False)
        posities_json_str = json.dumps(posities_init, ensure_ascii=False)
        formatie_json_str = json.dumps(formatie_init, ensure_ascii=False)
        datum_json        = json.dumps(datum_key, ensure_ascii=False)
 
        veld_html = f"""<!DOCTYPE html>
<html lang="nl">
<head>
<meta charset="utf-8">
<style>
* {{ box-sizing:border-box; margin:0; padding:0; }}
body {{ background:#FFF; font-family:'Inter',sans-serif; color:#111; padding:8px; }}
.wrap {{ display:flex; flex-direction:column; gap:12px; max-width:700px; margin:0 auto; }}
h3 {{ font-family:'Bebas Neue',cursive; color:#111; font-size:1.2rem; letter-spacing:2px; }}
.veld-wrap {{ width:100%; aspect-ratio:68/105; max-height:65vh; margin:0 auto; position:relative; }}
#veld {{
    width:100%; height:100%;
    background:linear-gradient(180deg,#1a5c28 0%,#1e6b2e 25%,#1a5c28 50%,#1e6b2e 75%,#1a5c28 100%);
    border-radius:8px; border:3px solid #fff; position:relative; overflow:hidden; touch-action:none;
}}
#veld::before {{ content:''; position:absolute; top:50%; left:0; right:0; height:2px; background:rgba(255,255,255,.6); }}
.cirkel {{ position:absolute; top:50%; left:50%; transform:translate(-50%,-50%); width:20%; aspect-ratio:1; border:2px solid rgba(255,255,255,.6); border-radius:50%; pointer-events:none; }}
.sp-boven,.sp-onder {{ position:absolute; left:20%; right:20%; height:14%; border:2px solid rgba(255,255,255,.6); pointer-events:none; }}
.sp-boven {{ top:0; border-top:none; border-radius:0 0 6px 6px; }}
.sp-onder {{ bottom:0; border-bottom:none; border-radius:6px 6px 0 0; }}
.gb,.go {{ position:absolute; left:35%; right:35%; height:4%; border:2px solid rgba(255,255,255,.8); background:rgba(255,255,255,.1); pointer-events:none; }}
.gb {{ top:0; border-top:none; }} .go {{ bottom:0; border-bottom:none; }}
.gs {{ position:absolute; top:0; bottom:0; width:9.09%; background:rgba(0,0,0,.08); pointer-events:none; }}
.token {{ position:absolute; transform:translate(-50%,-50%); cursor:grab; touch-action:none; user-select:none; z-index:10; display:flex; flex-direction:column; align-items:center; gap:2px
