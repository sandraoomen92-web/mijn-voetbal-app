import streamlit as st
import pandas as pd
import requests
import json
import base64
import datetime

# --- CONFIGURATIE PAGINA ---
st.set_page_config(page_title="⚽ BV O19-1 Dashboard", page_icon="⚽", layout="wide")

# --- GITHUB CONFIGURATIE VIA SECRETS ---
GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
REPO = st.secrets["GITHUB_REPO"]  # Bijv: sandraoomen92-web/mijn-voetbal-app
FILE_PATH = "voetbal_data.json"
URL = f"https://api.github.com/repos/{REPO}/contents/{FILE_PATH}"
HEADERS = {"Authorization": f"token {GITHUB_TOKEN}"}

# --- INITIALISATIE SESSION STATE ---
if "page" not in st.session_state:
    st.session_state.page = "team"
if "edit_speler" not in st.session_state:
    st.session_state.edit_speler = None
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

# ─── CSS STYLING ──────────────────────────────────────────────────────────────
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

[data-testid="stAlert"] p,
[data-testid="stAlert"] span {
    color: var(--tekst) !important;
    -webkit-text-fill-color: var(--tekst) !important;
}

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
    -webkit-text-fill-color: #FFFFFF !important;
}

.stat-card {
    background: var(--bg-subtle); border: 1px solid var(--rand);
    border-top: 4px solid var(--oranje); border-radius: 8px;
    padding: clamp(10px,3vw,18px); text-align: center; margin-bottom: 10px;
}
.stat-card.dim { border-top-color: var(--rand-sterk); }
.stat-number {
    font-family: 'Bebas Neue', sans-serif;
    font-size: clamp(1.6rem,5vw,2.8rem);
    color: var(--oranje); line-height: 1.1; letter-spacing: 1px;
}
.stat-number.alt { color: var(--zwart); }
.stat-label {
    font-size: clamp(0.65rem,2vw,0.8rem); color: var(--tekst-zacht);
    text-transform: uppercase; letter-spacing: 1.5px; margin-top: 2px; font-weight: 700;
}
.team-row {
    display: flex; align-items: center; gap: 12px;
    background: var(--bg-subtle); border: 1px solid var(--rand);
    border-left: 4px solid var(--oranje); border-radius: 8px;
    padding: 10px 14px; margin-bottom: 8px;
}
.team-row:hover { background: var(--oranje-dim); }
.team-nr {
    width:36px; height:36px; border-radius:50%; background:var(--oranje); color:#FFF;
    font-family:'Bebas Neue',sans-serif; font-size:16px;
    display:flex; align-items:center; justify-content:center; flex-shrink:0;
}
.team-naam { font-weight:700; font-size:0.95rem; color:var(--tekst); }
.team-pos  { font-size:0.78rem; color:var(--tekst-zacht); }
.edit-box {
    background:var(--oranje-dim); border:2px solid var(--oranje);
    border-radius:10px; padding:16px; margin-bottom:10px;
}
.speler-card {
    background:var(--bg-subtle); border:1px solid var(--rand);
    border-top:4px solid var(--oranje); border-radius:8px;
    padding:14px; margin-bottom:10px;
}
.badge {
    display:inline-block; padding:3px 10px; border-radius:20px;
    font-size:0.78rem; font-weight:700; margin:2px 2px 4px 0;
}
.badge-oranje { background:var(--oranje-dim); color:var(--oranje); border:1px solid var(--oranje); }
.badge-grijs  { background:var(--bg-muted); color:var(--tekst-mid); border:1px solid var(--rand-sterk); }
.preview-naam { font-size:0.95rem; padding:4px 0; color:var(--tekst); font-weight:600; }
hr { border-color: var(--rand) !important; }
.stDataFrame { border:1px solid var(--rand); border-radius:8px; }
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

