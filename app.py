import streamlit as st
import pandas as pd
from datetime import date, datetime
import json
import os

st.set_page_config(page_title="⚽ BV O19-1 Dashboard", page_icon="⚽", layout="wide")

DATA_FILE = "voetbal_data.json"

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
    -webkit-text-fill-color: #FFFFFF !important;
}

/* Custom componenten */
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

# ─── Header + navigatie ────────────────────────────────────────────────────────
st.markdown("# ⚽ VOETBAL DASHBOARD BV O19-1")
c1, c2, c3, _ = st.columns([1, 1, 1, 2])
with c1:
    if st.button("👥 Team", use_container_width=True,
                 type="primary" if st.session_state.page == "team" else "secondary"):
        st.session_state.page = "team"; st.session_state.edit_speler = None; st.rerun()
with c2:
    if st.button("📋 Aanwezigheid", use_container_width=True,
                 type="primary" if st.session_state.page == "aanwezigheid" else "secondary"):
        st.session_state.page = "aanwezigheid"; st.session_state.edit_speler = None; st.rerun()
with c3:
    if st.button("🟠 Opstelling", use_container_width=True,
                 type="primary" if st.session_state.page == "opstelling" else "secondary"):
        st.session_state.page = "opstelling"; st.session_state.edit_speler = None; st.rerun()
st.markdown("---")

# ══════════════════════════════════════════════════════════════════════════════
# PAGINA 1 — TEAM
# ══════════════════════════════════════════════════════════════════════════════
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
                    save_data(data); st.success(f"✅ {nieuwe_naam.strip()} toegevoegd!"); st.rerun()
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
                            save_data(data); st.session_state.edit_speler=None; st.success("✅ Bijgewerkt!"); st.rerun()
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
                            save_data(data); st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# PAGINA 2 — AANWEZIGHEID
# ══════════════════════════════════════════════════════════════════════════════
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
            wedstrijd_datum   = st.date_input("📅 Datum wedstrijd", value=date.today())
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
            if st.button("💾 Opslaan", type="primary"):
                data["trainingen"][datum_key] = {"afwezig":afwezig_selectie,"blessure":blessure_selectie}
                if wedstrijd_notitie: data["trainingen"][f"{datum_key}_notitie"] = wedstrijd_notitie
                save_data(data); st.success(f"✅ Aanwezigheid voor {wedstrijd_datum.strftime('%d %B %Y')} opgeslagen!")

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
                for datum in datum_lijst:
                    sessie=echte_wedstrijden[datum]
                    row[datum]="🩹" if naam in sessie.get("blessure",[]) else ("❌" if naam in sessie.get("afwezig",[]) else "✅")
                row["✅"]=aanwezig; row["❌"]=afwezig; row["🩹"]=blessure
                row["%"]=f"{round(aanwezig/len(datum_lijst)*100)}%" if datum_lijst else "0%"
                rows.append(row)
            st.dataframe(pd.DataFrame(rows), use_container_width=True, height=400)
            namen=[r["Speler"] for r in rows]
            st.markdown("**✅ Aanwezig**"); st.bar_chart(pd.DataFrame({"Aanwezig":[r["✅"] for r in rows]},index=namen))
            st.markdown("**❌ Afwezig**");  st.bar_chart(pd.DataFrame({"Afwezig": [r["❌"] for r in rows]},index=namen))
            st.markdown("**🩹 Geblesseerd**"); st.bar_chart(pd.DataFrame({"Blessure":[r["🩹"] for r in rows]},index=namen))
            wedstrijd_data=[]
            for datum in sorted(echte_wedstrijden.keys()):
                sessie=echte_wedstrijden[datum]; n_af=len(sessie.get("afwezig",[])); n_bl=len(sessie.get("blessure",[]))
                wedstrijd_data.append({"Datum":datum,"✅":totaal_spelers-n_af-n_bl,"❌":n_af,"🩹":n_bl,"Notitie":data["trainingen"].get(f"{datum}_notitie","")})
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

# ══════════════════════════════════════════════════════════════════════════════
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
        else:
            data["opstelling"][datum_key] = {
                "posities": posities_te_slaan,
                "formatie": formatie_te_slaan,
            }
            save_data(data)
            st.success(f"✅ Opstelling opgeslagen voor {datum_label_str} ({len(posities_te_slaan)} spelers)!")
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

/* Tokens */
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

