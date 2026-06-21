import streamlit as st
import pandas as pd
from datetime import date, datetime
import requests
import json
import os
import base64

# ─── PAGINA CONFIG ────────────────────────────────────────────────────────────
st.set_page_config(page_title="⚽ BV O19-1 Dashboard", page_icon="⚽", layout="wide")

# ─── GITHUB CONFIGURATIE ──────────────────────────────────────────────────────
GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
REPO         = st.secrets["GITHUB_REPO"]
FILE_PATH    = "voetbal_data.json"
URL          = f"https://api.github.com/repos/{REPO}/contents/{FILE_PATH}"
HEADERS      = {"Authorization": f"token {GITHUB_TOKEN}"}

def laad_data_van_github():
    response = requests.get(URL, headers=HEADERS)
    if response.status_code == 200:
        content      = response.json()
        file_content = base64.b64decode(content["content"]).decode("utf-8")
        return json.loads(file_content), content["sha"]
    elif response.status_code == 404:
        return {"spelers": [], "trainingen": {}, "opstellingen": {}}, None
    else:
        st.error(f"Fout bij laden van GitHub: {response.status_code}")
        return {"spelers": [], "trainingen": {}, "opstellingen": {}}, None

def sla_data_op_naar_github(data, sha, melding="Data succesvol opgeslagen op GitHub! 💾"):
    data_string   = json.dumps(data, indent=2, ensure_ascii=False)
    content_bytes = base64.b64encode(data_string.encode("utf-8")).decode("utf-8")
    payload = {"message": "Update voetbal data via Streamlit App", "content": content_bytes}
    if sha:
        payload["sha"] = sha
    response = requests.put(URL, headers=HEADERS, json=payload)
    if response.status_code in [200, 201]:
        st.success(melding)
        st.rerun()
    else:
        st.error(f"Fout bij opslaan naar GitHub: {response.text}")

def list_opstelling_datums(data):
    return sorted(data.get("opstellingen", {}).keys(), reverse=True)

# ─── SESSION STATE ────────────────────────────────────────────────────────────
for k, v in [
    ("page",             "team"),
    ("edit_speler",      None),
    ("opstelling_datum", date.today()),
    ("opst_posities",    {}),
    ("opst_formatie",    ""),
]:
    if k not in st.session_state:
        st.session_state[k] = v

# ─── DATA LADEN ───────────────────────────────────────────────────────────────
data, file_sha = laad_data_van_github()
for k, v in [("spelers", []), ("trainingen", {}), ("opstellingen", {})]:
    if k not in data:
        data[k] = v

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

h1,h2,h3,.stApp h1,.stApp h2,.stApp h3,
[data-testid="stMarkdown"] h1,[data-testid="stMarkdown"] h2,[data-testid="stMarkdown"] h3,
[data-testid="stMarkdownContainer"] h1,[data-testid="stMarkdownContainer"] h2,[data-testid="stMarkdownContainer"] h3 {
    font-family: 'Bebas Neue', sans-serif !important;
    letter-spacing: 2px !important;
    color: var(--zwart) !important;
    -webkit-text-fill-color: var(--zwart) !important;
    opacity: 1 !important;
}
h1,.stApp h1,[data-testid="stMarkdown"] h1,[data-testid="stMarkdownContainer"] h1 {
    font-size: clamp(1.8rem,6vw,3rem) !important;
    color: var(--oranje) !important;
    -webkit-text-fill-color: var(--oranje) !important;
}