# ==============================================================================
# PAGINA 1 — TEAM
# ==============================================================================
if st.session_state.page == "team":
    st.markdown("## 👥 Teambeheer")
    with st.expander("➕ Nieuwe speler toevoegen", expanded=not bool(data["spelers"])):
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1: nieuwe_naam    = st.text_input("Naam", placeholder="Jan de Vries", key="nieuw_naam")
        with col2: nieuwe_positie = st.selectbox("Positie", ["Keeper","Verdediger","Middenvelder","Aanvaller"], key="nieuw_pos")
        with col3: nieuwe_nummer  = st.number_input("Rugnummer", min_value=1, max_value=99, value=1, key="nieuw_nr")
        if st.button("✅ Speler toevoegen", type="primary"):
            if nieuwe_naam.strip():
                if nieuwe_naam.strip() in [s["naam"] for s in data["spelers"]]:
                    st.error("Speler bestaat al!")
                else:
                    data["spelers"].append({"naam": nieuwe_naam.strip(), "positie": nieuwe_positie, "nummer": int(nieuwe_nummer)})
                    sla_data_op_naar_github(data, file_sha)
            else:
                st.warning("Vul een naam in.")

    st.markdown("---")
    st.markdown(f"### Spelerslijst ({len(data['spelers'])} spelers)")
    if not data["spelers"]:
        st.info("Nog geen spelers. Voeg hierboven je eerste speler toe.")
    else:
        pos_volgorde = {"Keeper":0,"Verdediger":1,"Middenvelder":2,"Aanvaller":3}
        pos_icons    = {"Keeper":"🧤","Verdediger":"🛡️","Middenvelder":"⚙️","Aanvaller":"⚡"}
        gesorteerd   = sorted(data["spelers"], key=lambda x: (pos_volgorde.get(x["positie"],9), x["nummer"]))
        for speler in gesorteerd:
            naam = speler["naam"]
            if st.session_state.edit_speler == naam:
                st.markdown('<div class="edit-box">', unsafe_allow_html=True)
                st.markdown(f"**✏️ {naam} bewerken**")
                ec1, ec2, ec3 = st.columns([2,1,1])
                with ec1: nieuwe_naam_e = st.text_input("Naam", value=naam, key=f"edit_naam_{naam}")
                with ec2:
                    pos_opties   = ["Keeper","Verdediger","Middenvelder","Aanvaller"]
                    nieuwe_pos_e = st.selectbox("Positie", pos_opties, index=pos_opties.index(speler["positie"]), key=f"edit_pos_{naam}")
                with ec3: nieuwe_nr_e = st.number_input("Rugnummer", min_value=1, max_value=99, value=speler["nummer"], key=f"edit_nr_{naam}")
                bc1, bc2 = st.columns(2)
                with bc1:
                    if st.button("💾 Opslaan", key=f"save_{naam}", type="primary", use_container_width=True):
                        nieuwe_naam_e = nieuwe_naam_e.strip()
                        andere_namen  = [s["naam"] for s in data["spelers"] if s["naam"] != naam]
                        if not nieuwe_naam_e:
                            st.error("Naam mag niet leeg zijn.")
                        elif nieuwe_naam_e in andere_namen:
                            st.error("Er bestaat al een speler met deze naam.")
                        else:
                            for s in data["spelers"]:
                                if s["naam"] == naam:
                                    if nieuwe_naam_e != naam:
                                        for sessie in data["trainingen"].values():
                                            if isinstance(sessie, dict):
                                                for key in ["afwezig","blessure"]:
                                                    if naam in sessie.get(key,[]):
                                                        sessie[key].remove(naam); sessie[key].append(nieuwe_naam_e)
                                    s["naam"]=nieuwe_naam_e; s["positie"]=nieuwe_pos_e; s["nummer"]=int(nieuwe_nr_e)
                                    break
                            sla_data_op_naar_github(data, file_sha)
                with bc2:
                    if st.button("❌ Annuleren", key=f"cancel_{naam}", use_container_width=True):
                        st.session_state.edit_speler=None; st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
            else:
                rc1, rc2 = st.columns([5,2])
                with rc1:
                    st.markdown(f"""<div class="team-row">
                        <div class="team-nr">{speler['nummer']}</div>
                        <div><div class="team-naam">{naam}</div>
                        <div class="team-pos">{pos_icons.get(speler['positie'],'⚽')} {speler['positie']}</div></div>
                    </div>""", unsafe_allow_html=True)
                with rc2:
                    bc1, bc2 = st.columns(2)
                    with bc1:
                        if st.button("✏️", key=f"edit_{naam}", use_container_width=True, help="Bewerken"):
                            st.session_state.edit_speler=naam; st.rerun()
                    with bc2:
                        if st.button("🗑️", key=f"del_{naam}", use_container_width=True, help="Verwijderen"):
                            data["spelers"]=[s for s in data["spelers"] if s["naam"]!=naam]
                            sla_data_op_naar_github(data, file_sha)

