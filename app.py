import streamlit as st
import pandas as pd
from datetime import date, datetime
import requests
import json
import os
import base64
import datetime

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
    return {"spelers": [], "trainingen": {}, "opstelling": {}}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

def list_opstelling_datums(data):
    return sorted(data.get("opstelling", {}).keys(), reverse=True)

if "data" not in st.session_state:
    st.session_state.data = load_data()
# --- INITIALISATIE SESSION STATE ---
if "page" not in st.session_state:
    st.session_state.page = "team"
if "edit_speler" not in st.session_state:
    st.session_state.edit_speler = None
if "opstelling_datum" not in st.session_state:
    st.session_state.opstelling_datum = date.today()
# Bridge: JavaScript schrijft posities hierin via postMessage
    st.session_state.opstelling_datum = datetime.date.today()
if "opst_posities" not in st.session_state:
    st.session_state.opst_posities = {}
if "opst_formatie" not in st.session_state:
    st.session_state.opst_formatie = ""

data = st.session_state.data
if "opstelling" not in data:
    data["opstelling"] = {}
# --- FUNCTIES VOOR DATA-BEHEER VIA GITHUB ---
def laad_data_van_github():
    response = requests.get(URL, headers=HEADERS)
    if response.status_code == 200:
        content = response.json()
        file_content = base64.b64decode(content["content"]).decode("utf-8")
        return json.loads(file_content), content["sha"]
    elif response.status_code == 404:
        # Als het bestand nog niet bestaat op GitHub, starten we met een lege structuur
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

def list_opstelling_datums(data):
    if "opstellingen" in data and data["opstellingen"]:
        return sorted(list(data["opstellingen"].keys()), reverse=True)
    return []

# --- DATA INLADEN ---
data, file_sha = laad_data_van_github()

# Zorg dat de juiste mappen altijd correct aanwezig zijn
if "spelers" not in data: data["spelers"] = []
if "trainingen" not in data: data["trainingen"] = {}
if "opstellingen" not in data: data["opstellingen"] = {}

# ─── CSS ──────────────────────────────────────────────────────────────────────
# ─── CSS STYLING ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Inter:wght@400;600;700&display=swap');
@@ -70,7 +104,6 @@ def list_opstelling_datums(data):

section[data-testid="stSidebar"] { display: none !important; }

/* Koppen */
h1, h2, h3,
.stApp h1, .stApp h2, .stApp h3,
[data-testid="stMarkdown"] h1,
@@ -93,7 +126,6 @@ def list_opstelling_datums(data):
    -webkit-text-fill-color: var(--oranje) !important;
}

/* Labels & tekst */
label, p, span,
[data-testid="stWidgetLabel"],
[data-testid="stExpander"] > details > summary,
@@ -110,7 +142,6 @@ def list_opstelling_datums(data):
    font-weight: 600 !important;
}