/* Bank */
.bank {{ background:#F5F5F5; border:1px solid #BBB; border-top:4px solid #C44A00; border-radius:8px; padding:10px; }}
.bank-titel {{ font-family:'Bebas Neue',cursive; color:#333; letter-spacing:1px; font-size:.95rem; margin-bottom:8px; }}
.bank-lijst {{ display:flex; flex-wrap:wrap; gap:6px; }}
.bank-item {{
    display:flex; align-items:center; gap:5px; background:#fff;
    border:1.5px solid #BBB; border-radius:20px; padding:4px 10px 4px 5px;
    cursor:pointer; font-size:clamp(10px,2.5vw,12px); color:#111;
    transition:border-color .15s,background .15s;
}}
.bank-item:hover {{ border-color:#C44A00; background:#FFF0E6; }}
.bank-item.geplaatst {{ opacity:.35; cursor:default; pointer-events:none; }}
.bank-item.actief {{ border-color:#C44A00; background:#FFF0E6; font-weight:700; }}
.bnr {{
    width:24px; height:24px; border-radius:50%; background:#C44A00; color:#fff;
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
<body>
<div class="wrap">
  <div class="form-row">
    <h3>⚽ {datum_label_str}</h3>
    <select class="fsel" id="formatie" onchange="zetFormatie()">
      <option value="">-- Kies formatie --</option>
      <option value="4-3-3">4-3-3</option>
      <option value="4-4-2">4-4-2</option>
      <option value="4-2-3-1">4-2-3-1</option>
      <option value="3-5-2">3-5-2</option>
      <option value="5-3-2">5-3-2</option>
      <option value="3-4-3">3-4-3</option>
    </select>
  </div>

  <div class="veld-wrap">
    <div id="veld">
      <div class="cirkel"></div>
      <div class="sp-boven"></div><div class="sp-onder"></div>
      <div class="gb"></div><div class="go"></div>
      <div class="gs" style="left:0%"></div><div class="gs" style="left:18.18%"></div>
      <div class="gs" style="left:36.36%"></div><div class="gs" style="left:54.54%"></div>
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
    formatie: document.getElementById('formatie').value || ''
  }});
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

// ── Bank ────────────────────────────────────────────────────────────────────
function renderBank() {{
  const lijst = document.getElementById('bank');
  lijst.innerHTML = '';
  [...SPELERS].sort((a,b)=>a.nummer-b.nummer).forEach(s => {{
    const opVeld = s.naam in posities;
    const actief = plaatsMode === s.naam;
    const div    = document.createElement('div');
    div.className = 'bank-item'+(opVeld?' geplaatst':'')+(actief?' actief':'');
    div.innerHTML = `<div class="bnr">${{s.nummer}}</div><span>${{s.naam}}</span>`;
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
  posities[plaatsMode] = {{ x:((e.clientX-r.left)/r.width)*100, y:((e.clientY-r.top)/r.height)*100 }};
  plaatsMode = null; renderBank(); renderVeld(); onChange();
}});

function renderVeld() {{
  document.querySelectorAll('.token').forEach(el=>el.remove());
  const veld = document.getElementById('veld');
  Object.entries(posities).forEach(([naam, pos]) => {{
    const sp = SPELERS.find(s=>s.naam===naam); if(!sp) return;
    const tok = document.createElement('div');
    tok.className='token'; tok.style.left=pos.x+'%'; tok.style.top=pos.y+'%';
    tok.innerHTML=`<div class="tc">${{sp.nummer}}</div><div class="tn">${{naam.split(' ')[0]}}</div>`;
    tok.addEventListener('dblclick', e=>{{ e.stopPropagation(); delete posities[naam]; renderBank(); renderVeld(); onChange(); }});

    // Muis drag
    let dr=false,sX,sY,sL,sT;
    tok.addEventListener('mousedown',e=>{{ if(plaatsMode)return; e.preventDefault(); dr=true; sX=e.clientX;sY=e.clientY;sL=pos.x;sT=pos.y; tok.classList.add('dragging'); }});
    document.addEventListener('mousemove',e=>{{
      if(!dr)return; const r=veld.getBoundingClientRect();
      const nx=Math.max(2,Math.min(98,sL+((e.clientX-sX)/r.width)*100));
      const ny=Math.max(2,Math.min(98,sT+((e.clientY-sY)/r.height)*100));
      tok.style.left=nx+'%'; tok.style.top=ny+'%'; posities[naam]={{x:nx,y:ny}};
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
  posities={{}};
  sorted.forEach((s,i)=>{{ if(FORMATIES[f][i]) posities[s.naam]={{x:FORMATIES[f][i][0],y:FORMATIES[f][i][1]}}; }});
  renderBank(); renderVeld(); onChange();
}}

// ── Init ────────────────────────────────────────────────────────────────────
document.getElementById('formatie').value = INIT_FMT || '';
renderBank();
renderVeld();
// Stuur initiële staat direct door zodat Streamlit hem kent vóór eerste opslaan
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