# ==============================================================================
# PAGINA 2 — AANWEZIGHEID
# ==============================================================================
elif st.session_state.page == "aanwezigheid":
    echte_wedstrijden  = {k:v for k,v in data["trainingen"].items() if not k.endswith("_notitie")}
    totaal_spelers     = len(data["spelers"])
    totaal_wedstrijden = len(echte_wedstrijden)
    speler_namen       = [s["naam"] for s in data["spelers"]]

    def speler_stats(naam):
        aanwezig=afwezig=blessure=0
        for sessie in echte_wedstrijden.values():
            if naam in sessie.get("blessure",[]): blessure+=1
            elif naam in sessie.get("afwezig",[]): afwezig+=1
            else: aanwezig+=1
        return aanwezig, afwezig, blessure

    if echte_wedstrijden and data["spelers"]:
        alle_pct         = [(totaal_spelers-len(s.get("afwezig",[]))-len(s.get("blessure",[])))/totaal_spelers*100 for s in echte_wedstrijden.values()]
        gem_aanwezigheid = round(sum(alle_pct)/len(alle_pct),1)
        gem_blessure     = round(sum(len(s.get("blessure",[])) for s in echte_wedstrijden.values())/totaal_wedstrijden,1)
    else:
        gem_aanwezigheid = gem_blessure = 0

    r1c1, r1c2 = st.columns(2)
    with r1c1: st.markdown(f'<div class="stat-card"><div class="stat-number">{totaal_spelers}</div><div class="stat-label">Spelers</div></div>', unsafe_allow_html=True)
    with r1c2: st.markdown(f'<div class="stat-card"><div class="stat-number alt">{totaal_wedstrijden}</div><div class="stat-label">Wedstrijden</div></div>', unsafe_allow_html=True)
    r2c1, r2c2 = st.columns(2)
    with r2c1: st.markdown(f'<div class="stat-card"><div class="stat-number">{gem_aanwezigheid}%</div><div class="stat-label">Gem. aanwezigheid</div></div>', unsafe_allow_html=True)
    with r2c2: st.markdown(f'<div class="stat-card dim"><div class="stat-number alt">{gem_blessure}</div><div class="stat-label">Gem. geblesseerd p/wedstrijd</div></div>', unsafe_allow_html=True)
    st.markdown("---")

    tab1, tab2, tab3 = st.tabs(["📋 Registreren","📊 Overzicht","👥 Per speler"])
    with tab1:
        st.markdown("## 📋 Aanwezigheid registreren")
        if not data["spelers"]:
            st.info("Voeg eerst spelers toe via het Team-menu.")
        else:
            wedstrijd_datum   = st.date_input("📅 Datum wedstrijd", value=datetime.date.today())
            datum_key         = str(wedstrijd_datum)
            wedstrijd_notitie = st.text_input("📝 Notitie (optioneel)", placeholder="Bijv. Uitwedstrijd, bekerwedstrijd...")
            bestaande         = echte_wedstrijden.get(datum_key, {"afwezig":[],"blessure":[]})
            st.markdown("### Wie is er afwezig?")
            st.markdown("**❌ Afwezig**")
            afwezig_selectie  = st.multiselect("Afwezig", options=speler_namen,
                default=[n for n in bestaande.get("afwezig",[]) if n in speler_namen],
                label_visibility="collapsed", key=f"afwezig_{datum_key}")
            st.markdown("**🩹 Geblesseerd**")
            blessure_selectie = st.multiselect("Geblesseerd", options=speler_namen,
                default=[n for n in bestaande.get("blessure",[]) if n in speler_namen],
                label_visibility="collapsed", key=f"blessure_{datum_key}")
            aanwezig_namen = [n for n in speler_namen if n not in afwezig_selectie and n not in blessure_selectie]
            st.markdown("---")
            with st.expander(f"✅ Aanwezig ({len(aanwezig_namen)})", expanded=True):
                for n in aanwezig_namen: st.markdown(f'<div class="preview-naam">🟠 {n}</div>', unsafe_allow_html=True)
            with st.expander(f"❌ Afwezig ({len(afwezig_selectie)})"):
                for n in afwezig_selectie: st.markdown(f'<span class="badge badge-grijs">{n}</span>', unsafe_allow_html=True)
            with st.expander(f"🩹 Geblesseerd ({len(blessure_selectie)})"):
                for n in blessure_selectie: st.markdown(f'<span class="badge badge-oranje">🩹 {n}</span>', unsafe_allow_html=True)
            if st.button("💾 Opslaan", type="primary", key="save_attendance_btn"):
                data["trainingen"][datum_key] = {"afwezig":afwezig_selectie,"blessure":blessure_selectie}
                if wedstrijd_notitie: data["trainingen"][f"{datum_key}_notitie"] = wedstrijd_notitie
                sla_data_op_naar_github(data, file_sha)

    with tab2:
        st.markdown("## 📊 Aanwezigheidsoverzicht")
        if not echte_wedstrijden or not data["spelers"]:
            st.info("Nog geen aanwezigheidsdata beschikbaar.")
        else:
            datum_lijst = sorted(echte_wedstrijden.keys(), reverse=True)
            rows = []
            for naam in speler_namen:
                aanwezig, afwezig, blessure = speler_stats(naam)
                row = {"Speler": naam}
                for d in datum_lijst:
                    sessie=echte_wedstrijden[d]
                    row[d]="🩹" if naam in sessie.get("blessure",[]) else ("❌" if naam in sessie.get("afwezig",[]) else "✅")
                row["✅"]=aanwezig; row["❌"]=afwezig; row["🩹"]=blessure
                row["%"]=f"{round(aanwezig/len(datum_lijst)*100)}%" if datum_lijst else "0%"
                rows.append(row)
            st.dataframe(pd.DataFrame(rows), use_container_width=True, height=400)
            namen=[r["Speler"] for r in rows]
            st.markdown("**✅ Aanwezig**"); st.bar_chart(pd.DataFrame({"Aanwezig":[r["✅"] for r in rows]},index=namen))
            st.markdown("**❌ Afwezig**");  st.bar_chart(pd.DataFrame({"Refused": [r["❌"] for r in rows]},index=namen))
            st.markdown("**🩹 Geblesseerd**"); st.bar_chart(pd.DataFrame({"Blessure":[r["🩹"] for r in rows]},index=namen))
            wedstrijd_data=[]
            for d in sorted(echte_wedstrijden.keys()):
                sessie=echte_wedstrijden[d]; n_af=len(sessie.get("afwezig",[])); n_bl=len(sessie.get("blessure",[]))
                wedstrijd_data.append({"Datum":d,"✅":totaal_spelers-n_af-n_bl,"❌":n_af,"🩹":n_bl,"Notitie":data["trainingen"].get(f"{d}_notitie","")})
            st.markdown("### 📅 Overzicht per wedstrijd")
            st.dataframe(pd.DataFrame(wedstrijd_data).set_index("Datum"), use_container_width=True)
            st.markdown("### 📈 Trend per wedstrijd")
            st.bar_chart(pd.DataFrame(wedstrijd_data).set_index("Datum")[["✅","❌","🩹"]])

    with tab3:
        st.markdown("## 👥 Per speler")
        if not data["spelers"]:
            st.info("Nog geen spelers.")
        else:
            cols=st.columns(2)
            for i, speler in enumerate(sorted(data["spelers"],key=lambda x:x["nummer"])):
                naam=speler["naam"]; aanwezig,afwezig,blessure=speler_stats(naam)
                totaal=len(echte_wedstrijden); pct=round(aanwezig/totaal*100) if totaal else 0
                with cols[i%2]:
                    st.markdown(f"""<div class="speler-card">
                        <div style="font-family:'Bebas Neue',sans-serif;font-size:1.15rem;color:#111;letter-spacing:.5px;font-weight:700">#{speler['nummer']} {naam}</div>
                        <div style="color:#555;font-size:.8rem;margin-bottom:8px">{speler['positie']}</div>
                        <span class="badge badge-oranje">✅ {aanwezig}x aanwezig</span><br>
                        <span class="badge badge-grijs">❌ {afwezig}x afwezig</span>
                        <span class="badge badge-grijs">🩹 {blessure}x geblesseerd</span>
                        <hr style="margin:8px 0">
                        <div style="color:var(--oranje);font-weight:700;font-size:1.1rem">{pct}%</div>
                        <div style="color:#555;font-size:.78rem">{aanwezig}/{totaal} wedstrijden aanwezig</div>
                    </div>""", unsafe_allow_html=True)