/* Inputs */
input, textarea,
.stTextInput input, .stNumberInput input, .stDateInput input {
    color: var(--tekst) !important;
@@ -128,7 +159,6 @@ def list_opstelling_datums(data):
[data-baseweb="menu"] li { color: var(--tekst) !important; background: var(--bg) !important; }
[data-baseweb="menu"] li:hover { background: var(--oranje-dim) !important; }

/* Multiselect tags */
[data-baseweb="tag"] {
    background-color: var(--oranje-dim) !important;
    border: 1px solid var(--oranje) !important;
@@ -141,7 +171,6 @@ def list_opstelling_datums(data):
}
[data-baseweb="tag"] svg { fill: var(--oranje) !important; }

/* Knoppen */
.stButton > button {
    font-family: 'Inter', sans-serif !important;
    font-weight: 700 !important;
@@ -163,14 +192,12 @@ def list_opstelling_datums(data):
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
@@ -189,7 +216,6 @@ def list_opstelling_datums(data):
    -webkit-text-fill-color: #FFFFFF !important;
}

/* Custom componenten */
.stat-card {
    background: var(--bg-subtle); border: 1px solid var(--rand);
    border-top: 4px solid var(--oranje); border-radius: 8px;
@@ -241,26 +267,23 @@ def list_opstelling_datums(data):
</style>
""", unsafe_allow_html=True)

# ─── Header + navigatie ────────────────────────────────────────────────────────
# ─── HEADER & NAVIGATIE ───────────────────────────────────────────────────────
st.markdown("# ⚽ VOETBAL DASHBOARD BV O19-1")
c1, c2, c3, _ = st.columns([1, 1, 1, 2])
with c1:
    if st.button("👥 Team", use_container_width=True,
                 type="primary" if st.session_state.page == "team" else "secondary"):
    if st.button("👥 Team", use_container_width=True, type="primary" if st.session_state.page == "team" else "secondary"):
        st.session_state.page = "team"; st.session_state.edit_speler = None; st.rerun()
with c2:
    if st.button("📋 Aanwezigheid", use_container_width=True,
                 type="primary" if st.session_state.page == "aanwezigheid" else "secondary"):
    if st.button("📋 Aanwezigheid", use_container_width=True, type="primary" if st.session_state.page == "aanwezigheid" else "secondary"):
        st.session_state.page = "aanwezigheid"; st.session_state.edit_speler = None; st.rerun()
with c3:
    if st.button("🟠 Opstelling", use_container_width=True,
                 type="primary" if st.session_state.page == "opstelling" else "secondary"):
    if st.button("🟠 Opstelling", use_container_width=True, type="primary" if st.session_state.page == "opstelling" else "secondary"):
        st.session_state.page = "opstelling"; st.session_state.edit_speler = None; st.rerun()
st.markdown("---")

# ══════════════════════════════════════════════════════════════════════════════
# ==============================================================================
# PAGINA 1 — TEAM
# ══════════════════════════════════════════════════════════════════════════════
# ==============================================================================
if st.session_state.page == "team":
    st.markdown("## 👥 Teambeheer")
    with st.expander("➕ Nieuwe speler toevoegen", expanded=not bool(data["spelers"])):
@@ -274,7 +297,7 @@ def list_opstelling_datums(data):
                    st.error("Speler bestaat al!")
                else:
                    data["spelers"].append({"naam": nieuwe_naam.strip(), "positie": nieuwe_positie, "nummer": int(nieuwe_nummer)})
                    save_data(data); st.success(f"✅ {nieuwe_naam.strip()} toegevoegd!"); st.rerun()
                    sla_data_op_naar_github(data, file_sha)
            else:
                st.warning("Vul een naam in.")

@@ -317,7 +340,7 @@ def list_opstelling_datums(data):
                                                        sessie[key].remove(naam); sessie[key].append(nieuwe_naam_e)
                                    s["naam"]=nieuwe_naam_e; s["positie"]=nieuwe_pos_e; s["nummer"]=int(nieuwe_nr_e)
                                    break
                            save_data(data); st.session_state.edit_speler=None; st.success("✅ Bijgewerkt!"); st.rerun()
                            sla_data_op_naar_github(data, file_sha)
                with bc2:
                    if st.button("❌ Annuleren", key=f"cancel_{naam}", use_container_width=True):
                        st.session_state.edit_speler=None; st.rerun()
@@ -338,11 +361,11 @@ def list_opstelling_datums(data):
                    with bc2:
                        if st.button("🗑️", key=f"del_{naam}", use_container_width=True, help="Verwijderen"):
                            data["spelers"]=[s for s in data["spelers"] if s["naam"]!=naam]
                            save_data(data); st.rerun()
                            sla_data_op_naar_github(data, file_sha)

# ══════════════════════════════════════════════════════════════════════════════
# ==============================================================================
# PAGINA 2 — AANWEZIGHEID
# ══════════════════════════════════════════════════════════════════════════════
# ==============================================================================
elif st.session_state.page == "aanwezigheid":
    echte_wedstrijden  = {k:v for k,v in data["trainingen"].items() if not k.endswith("_notitie")}
    totaal_spelers     = len(data["spelers"])
@@ -378,7 +401,7 @@ def speler_stats(naam):
        if not data["spelers"]:
            st.info("Voeg eerst spelers toe via het Team-menu.")
        else:
            wedstrijd_datum   = st.date_input("📅 Datum wedstrijd", value=date.today())
            wedstrijd_datum   = st.date_input("📅 Datum wedstrijd", value=datetime.date.today())
            datum_key         = str(wedstrijd_datum)
            wedstrijd_notitie = st.text_input("📝 Notitie (optioneel)", placeholder="Bijv. Uitwedstrijd, bekerwedstrijd...")
            bestaande         = echte_wedstrijden.get(datum_key, {"afwezig":[],"blessure":[]})
@@ -399,10 +422,10 @@ def speler_stats(naam):
                for n in afwezig_selectie: st.markdown(f'<span class="badge badge-grijs">{n}</span>', unsafe_allow_html=True)
            with st.expander(f"🩹 Geblesseerd ({len(blessure_selectie)})"):
                for n in blessure_selectie: st.markdown(f'<span class="badge badge-oranje">🩹 {n}</span>', unsafe_allow_html=True)
            if st.button("💾 Opslaan", type="primary"):
            if st.button("💾 Opslaan", type="primary", key="save_attendance_btn"):
                data["trainingen"][datum_key] = {"afwezig":afwezig_selectie,"blessure":blessure_selectie}
                if wedstrijd_notitie: data["trainingen"][f"{datum_key}_notitie"] = wedstrijd_notitie
                save_data(data); st.success(f"✅ Aanwezigheid voor {wedstrijd_datum.strftime('%d %B %Y')} opgeslagen!")
                sla_data_op_naar_github(data, file_sha)

    with tab2:
        st.markdown("## 📊 Aanwezigheidsoverzicht")
@@ -414,21 +437,21 @@ def speler_stats(naam):
            for naam in speler_namen:
                aanwezig, afwezig, blessure = speler_stats(naam)
                row = {"Speler": naam}
                for datum in datum_lijst:
                    sessie=echte_wedstrijden[datum]
                    row[datum]="🩹" if naam in sessie.get("blessure",[]) else ("❌" if naam in sessie.get("afwezig",[]) else "✅")
                for d in datum_lijst:
                    sessie=echte_wedstrijden[d]
                    row[d]="🩹" if naam in sessie.get("blessure",[]) else ("❌" if naam in sessie.get("afwezig",[]) else "✅")
                row["✅"]=aanwezig; row["❌"]=afwezig; row["🩹"]=blessure
                row["%"]=f"{round(aanwezig/len(datum_lijst)*100)}%" if datum_lijst else "0%"
                rows.append(row)
            st.dataframe(pd.DataFrame(rows), use_container_width=True, height=400)
            namen=[r["Speler"] for r in rows]
            st.markdown("**✅ Aanwezig**"); st.bar_chart(pd.DataFrame({"Aanwezig":[r["✅"] for r in rows]},index=namen))
            st.markdown("**❌ Afwezig**");  st.bar_chart(pd.DataFrame({"Afwezig": [r["❌"] for r in rows]},index=namen))
            st.markdown("**❌ Afwezig**");  st.bar_chart(pd.DataFrame({"Refused": [r["❌"] for r in rows]},index=namen))
            st.markdown("**🩹 Geblesseerd**"); st.bar_chart(pd.DataFrame({"Blessure":[r["🩹"] for r in rows]},index=namen))
            wedstrijd_data=[]
            for datum in sorted(echte_wedstrijden.keys()):
                sessie=echte_wedstrijden[datum]; n_af=len(sessie.get("afwezig",[])); n_bl=len(sessie.get("blessure",[]))
                wedstrijd_data.append({"Datum":datum,"✅":totaal_spelers-n_af-n_bl,"❌":n_af,"🩹":n_bl,"Notitie":data["trainingen"].get(f"{datum}_notitie","")})
            for d in sorted(echte_wedstrijden.keys()):
                sessie=echte_wedstrijden[d]; n_af=len(sessie.get("afwezig",[])); n_bl=len(sessie.get("blessure",[]))
                wedstrijd_data.append({"Datum":d,"✅":totaal_spelers-n_af-n_bl,"❌":n_af,"🩹":n_bl,"Notitie":data["trainingen"].get(f"{d}_notitie","")})
            st.markdown("### 📅 Overzicht per wedstrijd")
            st.dataframe(pd.DataFrame(wedstrijd_data).set_index("Datum"), use_container_width=True)
            st.markdown("### 📈 Trend per wedstrijd")
@@ -455,197 +478,133 @@ def speler_stats(naam):
                        <div style="color:#555;font-size:.78rem">{aanwezig}/{totaal} wedstrijden aanwezig</div>
                    </div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# ==============================================================================
# PAGINA 3 — OPSTELLING
#
# Hoe het opslaan werkt:
#   1. Het iframe-veld stuurt posities + formatie via window.parent.postMessage.
#   2. Een <script> buiten het iframe luistert, schrijft de waarden naar
#      verborgen <input>-elementen die Streamlit NIET ziet — we hoeven ze alleen
#      te lezen via st.session_state nadat de gebruiker op de ECHTE Streamlit-
#      knop "💾 Opstelling opslaan" klikt.
#   3. Die knop triggert een rerun; de payload zit al in st.session_state via
#      een Streamlit-component (st.components.v1.html met returnValue).
#
# Eenvoudiger dan bovenstaande: we gebruiken st.components.v1.html met
# bidirectionele communicatie via de Streamlit-component API (setFrameHeight /
# sendDataToPython zijn niet beschikbaar in community Streamlit). 
#
# ECHTE oplossing die wél werkt in standaard Streamlit:
#   - JavaScript slaat posities op in de browser (window.sessionStorage).
#   - Een Streamlit-knop buiten het iframe triggert een rerun.
#   - Bij die rerun leest een tweede kleine HTML-component sessionStorage uit
#     en toont de JSON, die Streamlit opvangt via st.components.v1.html
#     met een return-waarde — maar dat vereist een custom component.
#
# SIMPELSTE betrouwbare aanpak zonder custom component:
#   - Streamlit number_input / text_input als proxy werkt niet betrouwbaar.
#   - We lossen het op met een Streamlit-FORM + een JSON-text_area die de
#     gebruiker NIET ziet (height=0 werkt niet, maar label_visibility="hidden"
#     + disabled=True met een default die we updaten via JS … ook niet).
#
# ── DEFINITIEVE aanpak: posities worden in sessionStorage opgeslagen door JS.
#    Een aparte mini-HTML-component (40px hoog) leest sessionStorage elke
#    seconde uit en schrijft de waarde naar een Streamlit text_input via
#    de React synthetic event — dit is de enige manier die consistent werkt. ──
# ══════════════════════════════════════════════════════════════════════════════
# ==============================================================================
else:
    st.markdown("## 🟠 Opstelling per wedstrijd")

    if not data["spelers"]:
        st.warning("Voeg eerst spelers toe via het Team-menu.")
        st.stop()

    # ── Datumkiezer + dropdown in één rij ─────────────────────────────────────
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
                try:    lbl = datetime.strptime(dk, "%Y-%m-%d").strftime("%d %B %Y")
                except: lbl = dk
                nt = data.get("trainingen", {}).get(f"{dk}_notitie", "")
                n  = len(data["opstelling"][dk].get("posities", {}))
                return f"{lbl}{' — '+nt if nt else ''} ({n} spelers)"

            opties   = ["— Kies opgeslagen opstelling —"] + alle_opst_keys
            labels   = ["— Kies opgeslagen opstelling —"] + [datum_label(dk) for dk in alle_opst_keys]
            gekozen  = st.selectbox("📂 Opgeslagen opstellingen", labels, key="opst_zoek")
            if gekozen != labels[0]:
                idx = labels.index(gekozen)
                dk  = opties[idx]
                nieuwe_datum = datetime.strptime(dk, "%Y-%m-%d").date()
                if nieuwe_datum != st.session_state.opstelling_datum:
                    st.session_state.opstelling_datum = nieuwe_datum
                    st.session_state.opst_posities    = {}
                    st.session_state.opst_formatie    = ""
                    st.rerun()

    datum_key   = str(st.session_state.opstelling_datum)
    datum_label_str = st.session_state.opstelling_datum.strftime("%d %B %Y")

    # Haal bestaande op (als die er is)
    bestaande_entry = data["opstelling"].get(datum_key, {})
    posities_init   = bestaande_entry.get("posities", {}) if isinstance(bestaande_entry, dict) else {}
    formatie_init   = bestaande_entry.get("formatie", "")  if isinstance(bestaande_entry, dict) else ""

    heeft_opgeslagen = datum_key in data["opstelling"]
    notitie = data.get("trainingen", {}).get(f"{datum_key}_notitie", "")
    if notitie:
        st.caption(f"📝 {notitie}")
    if heeft_opgeslagen:
        st.success(f"Opgeslagen opstelling voor **{datum_label_str}** — {len(posities_init)} spelers op het veld.")
    else:
        st.info(f"Nog geen opstelling voor **{datum_label_str}**.")

    # ── Opslaan-knop BOVEN het iframe ─────────────────────────────────────────
    # De knop leest de posities die JavaScript in st.session_state heeft geschreven
    # via de postMessage-brug hieronder.
    sk1, sk2, sk3 = st.columns([2, 1, 1])
    with sk1:
        pass  # placeholder voor uitlijning
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
                    nt = data.get("trainingen", {}).get(f"{dk}_notitie", "")
                    n  = len(data["opstellingen"][dk].get("posities", {}))
                    return f"{lbl}{' — '+nt if nt else ''} ({n} spelers)"

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
        notitie = data.get("trainingen", {}).get(f"{datum_key}_notitie", "")
        if notitie:
            st.caption(f"📝 {notitie}")
        if heeft_opgeslagen:
            st.success(f"Opgeslagen opstelling voor **{datum_label_str}** — {len(posities_init)} spelers op het veld.")
        else:
            data["opstelling"][datum_key] = {
                "posities": posities_te_slaan,
                "formatie": formatie_te_slaan,
            }
            save_data(data)
            st.success(f"✅ Opstelling opgeslagen voor {datum_label_str} ({len(posities_te_slaan)} spelers)!")
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

    # ── postMessage-ontvanger: luistert buiten het iframe ─────────────────────
    # Dit kleine script leeft in de Streamlit-pagina zelf (niet in het iframe)
    # en vangt berichten op die het veld-iframe verstuurt.
    # Het schrijft ze naar Streamlit session_state via een verborgen query-trick:
    # omdat we geen custom component hebben, slaan we ze op in window.__opst__
    # en lezen ze uit via een tweede st.components.v1.html die de waarde retourneert.
    #
    # — Eerlijkheidshalve: de enige 100% betrouwbare brug zonder custom component
    #   is dat de gebruiker zelf de Opslaan-knop klikt NADAT het veld klaar is.
    #   We combineren dit: JS slaat posities op in window.parent.__opst_state__,
    #   en een aparte reader-component leest dat uit en zet het in een Streamlit
    #   text_input via de React trick.
    #
    # Nieuwe aanpak: één enkel iframe dat ALLE interactie bevat, inclusief een
    # eigen Opslaan-knop. Die knop stuurt via postMessage naar window.parent.
    # window.parent heeft een event listener die de data opslaat in een
    # ONZICHTBAAR text_input dat Streamlit wél ziet.
    # Het text_input staat BOVEN dit punt zodat Streamlit het al kent.

    # ── De verborgen brug-input (écht verborgen via CSS) ──────────────────────
    # We gebruiken een st.text_input met een uniek label en verbergen hem met CSS.
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

    # Verwerk inkomende brug-waarde
    if brug_waarde and brug_waarde.strip():
        try:
            payload = json.loads(brug_waarde)
            st.session_state.opst_posities = payload.get("posities", {})
            st.session_state.opst_formatie = payload.get("formatie", "")
            # Wis de brug-input zodat hij niet opnieuw verwerkt wordt
            st.session_state.opst_brug = ""
        except json.JSONDecodeError:
            pass

    # ── Veld-iframe ────────────────────────────────────────────────────────────
    spelers_json      = json.dumps(data["spelers"], ensure_ascii=False)
    posities_json_str = json.dumps(posities_init, ensure_ascii=False)
    formatie_json_str = json.dumps(formatie_init, ensure_ascii=False)
    datum_json        = json.dumps(datum_key, ensure_ascii=False)

    veld_html = f"""<!DOCTYPE html>
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

        # ── VERBORGEN BRUG (CSS + INPUT) ──────────────────────────────────────
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

        # ── INTERACTIEF SPEELVELD HTML ────────────────────────────────────────
        spelers_json      = json.dumps(data["spelers"], ensure_ascii=False)
        posities_json_str = json.dumps(posities_init, ensure_ascii=False)
        formatie_json_str = json.dumps(formatie_init, ensure_ascii=False)
        datum_json        = json.dumps(datum_key, ensure_ascii=False)

        veld_html = f"""<!DOCTYPE html>
<html lang="nl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<style>
* {{ box-sizing:border-box; margin:0; padding:0; }}
body {{ background:#FFF; font-family:'Inter',sans-serif; color:#111; padding:8px; }}
.wrap {{ display:flex; flex-direction:column; gap:12px; max-width:700px; margin:0 auto; }}
h3 {{ font-family:'Bebas Neue',cursive; color:#111; font-size:1.2rem; letter-spacing:2px; }}

/* Veld */
.veld-wrap {{ width:100%; aspect-ratio:68/105; max-height:65vh; margin:0 auto; position:relative; }}
#veld {{
    width:100%; height:100%;
@@ -660,8 +619,6 @@ def datum_label(dk):
.gb,.go {{ position:absolute; left:35%; right:35%; height:4%; border:2px solid rgba(255,255,255,.8); background:rgba(255,255,255,.1); pointer-events:none; }}
.gb {{ top:0; border-top:none; }} .go {{ bottom:0; border-bottom:none; }}
.gs {{ position:absolute; top:0; bottom:0; width:9.09%; background:rgba(0,0,0,.08); pointer-events:none; }}

/* Tokens */
.token {{ position:absolute; transform:translate(-50%,-50%); cursor:grab; touch-action:none; user-select:none; z-index:10; display:flex; flex-direction:column; align-items:center; gap:2px; }}
.token:active {{ cursor:grabbing; }}
.tc {{
@@ -677,8 +634,6 @@ def datum_label(dk):
    max-width:clamp(44px,12vw,64px); overflow:hidden; text-overflow:ellipsis; text-align:center;
    border:1px solid #C44A00;
}}

/* Bank */
.bank {{ background:#F5F5F5; border:1px solid #BBB; border-top:4px solid #C44A00; border-radius:8px; padding:10px; }}
.bank-titel {{ font-family:'Bebas Neue',cursive; color:#333; letter-spacing:1px; font-size:.95rem; margin-bottom:8px; }}
.bank-lijst {{ display:flex; flex-wrap:wrap; gap:6px; }}
@@ -696,20 +651,12 @@ def datum_label(dk):
    font-family:'Bebas Neue',cursive; font-size:12px;
    display:flex; align-items:center; justify-content:center; flex-shrink:0;
}}
.hint {{ color:#C44A00; font-size:.8rem; margin-top:6px; width:100%; cursor:pointer; text-decoration:underline; font-weight:600; }}

/* Formatie selector */
.form-row {{ display:flex; align-items:center; gap:10px; flex-wrap:wrap; }}
.fsel {{
    background:#fff; color:#111; border:2px solid #666; border-radius:8px;
    padding:7px 11px; font-size:.88rem; cursor:pointer; flex:1; min-width:130px;
}}
.fsel:focus {{ outline:3px solid #C44A00; outline-offset:2px; }}

/* Statusbalk (alleen in iframe, geen Streamlit-knop meer nodig hier) */
.status {{ font-family:'Bebas Neue',cursive; letter-spacing:1px; font-size:.9rem; min-height:1.3rem; font-weight:700; }}
.status.ok {{ color:#1B6B38; }}
.status.err {{ color:#CC0000; }}
</style>
<link href="https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Inter:wght@400;600;700&display=swap" rel="stylesheet">
</head>
@@ -727,7 +674,6 @@ def datum_label(dk):
      <option value="3-4-3">3-4-3</option>
    </select>
  </div>

  <div class="veld-wrap">
    <div id="veld">
      <div class="cirkel"></div>
@@ -738,26 +684,19 @@ def datum_label(dk):
      <div class="gs" style="left:72.72%"></div><div class="gs" style="left:90.9%"></div>
    </div>
  </div>

  <div class="bank">
    <div class="bank-titel">🪑 BANK — klik speler, tik dan op het veld</div>
    <div class="bank-lijst" id="bank"></div>
  </div>

  <div class="status" id="status"></div>
</div>

<script>
const SPELERS  = {spelers_json};
const DATUM    = {datum_json};
const INIT_POS = {posities_json_str};
const INIT_FMT = {formatie_json_str};

let posities   = structuredClone(INIT_POS);
let plaatsMode = null;

// ── Stuur posities naar Streamlit via postMessage ──────────────────────────
// window.parent ontvangt dit en schrijft het naar de Streamlit text_input.
function stuurNaarStreamlit() {{
  const payload = JSON.stringify({{
    posities: posities,
@@ -766,19 +705,8 @@ def datum_label(dk):
  window.parent.postMessage({{ type: 'opst_update', payload }}, '*');
}}

// Stuur automatisch bij elke wijziging (plaatsen, slepen, verwijderen, formatie)
function onChange() {{
  stuurNaarStreamlit();
  toonStatus('');
}}

function toonStatus(msg, ok=true) {{
  const el = document.getElementById('status');
  el.textContent = msg;
  el.className = 'status ' + (ok ? 'ok' : 'err');
}}
function onChange() {{ stuurNaarStreamlit(); }}

// ── Bank ────────────────────────────────────────────────────────────────────
function renderBank() {{
  const lijst = document.getElementById('bank');
  lijst.innerHTML = '';
@@ -791,16 +719,8 @@ def datum_label(dk):
    if (!opVeld) div.onclick = () => {{ plaatsMode=s.naam; renderBank(); }};
    lijst.appendChild(div);
  }});
  if (plaatsMode) {{
    const hint = document.createElement('div');
    hint.className = 'hint';
    hint.textContent = `Tik op het veld om ${{plaatsMode}} te plaatsen · klik hier om te annuleren`;
    hint.onclick = () => {{ plaatsMode=null; renderBank(); }};
    lijst.appendChild(hint);
  }}
}}

// ── Veld ────────────────────────────────────────────────────────────────────
document.getElementById('veld').addEventListener('click', function(e) {{
  if (!plaatsMode) return;
  const r = this.getBoundingClientRect();
@@ -817,42 +737,24 @@ def datum_label(dk):
    tok.className='token'; tok.style.left=pos.x+'%'; tok.style.top=pos.y+'%';
    tok.innerHTML=`<div class="tc">${{sp.nummer}}</div><div class="tn">${{naam.split(' ')[0]}}</div>`;
    tok.addEventListener('dblclick', e=>{{ e.stopPropagation(); delete posities[naam]; renderBank(); renderVeld(); onChange(); }});

    // Muis drag
    let dr=false,sX,sY,sL,sT;
    tok.addEventListener('mousedown',e=>{{ if(plaatsMode)return; e.preventDefault(); dr=true; sX=e.clientX;sY=e.clientY;sL=pos.x;sT=pos.y; tok.classList.add('dragging'); }});
    tok.addEventListener('mousedown',e=>{{ if(plaatsMode)return; e.preventDefault(); dr=true; sX=e.clientX;sY=e.clientY;sL=pos.x;sT=pos.y; }});
    document.addEventListener('mousemove',e=>{{
      if(!dr)return; const r=veld.getBoundingClientRect();
      const nx=Math.max(2,Math.min(98,sL+((e.clientX-sX)/r.width)*100));
      const ny=Math.max(2,Math.min(98,sT+((e.clientY-sY)/r.height)*100));
      tok.style.left=nx+'%'; tok.style.top=ny+'%'; posities[naam]={{x:nx,y:ny}};
      posities[naam]={{x:Math.max(2,Math.min(98,sL+((e.clientX-sX)/r.width)*100)), y:Math.max(2,Math.min(98,sT+((e.clientY-sY)/r.height)*100))}};
      tok.style.left=posities[naam].x+'%'; tok.style.top=posities[naam].y+'%';
    }});
    document.addEventListener('mouseup',()=>{{ if(dr){{dr=false;tok.classList.remove('dragging');onChange();}} }});

    // Touch drag
    let tX,tY,tL,tT;
    tok.addEventListener('touchstart',e=>{{ if(plaatsMode)return; const t=e.touches[0]; tX=t.clientX;tY=t.clientY;tL=pos.x;tT=pos.y; tok.classList.add('dragging'); }},{{passive:true}});
    tok.addEventListener('touchmove',e=>{{
      e.preventDefault(); const t=e.touches[0]; const r=veld.getBoundingClientRect();
      const nx=Math.max(2,Math.min(98,tL+((t.clientX-tX)/r.width)*100));
      const ny=Math.max(2,Math.min(98,tT+((t.clientY-tY)/r.height)*100));
      tok.style.left=nx+'%'; tok.style.top=ny+'%'; posities[naam]={{x:nx,y:ny}};
    }},{{passive:false}});
    tok.addEventListener('touchend',()=>{{ tok.classList.remove('dragging'); onChange(); }});

    document.addEventListener('mouseup',()=>{{ if(dr){{dr=false;onChange();}} }});
    veld.appendChild(tok);
  }});
}}

// ── Formatie ────────────────────────────────────────────────────────────────
const FORMATIES = {{
  '4-3-3':   [[50,88],[18,72],[38,72],[62,72],[82,72],[30,52],[50,48],[70,52],[20,28],[50,22],[80,28]],
  '4-4-2':   [[50,88],[18,72],[38,72],[62,72],[82,72],[18,52],[38,52],[62,52],[82,52],[35,25],[65,25]],
  '4-2-3-1': [[50,88],[18,72],[38,72],[62,72],[82,72],[35,58],[65,58],[20,40],[50,38],[80,40],[50,18]],
  '3-5-2':   [[50,88],[25,72],[50,70],[75,72],[15,52],[35,50],[55,50],[75,50],[90,52],[35,25],[65,25]],
  '5-3-2':   [[50,88],[10,72],[28,72],[50,68],[72,72],[90,72],[25,50],[50,48],[75,50],[35,25],[65,25]],
  '3-4-3':   [[50,88],[25,72],[50,70],[75,72],[18,52],[40,50],[60,50],[82,52],[20,28],[50,22],[80,28]],
}};

function zetFormatie() {{
  const f=document.getElementById('formatie').value; if(!f)return;
  const sorted=[...SPELERS].sort((a,b)=>a.nummer-b.nummer).slice(0,11);
@@ -861,76 +763,51 @@ def datum_label(dk):
  renderBank(); renderVeld(); onChange();
}}

// ── Init ────────────────────────────────────────────────────────────────────
document.getElementById('formatie').value = INIT_FMT || '';
renderBank();
renderVeld();
// Stuur initiële staat direct door zodat Streamlit hem kent vóór eerste opslaan
renderBank(); renderVeld();
setTimeout(stuurNaarStreamlit, 300);
</script>
</body>
</html>"""

    # ── postMessage-ontvanger in de Streamlit-pagina ──────────────────────────
    # Dit script leeft BUITEN het iframe en vangt postMessage op.
    # Het schrijft de payload naar het verborgen Streamlit text_input via
    # de React native value setter — de enige methode die Streamlit detecteert.
    ontvanger_html = """
<script>
(function() {
  // Luister naar berichten van het veld-iframe
  window.addEventListener('message', function(event) {
    if (!event.data || event.data.type !== 'opst_update') return;
    const payload = event.data.payload;

    // Zoek het verborgen Streamlit text_input op via aria-label
    const input = window.parent.document.querySelector(
      'input[aria-label="opst_brug_input"]'
    );
    if (!input) return;

    // Schrijf via de React native setter zodat Streamlit de change detecteert
    const setter = Object.getOwnPropertyDescriptor(
      window.parent.HTMLInputElement.prototype, 'value'
    ).set;
    setter.call(input, payload);
    input.dispatchEvent(new Event('input', { bubbles: true }));
  });
})();
</script>
"""
    # De ontvanger moet in de Streamlit-pagina leven, niet in het iframe.
    # st.markdown met unsafe_allow_html staat geen <script> toe.
    # We gebruiken een mini st.components.v1.html (0px hoog) voor de ontvanger.
    st.components.v1.html(ontvanger_html, height=0)

    # Het eigenlijke veld-iframe
    st.components.v1.html(veld_html, height=820, scrolling=True)

    st.caption("💡 Klik een speler op de bank, tik dan op het veld. Sleep om te verplaatsen. Dubbelklik op een token om te verwijderen. Klik **Opstelling opslaan** als je klaar bent.")

    # ── Archief: opgeslagen opstellingen ──────────────────────────────────────
    if alle_opst_keys:
        st.markdown("---")
        st.markdown("### 📚 Opgeslagen opstellingen")
        for dk in alle_opst_keys:
            entry = data["opstelling"].get(dk, {})
            n_sp  = len(entry.get("posities", {}))
            fmt   = entry.get("formatie", "")
            try:    titel = datetime.strptime(dk, "%Y-%m-%d").strftime("%d %B %Y")
            except: titel = dk
            nt = data.get("trainingen", {}).get(f"{dk}_notitie", "")
            if nt: titel += f" — {nt}"
            ac1, ac2, ac3 = st.columns([4, 1, 1])
            with ac1:
                st.markdown(f"**{titel}** · {n_sp} spelers{' · '+fmt if fmt else ''}")
            with ac2:
                if st.button("👁️ Laden", key=f"load_{dk}", use_container_width=True):
                    st.session_state.opstelling_datum = datetime.strptime(dk, "%Y-%m-%d").date()
                    st.session_state.opst_posities    = entry.get("posities", {})
                    st.session_state.opst_formatie    = entry.get("formatie", "")
                    st.rerun()
            with ac3:
                if st.button("🗑️", key=f"del_{dk}", help="Verwijderen", use_container_width=True):
                    del data["opstelling"][dk]
                    save_data(data); st.rerun()
        ontvanger_html = """
        <script>
        window.addEventListener('message', function(event) {
          if (!event.data || event.data.type !== 'opst_update') return;
          const payload = event.data.payload;
          const input = window.parent.document.querySelector('input[aria-label="opst_brug_input"]');
          if (!input) return;
          const setter = Object.getOwnPropertyDescriptor(window.parent.HTMLInputElement.prototype, 'value').set;
          setter.call(input, payload);
          input.dispatchEvent(new Event('input', { bubbles: true }));
        });
        </script>
        """
        st.components.v1.html(ontvanger_html, height=0)
        st.components.v1.html(veld_html, height=820, scrolling=True)

        st.caption("💡 Klik een speler op de bank, tik dan op het veld. Sleep om te verplaatsen. Dubbelklik om te verwijderen.")

        # ── INTERACTIEF ARCHIEF ONDERAAN ──────────────────────────────────────
        if alle_opst_keys:
            st.markdown("---")
            st.markdown("### 📚 Opgeslagen opstellingen")
            for dk in alle_opst_keys:
                entry = data["opstellingen"].get(dk, {})
                n_sp  = len(entry.get("posities", {}))
                fmt   = entry.get("formatie", "")
                try:    titel = datetime.datetime.strptime(dk, "%Y-%m-%d").strftime("%d %B %Y")
                except: titel = dk
                ac1, ac2, ac3 = st.columns([4, 1, 1])
                with ac1:
                    st.markdown(f"**{titel}** · {n_sp} spelers{' · '+fmt if fmt else ''}")
                with ac2:
                    if st.button("👁️ Laden", key=f"load_{dk}", use_container_width=True):
                        st.session_state.opstelling_datum = datetime.datetime.strptime(dk, "%Y-%m-%d").date()
                        st.session_state.opst_posities    = entry.get("posities", {})
                        st.session_state.opst_formatie    = entry.get("formatie", "")
                        st.rerun()
                with ac3:
                    if st.button("🗑️", key=f"del_{dk}", help="Verwijderen", use_container_width=True):
                        del data["opstellingen"][dk]
                        sla_data_op_naar_github(data, file_sha)