label, p, span,
[data-testid="stWidgetLabel"],
[data-testid="stExpander"] > details > summary,
[data-testid="stExpander"] > details > summary *,
.streamlit-expanderHeader, .streamlit-expanderHeader * {
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
.stTextInput input,.stNumberInput input,.stDateInput input {
    color: var(--tekst) !important;
    -webkit-text-fill-color: var(--tekst) !important;
    background-color: var(--bg) !important;
    border-color: var(--rand-sterk) !important;
}
[data-baseweb="select"],[data-baseweb="select"] div,[data-baseweb="select"] span {
    color: var(--tekst) !important;
    -webkit-text-fill-color: var(--tekst) !important;
    background-color: var(--bg) !important;
}
[data-baseweb="menu"] li { color: var(--tekst) !important; background: var(--bg) !important; }
[data-baseweb="menu"] li:hover { background: var(--oranje-dim) !important; }
[data-baseweb="tag"] { background-color: var(--oranje-dim) !important; border: 1px solid var(--oranje) !important; border-radius: 6px !important; }
[data-baseweb="tag"] span { color: var(--oranje) !important; -webkit-text-fill-color: var(--oranje) !important; font-weight: 700 !important; }
[data-baseweb="tag"] svg { fill: var(--oranje) !important; }

.stButton > button {
    font-family: 'Inter', sans-serif !important; font-weight: 700 !important;
    font-size: 0.9rem !important; border-radius: 8px !important;
    min-height: 2.75rem !important; border-width: 2px !important;
}
.stButton > button[kind="primary"] {
    background-color: var(--oranje) !important; color: #FFF !important;
    -webkit-text-fill-color: #FFF !important; border-color: var(--oranje) !important;
}
.stButton > button[kind="primary"]:hover { background-color: #9A3A00 !important; border-color: #9A3A00 !important; }
.stButton > button[kind="secondary"] {
    background-color: var(--bg-subtle) !important; color: var(--zwart) !important;
    -webkit-text-fill-color: var(--zwart) !important; border-color: var(--rand-sterk) !important;
}

[data-testid="stAlert"] p,[data-testid="stAlert"] span {
    color: var(--tekst) !important; -webkit-text-fill-color: var(--tekst) !important;
}

.stTabs [data-baseweb="tab-list"] {
    background: var(--bg-subtle) !important; border: 1px solid var(--rand) !important;
    border-radius: 8px; padding: 4px; gap: 4px;
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important; color: var(--tekst-mid) !important;
    -webkit-text-fill-color: var(--tekst-mid) !important;
    font-family: 'Bebas Neue', sans-serif; letter-spacing: 1px; font-size: 1rem; border-radius: 6px;
}
.stTabs [aria-selected="true"] {
    background: var(--oranje) !important; color: #FFF !important; -webkit-text-fill-color: #FFF !important;
}

.stat-card {
    background: var(--bg-subtle); border: 1px solid var(--rand);
    border-top: 4px solid var(--oranje); border-radius: 8px;
    padding: clamp(10px,3vw,18px); text-align: center; margin-bottom: 10px;
}
.stat-card.dim { border-top-color: var(--rand-sterk); }
.stat-number { font-family:'Bebas Neue',sans-serif; font-size:clamp(1.6rem,5vw,2.8rem); color:var(--oranje); line-height:1.1; letter-spacing:1px; }
.stat-number.alt { color: var(--zwart); }
.stat-label { font-size:clamp(0.65rem,2vw,0.8rem); color:var(--tekst-zacht); text-transform:uppercase; letter-spacing:1.5px; margin-top:2px; font-weight:700; }

.team-row {
    display:flex; align-items:center; gap:12px;
    background:var(--bg-subtle); border:1px solid var(--rand);
    border-left:4px solid var(--oranje); border-radius:8px;
    padding:10px 14px; margin-bottom:8px; transition:background .15s;
}
.team-row:hover { background: var(--oranje-dim); }
.team-nr { width:36px; height:36px; border-radius:50%; background:var(--oranje); color:#FFF; font-family:'Bebas Neue',sans-serif; font-size:16px; display:flex; align-items:center; justify-content:center; flex-shrink:0; }
.team-naam { font-weight:700; font-size:.95rem; color:var(--tekst); }
.team-pos  { font-size:.78rem; color:var(--tekst-zacht); }
.edit-box  { background:var(--oranje-dim); border:2px solid var(--oranje); border-radius:10px; padding:16px; margin-bottom:10px; }

.speler-card { background:var(--bg-subtle); border:1px solid var(--rand); border-top:4px solid var(--oranje); border-radius:8px; padding:14px; margin-bottom:10px; }
.badge { display:inline-block; padding:3px 10px; border-radius:20px; font-size:.78rem; font-weight:700; margin:2px 2px 4px 0; }
.badge-oranje { background:var(--oranje-dim); color:var(--oranje); border:1px solid var(--oranje); }
.badge-grijs  { background:var(--bg-muted); color:var(--tekst-mid); border:1px solid var(--rand-sterk); }
.preview-naam { font-size:.95rem; padding:4px 0; color:var(--tekst); font-weight:600; }
hr { border-color: var(--rand) !important; }
.stDataFrame { border:1px solid var(--rand); border-radius:8px; }

/* Verberg de brug-input volledig */
div[data-testid="stTextInput"]:has(input[aria-label="opst_brug_input"]) {
    position: absolute !important; opacity: 0 !important;
    pointer-events: none !important; height: 0 !important;
    overflow: hidden !important; top: -9999px !important;
}
</style>
""", unsafe_allow_html=True)

# ─── HEADER + NAVIGATIE ───────────────────────────────────────────────────────
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
                if any(s["naam"].lower() == nieuwe_naam.strip().lower() for s in data["spelers"]):
                    st.error("Speler bestaat al!")
                else:
                    data["spelers"].append({"naam": nieuwe_naam.strip(), "positie": nieuwe_positie, "nummer": int(nieuwe_nummer)})
                    sla_data_op_naar_github(data, file_sha, f"✅ {nieuwe_naam.strip()} toegevoegd!")
            else:
                st.warning("Vul een naam in.")

    st.markdown("---")
    st.markdown(f"### Spelerslijst ({len(data['spelers'])} spelers)")

    if not data["spelers"]:
        st.info("Nog geen spelers. Voeg hierboven je eerste speler toe.")
    else:
        pos_volgorde = {"Keeper":0,"Verdediger":1,"Middenvelder":2,"Aanvaller":3}
        pos_icons    = {"Keeper":"🧤","Verdediger":"🛡️","Middenvelder":"⚙️","Aanvaller":"⚡"}
        gesorteerd   = sorted(data["spelers"], key=lambda x: (pos_volgorde.get(x.get("positie",""),9), x.get("nummer",99)))

        for speler in gesorteerd:
            naam = speler["naam"]
            if st.session_state.edit_speler == naam:
                st.markdown('<div class="edit-box">', unsafe_allow_html=True)
                st.markdown(f"**✏️ {naam} bewerken**")
                ec1, ec2, ec3 = st.columns([2,1,1])
                with ec1: nieuwe_naam_e = st.text_input("Naam", value=naam, key=f"edit_naam_{naam}")
                with ec2:
                    pos_opties  = ["Keeper","Verdediger","Middenvelder","Aanvaller"]
                    huidige_pos = speler.get("positie","Verdediger")
                    if huidige_pos not in pos_opties: huidige_pos = "Verdediger"
                    nieuwe_pos_e = st.selectbox("Positie", pos_opties, index=pos_opties.index(huidige_pos), key=f"edit_pos_{naam}")
                with ec3: nieuwe_nr_e = st.number_input("Rugnummer", min_value=1, max_value=99, value=int(speler.get("nummer",1)), key=f"edit_nr_{naam}")
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
                                                for k in ["afwezig","blessure"]:
                                                    if naam in sessie.get(k,[]):
                                                        sessie[k].remove(naam); sessie[k].append(nieuwe_naam_e)
                                    s["naam"]=nieuwe_naam_e; s["positie"]=nieuwe_pos_e; s["nummer"]=int(nieuwe_nr_e)
                                    break
                            st.session_state.edit_speler = None
                            sla_data_op_naar_github(data, file_sha, "✅ Speler bijgewerkt!")
                with bc2:
                    if st.button("❌ Annuleren", key=f"cancel_{naam}", use_container_width=True):
                        st.session_state.edit_speler = None; st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
            else:
                rc1, rc2 = st.columns([5,2])
                with rc1:
                    icon = pos_icons.get(speler.get("positie",""),"⚽")
                    st.markdown(f"""<div class="team-row">
                        <div class="team-nr">{speler.get('nummer','')}</div>
                        <div><div class="team-naam">{naam}</div>
                        <div class="team-pos">{icon} {speler.get('positie','')}</div></div>
                    </div>""", unsafe_allow_html=True)
                with rc2:
                    bc1, bc2 = st.columns(2)
                    with bc1:
                        if st.button("✏️", key=f"edit_{naam}", use_container_width=True, help="Bewerken"):
                            st.session_state.edit_speler = naam; st.rerun()
                    with bc2:
                        if st.button("🗑️", key=f"del_{naam}", use_container_width=True, help="Verwijderen"):
                            data["spelers"] = [s for s in data["spelers"] if s["naam"] != naam]
                            sla_data_op_naar_github(data, file_sha, f"🗑️ {naam} verwijderd.")

# ══════════════════════════════════════════════════════════════════════════════
# PAGINA 2 — AANWEZIGHEID
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.page == "aanwezigheid":

    echte_trainingen  = {k: v for k, v in data["trainingen"].items() if not k.endswith("_notitie")}
    totaal_spelers    = len(data["spelers"])
    totaal_trainingen = len(echte_trainingen)
    speler_namen      = [s["naam"] for s in data["spelers"]]

    def speler_stats(naam):
        aanwezig = afwezig = blessure = 0
        for sessie in echte_trainingen.values():
            if not isinstance(sessie, dict): continue
            if naam in sessie.get("blessure",[]): blessure += 1
            elif naam in sessie.get("afwezig",[]): afwezig += 1
            else: aanwezig += 1
        return aanwezig, afwezig, blessure

    # ── Stat-kaarten ──────────────────────────────────────────────────────────
    if echte_trainingen and data["spelers"]:
        alle_pct = [
            (totaal_spelers - len(s.get("afwezig",[])) - len(s.get("blessure",[]))) / totaal_spelers * 100
            for s in echte_trainingen.values() if isinstance(s, dict)
        ]
        gem_aanw = round(sum(alle_pct)/len(alle_pct), 1) if alle_pct else 0
        gem_bl   = round(sum(len(s.get("blessure",[])) for s in echte_trainingen.values() if isinstance(s,dict)) / totaal_trainingen, 1)
    else:
        gem_aanw = gem_bl = 0

    r1c1, r1c2 = st.columns(2)
    with r1c1: st.markdown(f'<div class="stat-card"><div class="stat-number">{totaal_spelers}</div><div class="stat-label">Spelers</div></div>', unsafe_allow_html=True)
    with r1c2: st.markdown(f'<div class="stat-card"><div class="stat-number alt">{totaal_trainingen}</div><div class="stat-label">Trainingen geregistreerd</div></div>', unsafe_allow_html=True)
    r2c1, r2c2 = st.columns(2)
    with r2c1: st.markdown(f'<div class="stat-card"><div class="stat-number">{gem_aanw}%</div><div class="stat-label">Gem. aanwezigheid</div></div>', unsafe_allow_html=True)
    with r2c2: st.markdown(f'<div class="stat-card dim"><div class="stat-number alt">{gem_bl}</div><div class="stat-label">Gem. geblesseerd p/training</div></div>', unsafe_allow_html=True)

    st.markdown("---")
    tab1, tab2, tab3 = st.tabs(["📋 Registreren", "📊 Overzicht", "👥 Per speler"])

    # ── Tab 1: Registreren ────────────────────────────────────────────────────
    with tab1:
        st.markdown("## 📋 Aanwezigheid registreren")
        if not data["spelers"]:
            st.info("Voeg eerst spelers toe via het Team-menu.")
        else:
            training_datum   = st.date_input("📅 Datum training", value=date.today())
            datum_key        = str(training_datum)
            training_notitie = st.text_input("📝 Notitie (optioneel)", placeholder="Bijv. Thuiswedstrijd, regenachtig...")
            bestaande        = echte_trainingen.get(datum_key, {"afwezig":[],"blessure":[]})
            if not isinstance(bestaande, dict):
                bestaande = {"afwezig":[],"blessure":[]}

            st.markdown("### Wie is er afwezig?")
            st.markdown("**❌ Afwezig**")
            afwezig_sel = st.multiselect("Afwezig", options=speler_namen,
                default=[n for n in bestaande.get("afwezig",[]) if n in speler_namen],
                label_visibility="collapsed", key=f"afwezig_{datum_key}")

            st.markdown("**🩹 Geblesseerd**")
            blessure_sel = st.multiselect("Geblesseerd", options=speler_namen,
                default=[n for n in bestaande.get("blessure",[]) if n in speler_namen],
                label_visibility="collapsed", key=f"blessure_{datum_key}")

            aanwezig_namen = [n for n in speler_namen if n not in afwezig_sel and n not in blessure_sel]

            st.markdown("---")
            with st.expander(f"✅ Aanwezig ({len(aanwezig_namen)})", expanded=True):
                for n in aanwezig_namen:
                    st.markdown(f'<div class="preview-naam">🟠 {n}</div>', unsafe_allow_html=True)
            with st.expander(f"❌ Afwezig ({len(afwezig_sel)})"):
                for n in afwezig_sel:
                    st.markdown(f'<span class="badge badge-grijs">{n}</span>', unsafe_allow_html=True)
            with st.expander(f"🩹 Geblesseerd ({len(blessure_sel)})"):
                for n in blessure_sel:
                    st.markdown(f'<span class="badge badge-oranje">🩹 {n}</span>', unsafe_allow_html=True)

            if st.button("💾 Opslaan", type="primary", key="aanw_opslaan"):
                data["trainingen"][datum_key] = {"afwezig": afwezig_sel, "blessure": blessure_sel}
                if training_notitie:
                    data["trainingen"][f"{datum_key}_notitie"] = training_notitie
                sla_data_op_naar_github(data, file_sha,
                    f"✅ Aanwezigheid voor {training_datum.strftime('%d %B %Y')} opgeslagen!")

    # ── Tab 2: Overzicht ──────────────────────────────────────────────────────
    with tab2:
        st.markdown("## 📊 Aanwezigheidsoverzicht")
        if not echte_trainingen or not data["spelers"]:
            st.info("Nog geen aanwezigheidsdata beschikbaar.")
        else:
            datum_lijst = sorted(echte_trainingen.keys(), reverse=True)
            rows = []
            for naam in speler_namen:
                aanwezig, afwezig, blessure = speler_stats(naam)
                row = {"Speler": naam}
                for datum in datum_lijst:
                    sessie = echte_trainingen[datum]
                    if not isinstance(sessie, dict):
                        row[datum] = "–"; continue
                    row[datum] = "🩹" if naam in sessie.get("blessure",[]) else ("❌" if naam in sessie.get("afwezig",[]) else "✅")
                row["✅"] = aanwezig
                row["❌"] = afwezig
                row["🩹"] = blessure
                row["Aanwezig"] = f"{aanwezig}/{len(datum_lijst)}"
                row["%"] = f"{round(aanwezig/len(datum_lijst)*100)}%" if datum_lijst else "0%"
                rows.append(row)

            # Toon kolommen: Speler + datums + totalen
            display_cols = ["Speler"] + datum_lijst + ["✅","❌","🩹","Aanwezig","%"]
            st.dataframe(pd.DataFrame(rows)[display_cols], use_container_width=True, height=400)

            namen = [r["Speler"] for r in rows]
            st.markdown("**✅ Aanwezig**")
            st.bar_chart(pd.DataFrame({"Aanwezig": [r["✅"] for r in rows]}, index=namen))
            st.markdown("**❌ Afwezig**")
            st.bar_chart(pd.DataFrame({"Afwezig":  [r["❌"] for r in rows]}, index=namen))
            st.markdown("**🩹 Geblesseerd**")
            st.bar_chart(pd.DataFrame({"Blessure": [r["🩹"] for r in rows]}, index=namen))

            t_data = []
            for datum in sorted(echte_trainingen.keys()):
                sessie = echte_trainingen[datum]
                if not isinstance(sessie, dict): continue
                n_af = len(sessie.get("afwezig",[])); n_bl = len(sessie.get("blessure",[]))
                t_data.append({"Datum": datum, "✅": totaal_spelers-n_af-n_bl, "❌": n_af, "🩹": n_bl,
                               "Notitie": data["trainingen"].get(f"{datum}_notitie","")})
            if t_data:
                st.markdown("### 📅 Overzicht per training")
                st.dataframe(pd.DataFrame(t_data).set_index("Datum"), use_container_width=True)
                st.markdown("### 📈 Trend per training")
                st.bar_chart(pd.DataFrame(t_data).set_index("Datum")[["✅","❌","🩹"]])

    # ── Tab 3: Per speler ─────────────────────────────────────────────────────
    with tab3:
        st.markdown("## 👥 Per speler")
        if not data["spelers"]:
            st.info("Nog geen spelers.")
        else:
            cols = st.columns(2)
            for i, speler in enumerate(sorted(data["spelers"], key=lambda x: x.get("nummer",99))):
                naam = speler["naam"]
                aanwezig, afwezig, blessure = speler_stats(naam)
                totaal = len(echte_trainingen)
                pct    = round(aanwezig/totaal*100) if totaal else 0
                with cols[i%2]:
                    st.markdown(f"""<div class="speler-card">
                        <div style="font-family:'Bebas Neue',sans-serif;font-size:1.15rem;color:#111;letter-spacing:.5px;font-weight:700">#{speler.get('nummer','')} {naam}</div>
                        <div style="color:#555;font-size:.8rem;margin-bottom:8px">{speler.get('positie','')}</div>
                        <span class="badge badge-oranje">✅ {aanwezig}/{totaal} trainingen</span><br>
                        <span class="badge badge-grijs">❌ {afwezig}x afwezig</span>
                        <span class="badge badge-grijs">🩹 {blessure}x geblesseerd</span>
                        <hr style="margin:8px 0">
                        <div style="color:var(--oranje);font-weight:700;font-size:1.1rem">{pct}% aanwezig</div>
                    </div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# PAGINA 3 — OPSTELLING
#
# Hoe het opslaan werkt (betrouwbaar zonder custom component):
#
# 1. Het iframe-veld stuurt posities via window.parent.postMessage naar de
#    Streamlit-pagina zodra er iets verandert.
# 2. Een 0px-hoge st.components.v1.html BUITEN het iframe vangt het bericht op
#    en schrijft de JSON naar het verborgen st.text_input via de React native
#    value setter (de enige methode die Streamlit detecteert).
# 3. Streamlit slaat de waarde op in session_state bij de volgende render.
# 4. De echte Streamlit-knop "💾 Opstelling opslaan" leest session_state en
#    schrijft naar GitHub. Geen page-navigatie, geen sessieverlies.
#
# BELANGRIJK: de brug-verwerking doet GEEN st.rerun() — anders wordt de knop
# nooit bereikt. De posities zijn al beschikbaar in session_state vóór de knop.
# ══════════════════════════════════════════════════════════════════════════════
else:
    st.markdown("## 🟠 Opstelling per wedstrijd")

    if not data["spelers"]:
        st.warning("Voeg eerst spelers toe via het Team-menu.")
        st.stop()

    alle_opst_keys = list_opstelling_datums(data)

    # ── Datumkiezer + dropdown ─────────────────────────────────────────────────
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
            def _lbl(dk):
                try:    t = datetime.strptime(dk, "%Y-%m-%d").strftime("%d %B %Y")
                except: t = dk
                n  = len(data["opstellingen"].get(dk,{}).get("posities",{}))
                nt = data.get("trainingen",{}).get(f"{dk}_notitie","")
                return f"{t}{' — '+nt if nt else ''} ({n} spelers)"

            opties  = ["— Kies opgeslagen opstelling —"] + alle_opst_keys
            labels  = ["— Kies opgeslagen opstelling —"] + [_lbl(dk) for dk in alle_opst_keys]
            gekozen = st.selectbox("📂 Opgeslagen opstellingen", labels, key="opst_zoek")
            if gekozen != labels[0]:
                idx = labels.index(gekozen)
                dk  = opties[idx]
                try:    nd = datetime.strptime(dk, "%Y-%m-%d").date()
                except: nd = st.session_state.opstelling_datum
                if nd != st.session_state.opstelling_datum:
                    entry = data["opstellingen"].get(dk, {})
                    st.session_state.opstelling_datum = nd
                    st.session_state.opst_posities    = entry.get("posities", {})
                    st.session_state.opst_formatie    = entry.get("formatie", "")
                    st.rerun()

    datum_key       = str(st.session_state.opstelling_datum)
    datum_label_str = st.session_state.opstelling_datum.strftime("%d %B %Y")

    bestaande_entry  = data["opstellingen"].get(datum_key, {})
    posities_init    = bestaande_entry.get("posities", {}) if isinstance(bestaande_entry, dict) else {}
    formatie_init    = bestaande_entry.get("formatie", "")  if isinstance(bestaande_entry, dict) else ""
    heeft_opgeslagen = datum_key in data["opstellingen"]

    # Laad bestaande opstelling in session_state als die er is en session_state leeg is
    if not st.session_state.opst_posities and posities_init:
        st.session_state.opst_posities = posities_init
        st.session_state.opst_formatie = formatie_init

    nt = data.get("trainingen",{}).get(f"{datum_key}_notitie","")
    if nt: st.caption(f"📝 {nt}")
    if heeft_opgeslagen:
        st.success(f"Opgeslagen opstelling voor **{datum_label_str}** — {len(posities_init)} spelers op het veld.")
    else:
        st.info(f"Nog geen opstelling voor **{datum_label_str}**.")

    # ── Knoppen ───────────────────────────────────────────────────────────────
    sk1, sk2, sk3 = st.columns([2, 1, 1])
    with sk2:
        opslaan_clicked = st.button("💾 Opstelling opslaan", type="primary", use_container_width=True, key="opst_opslaan")
    with sk3:
        reset_clicked = st.button("🔄 Reset veld", use_container_width=True, key="opst_reset")

    if reset_clicked:
        st.session_state.opst_posities = {}
        st.session_state.opst_formatie = ""
        st.rerun()

    if opslaan_clicked:
        pos = st.session_state.get("opst_posities", {})
        fmt = st.session_state.get("opst_formatie", "")
        if not pos:
            st.warning("⚠️ Geen spelers op het veld gevonden. Plaats spelers en klik dan op opslaan.")
        else:
            data["opstellingen"][datum_key] = {"posities": pos, "formatie": fmt}
            sla_data_op_naar_github(data, file_sha,
                f"✅ Opstelling opgeslagen voor {datum_label_str} ({len(pos)} spelers)!")

    # ── Verborgen brug-input ──────────────────────────────────────────────────
    # Ontvangt JSON van de postMessage-ontvanger hieronder.
    # GEEN st.rerun() hier — anders bereikt de opslaan-knop de posities nooit.
    brug_waarde = st.text_input("opst_brug_input", value="", key="opst_brug", label_visibility="hidden")
    if brug_waarde and brug_waarde.strip():
        try:
            payload = json.loads(brug_waarde)
            st.session_state.opst_posities = payload.get("posities", {})
            st.session_state.opst_formatie = payload.get("formatie", "")
            st.session_state["opst_brug"]  = ""
            # Geen rerun — posities zijn nu beschikbaar voor de volgende klik op opslaan
        except json.JSONDecodeError:
            pass

    # ── postMessage-ontvanger (0px, leeft buiten iframe) ─────────────────────
    # Vangt berichten van het veld-iframe op en schrijft ze naar de brug-input
    # via de React native setter (de enige methode die Streamlit detecteert).
    ontvanger = """<script>
(function() {
  if (window.__opst_listener__) return; // Voorkom dubbele registratie
  window.__opst_listener__ = true;
  window.addEventListener('message', function(e) {
    if (!e.data || e.data.type !== 'opst_update') return;
    var input = window.parent.document.querySelector('input[aria-label="opst_brug_input"]');
    if (!input) return;
    var setter = Object.getOwnPropertyDescriptor(window.parent.HTMLInputElement.prototype, 'value').set;
    setter.call(input, e.data.payload);
    input.dispatchEvent(new Event('input', {bubbles: true}));
  });
})();
</script>"""
    st.components.v1.html(ontvanger, height=0)

    # ── Veld-iframe ────────────────────────────────────────────────────────────
    # Gebruikt session_state.opst_posities (bevat geladen of bewerkte posities)
    posities_voor_iframe = st.session_state.opst_posities if st.session_state.opst_posities else posities_init
    formatie_voor_iframe = st.session_state.opst_formatie if st.session_state.opst_formatie else formatie_init

    spelers_json      = json.dumps(data["spelers"], ensure_ascii=False)
    posities_json_str = json.dumps(posities_voor_iframe, ensure_ascii=False)
    formatie_json_str = json.dumps(formatie_voor_iframe, ensure_ascii=False)

    veld_html = f"""<!DOCTYPE html>
<html lang="nl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:#FFF;font-family:'Inter',sans-serif;color:#111;padding:8px}}
.wrap{{display:flex;flex-direction:column;gap:12px;max-width:700px;margin:0 auto}}
h3{{font-family:'Bebas Neue',cursive;color:#111;font-size:1.2rem;letter-spacing:2px}}
.veld-wrap{{width:100%;aspect-ratio:68/105;max-height:65vh;margin:0 auto;position:relative}}
#veld{{
  width:100%;height:100%;
  background:linear-gradient(180deg,#1a5c28 0%,#1e6b2e 25%,#1a5c28 50%,#1e6b2e 75%,#1a5c28 100%);
  border-radius:8px;border:3px solid #fff;position:relative;overflow:hidden;touch-action:none;
  box-shadow:0 6px 16px rgba(0,0,0,0.15);
}}
#veld::before{{content:'';position:absolute;top:50%;left:0;right:0;height:2px;background:rgba(255,255,255,.6)}}
.cirkel{{position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);width:20%;aspect-ratio:1;border:2px solid rgba(255,255,255,.6);border-radius:50%;pointer-events:none}}
.sp-boven,.sp-onder{{position:absolute;left:20%;right:20%;height:14%;border:2px solid rgba(255,255,255,.6);pointer-events:none}}
.sp-boven{{top:0;border-top:none;border-radius:0 0 6px 6px}}
.sp-onder{{bottom:0;border-bottom:none;border-radius:6px 6px 0 0}}
.gb,.go{{position:absolute;left:35%;right:35%;height:4%;border:2px solid rgba(255,255,255,.8);background:rgba(255,255,255,.1);pointer-events:none}}
.gb{{top:0;border-top:none}}.go{{bottom:0;border-bottom:none}}
.gs{{position:absolute;top:0;bottom:0;width:9.09%;background:rgba(0,0,0,.08);pointer-events:none}}
.token{{position:absolute;transform:translate(-50%,-50%);cursor:grab;touch-action:none;user-select:none;z-index:10;display:flex;flex-direction:column;align-items:center;gap:2px}}
.token:active{{cursor:grabbing}}
.tc{{
  width:clamp(32px,8vw,44px);height:clamp(32px,8vw,44px);border-radius:50%;
  background:linear-gradient(135deg,#FF6600,#C44A00);border:2.5px solid #fff;
  display:flex;align-items:center;justify-content:center;
  font-family:'Bebas Neue',cursive;font-size:clamp(12px,3vw,16px);color:#fff;font-weight:700;
  box-shadow:0 3px 10px rgba(196,74,0,.5);transition:box-shadow .15s,transform .1s;
}}
.token.dragging .tc{{box-shadow:0 6px 20px rgba(196,74,0,.7);transform:scale(1.1)}}
.tn{{background:rgba(0,0,0,0.8);color:#fff;font-weight:600;font-size:clamp(7px,2vw,10px);padding:2px 5px;border-radius:3px;white-space:nowrap;max-width:clamp(44px,12vw,64px);overflow:hidden;text-overflow:ellipsis;text-align:center;border:1px solid #C44A00}}
.bank{{background:#F5F5F5;border:1px solid #BBB;border-top:4px solid #C44A00;border-radius:8px;padding:10px}}
.bank-titel{{font-family:'Bebas Neue',cursive;color:#333;letter-spacing:1px;font-size:.95rem;margin-bottom:8px}}
.bank-lijst{{display:flex;flex-wrap:wrap;gap:6px}}
.bank-item{{display:flex;align-items:center;gap:5px;background:#fff;border:1.5px solid #BBB;border-radius:20px;padding:4px 10px 4px 5px;cursor:pointer;font-size:clamp(10px,2.5vw,13px);color:#111;transition:border-color .15s,background .15s}}
.bank-item:hover{{border-color:#C44A00;background:#FFF0E6}}
.bank-item.geplaatst{{opacity:.35;cursor:default;pointer-events:none}}
.bank-item.actief{{border-color:#C44A00;background:#FFF0E6;font-weight:700}}
.bnr{{width:24px;height:24px;border-radius:50%;background:#C44A00;color:#fff;font-family:'Bebas Neue',cursive;font-size:12px;display:flex;align-items:center;justify-content:center;flex-shrink:0}}
.hint{{color:#C44A00;font-size:.8rem;margin-top:6px;width:100%;cursor:pointer;text-decoration:underline;font-weight:600}}
.form-row{{display:flex;align-items:center;gap:10px;flex-wrap:wrap;margin-bottom:4px}}
.fsel{{background:#fff;color:#111;border:2px solid #666;border-radius:8px;padding:7px 11px;font-size:.88rem;cursor:pointer;flex:1;min-width:130px}}
.fsel:focus{{outline:3px solid #C44A00;outline-offset:2px}}
.sync-status{{font-size:.75rem;color:#888;margin-top:2px;min-height:1rem}}
</style>
<link href="https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Inter:wght@400;600;700&display=swap" rel="stylesheet">
</head>
<body>
<div class="wrap">
  <div class="form-row">
    <h3>⚽ {datum_label_str}</h3>
    <select class="fsel" id="formatie" onchange="zetFormatie()">
      <option value="">-- Vrije opstelling --</option>
      <option value="4-3-3">4-3-3</option>
      <option value="4-4-2">4-4-2</option>
      <option value="4-2-3-1">4-2-3-1</option>
      <option value="3-5-2">3-5-2</option>
      <option value="5-3-2">5-3-2</option>
      <option value="3-4-3">3-4-3</option>
    </select>
  </div>
  <div class="sync-status" id="sync-status">Laadt opstelling...</div>

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
    <div class="bank-titel">🪑 BANK — klik speler, tik dan op het veld · dubbelklik token om te verwijderen</div>
    <div class="bank-lijst" id="bank"></div>
  </div>
</div>

<script>
const SPELERS  = {spelers_json};
const INIT_POS = {posities_json_str};
const INIT_FMT = {formatie_json_str};

// Gebruik een deep copy zodat INIT_POS niet gemuteerd wordt
let posities   = JSON.parse(JSON.stringify(INIT_POS));
let plaatsMode = null;
let syncTimer  = null;

function setSyncStatus(msg) {{
  const el = document.getElementById('sync-status');
  if (el) el.textContent = msg;
}}

// Stuur posities naar de postMessage-ontvanger buiten het iframe.
// Debounce zodat we niet bij elke pixel-beweging sturen.
function stuur() {{
  clearTimeout(syncTimer);
  syncTimer = setTimeout(function() {{
    const fmt = document.getElementById('formatie').value || '';
    const payload = JSON.stringify({{ posities: posities, formatie: fmt }});
    window.parent.postMessage({{ type: 'opst_update', payload: payload }}, '*');
    setSyncStatus('✓ ' + Object.keys(posities).length + ' speler(s) op het veld — klik Opstelling opslaan om op te slaan');
  }}, 150);
}}

function renderBank() {{
  const lijst = document.getElementById('bank');
  lijst.innerHTML = '';
  [...SPELERS].sort(function(a,b){{return a.nummer-b.nummer;}}).forEach(function(s) {{
    const opVeld = s.naam in posities;
    const actief = plaatsMode === s.naam;
    const div    = document.createElement('div');
    div.className = 'bank-item' + (opVeld?' geplaatst':'') + (actief?' actief':'');
    div.innerHTML = '<div class="bnr">'+s.nummer+'</div><span>'+s.naam+'</span>';
    if (!opVeld) div.onclick = function() {{ plaatsMode = s.naam; renderBank(); }};
    lijst.appendChild(div);
  }});
  if (plaatsMode) {{
    const hint = document.createElement('div');
    hint.className = 'hint';
    hint.textContent = 'Tik op het veld om ' + plaatsMode + ' te plaatsen · klik hier om te annuleren';
    hint.onclick = function() {{ plaatsMode = null; renderBank(); }};
    lijst.appendChild(hint);
  }}
}}

document.getElementById('veld').addEventListener('click', function(e) {{
  if (!plaatsMode) return;
  const r = this.getBoundingClientRect();
  posities[plaatsMode] = {{
    x: Math.max(2, Math.min(98, ((e.clientX - r.left) / r.width) * 100)),
    y: Math.max(2, Math.min(98, ((e.clientY - r.top)  / r.height) * 100))
  }};
  plaatsMode = null;
  renderBank();
  renderVeld();
  stuur();
}});

function renderVeld() {{
  document.querySelectorAll('.token').forEach(function(el){{el.remove();}});
  const veld = document.getElementById('veld');

  Object.keys(posities).forEach(function(naam) {{
    const pos = posities[naam];
    const sp  = SPELERS.find(function(s){{return s.naam===naam;}}) || {{nummer:'?'}};
    const tok = document.createElement('div');
    tok.className  = 'token';
    tok.style.left = pos.x + '%';
    tok.style.top  = pos.y + '%';
    tok.innerHTML  = '<div class="tc">'+sp.nummer+'</div><div class="tn">'+naam.split(' ')[0]+'</div>';

    tok.addEventListener('dblclick', function(e) {{
      e.stopPropagation();
      delete posities[naam];
      renderBank(); renderVeld(); stuur();
    }});

    // Muis drag
    var dr=false, sX, sY, sL, sT;
    tok.addEventListener('mousedown', function(e) {{
      if (plaatsMode) return;
      e.preventDefault();
      dr=true; sX=e.clientX; sY=e.clientY; sL=pos.x; sT=pos.y;
      tok.classList.add('dragging');
    }});
    document.addEventListener('mousemove', function(e) {{
      if (!dr) return;
      var r = veld.getBoundingClientRect();
      pos.x = Math.max(2, Math.min(98, sL + ((e.clientX-sX)/r.width)*100));
      pos.y = Math.max(2, Math.min(98, sT + ((e.clientY-sY)/r.height)*100));
      tok.style.left = pos.x + '%';
      tok.style.top  = pos.y + '%';
    }});
    document.addEventListener('mouseup', function() {{
      if (dr) {{ dr=false; tok.classList.remove('dragging'); stuur(); }}
    }});

    // Touch drag
    var tX, tY, tL, tT;
    tok.addEventListener('touchstart', function(e) {{
      if (plaatsMode) return;
      var t = e.touches[0]; tX=t.clientX; tY=t.clientY; tL=pos.x; tT=pos.y;
      tok.classList.add('dragging');
    }}, {{passive:true}});
    tok.addEventListener('touchmove', function(e) {{
      e.preventDefault();
      var t=e.touches[0], r=veld.getBoundingClientRect();
      pos.x = Math.max(2, Math.min(98, tL + ((t.clientX-tX)/r.width)*100));
      pos.y = Math.max(2, Math.min(98, tT + ((t.clientY-tY)/r.height)*100));
      tok.style.left = pos.x + '%';
      tok.style.top  = pos.y + '%';
    }}, {{passive:false}});
    tok.addEventListener('touchend', function() {{
      tok.classList.remove('dragging'); stuur();
    }});

    veld.appendChild(tok);
  }});
}}

var FORMATIES = {{
  '4-3-3':   [[50,88],[18,72],[38,72],[62,72],[82,72],[30,52],[50,48],[70,52],[20,28],[50,22],[80,28]],
  '4-4-2':   [[50,88],[18,72],[38,72],[62,72],[82,72],[18,52],[38,52],[62,52],[82,52],[35,25],[65,25]],
  '4-2-3-1': [[50,88],[18,72],[38,72],[62,72],[82,72],[35,58],[65,58],[20,40],[50,38],[80,40],[50,18]],
  '3-5-2':   [[50,88],[25,72],[50,70],[75,72],[15,52],[35,50],[55,50],[75,50],[90,52],[35,25],[65,25]],
  '5-3-2':   [[50,88],[10,72],[28,72],[50,68],[72,72],[90,72],[25,50],[50,48],[75,50],[35,25],[65,25]],
  '3-4-3':   [[50,88],[25,72],[50,70],[75,72],[18,52],[40,50],[60,50],[82,52],[20,28],[50,22],[80,28]]
}};

function zetFormatie() {{
  var f = document.getElementById('formatie').value;
  if (!f) return;
  var sorted = [...SPELERS].sort(function(a,b){{return a.nummer-b.nummer;}}).slice(0,11);
  posities = {{}};
  sorted.forEach(function(s,i) {{
    if (FORMATIES[f][i]) posities[s.naam] = {{x:FORMATIES[f][i][0], y:FORMATIES[f][i][1]}};
  }});
  renderBank(); renderVeld(); stuur();
}}

// Initialisatie
document.getElementById('formatie').value = INIT_FMT || '';
renderBank();
renderVeld();
// Stuur initiële staat zodat Streamlit de posities kent vóór eerste opslaan
setTimeout(stuur, 500);
setSyncStatus(Object.keys(posities).length + ' speler(s) geladen');
</script>
</body>
</html>"""

    st.components.v1.html(veld_html, height=820, scrolling=True)
    st.caption("💡 Klik een speler op de bank, tik dan op het veld. Sleep om te verplaatsen. Dubbelklik op een token om te verwijderen. Klik dan **Opstelling opslaan** hierboven.")

    # ── Archief ────────────────────────────────────────────────────────────────
    if alle_opst_keys:
        st.markdown("---")
        st.markdown("### 📚 Opgeslagen opstellingen")
        for dk in alle_opst_keys:
            entry = data["opstellingen"].get(dk, {})
            n_sp  = len(entry.get("posities", {}))
            fmt   = entry.get("formatie", "")
            try:    titel = datetime.strptime(dk, "%Y-%m-%d").strftime("%d %B %Y")
            except: titel = dk
            nt = data.get("trainingen",{}).get(f"{dk}_notitie","")
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
                if st.button("🗑️", key=f"del_opst_{dk}", help="Verwijderen", use_container_width=True):
                    del data["opstellingen"][dk]
                    sla_data_op_naar_github(data, file_sha, f"🗑️ Opstelling van {titel} verwijderd.")