# ==============================================================================
# PAGINA 3 — OPSTELLING
# ==============================================================================
else:
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
        
        # HIER IS DE FORMATIE-BRUG HERSTELD:
        with st.empty():
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
.token {{ position:absolute; transform:translate(-50%,-50%); cursor:grab; touch-action:none; user-select:none; z-index:10; display:flex; flex-direction:column; align-items:center; gap:2px; }}
.token:active {{ cursor:grabbing; }}
.tc {{
    width:clamp(30px,7vw,42px); height:clamp(30px,7vw,42px); border-radius:50%;
    background:#C44A00; border:2.5px solid #fff; display:flex; align-items:center; justify-content:center;
    font-family:'Bebas Neue',cursive; font-size:clamp(11px,3vw,15px); color:#fff; font-weight:700;
    box-shadow:0 2px 8px rgba(196,74,0,.5); transition:box-shadow .15s;
}}
.token.dragging .tc {{ box-shadow:0 4px 18px rgba(196,74,0,.7); }}
.tn {{
    background:#fff; color:#111; font-weight:600; font-size:clamp(6px,1.8vw,9px);
    padding:1px 4px; border-radius:3px; white-space:nowrap;
    max-width:clamp(44px,12vw,64px); overflow:hidden; text-overflow:ellipsis; text-align:center;
    border:1px solid #C44A00;
}}
.bank {{ background:#F5F5F5; border:1px solid #BBB; border-top:4px solid #C44A00; border-radius:8px; padding:10px; }}
.bank-titel {{ font-family:'Bebas Neue',cursive; color:#333; letter-spacing:1px; font-size:.95rem; margin-bottom:8px; }}
.bank-lijst {{ display:flex; flex-wrap:wrap; gap:6px; }}
.bank-item {{
    display:flex; align-items:center
"""
