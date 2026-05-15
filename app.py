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
    return sorted(
        [k for k in data.get("opstelling", {}).keys()],
        reverse=True,
    )

def format_datum_label(datum_key, data):
    try:
        lbl = datetime.strptime(datum_key, "%Y-%m-%d").strftime("%d %B %Y")
    except ValueError:
        lbl = datum_key
    notitie = data.get("trainingen", {}).get(f"{datum_key}_notitie", "")
    if notitie:
        lbl += f" — {notitie}"
    n = len(data.get("opstelling", {}).get(datum_key, {}).get("posities", {}))
    return f"{lbl} ({n} op veld)"

if "data" not in st.session_state:
    st.session_state.data = load_data()
if "page" not in st.session_state:
    st.session_state.page = "team"
if "edit_speler" not in st.session_state:
    st.session_state.edit_speler = None
if "opstelling_datum" not in st.session_state:
    st.session_state.opstelling_datum = date.today()
if "opst_payload_raw" not in st.session_state:
    st.session_state.opst_payload_raw = ""

data = st.session_state.data
if "opstelling" not in data:
    data["opstelling"] = {}

# ─── CSS ──────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Inter:wght@400;600;700&display=swap');

:root {
    --oranje:        #C44A00;
    --oranje-hover:  #9A3A00;
    --oranje-licht:  #FFF0E6;
    --oranje-rand:   #C44A00;
    --zwart:         #1A1A1A;
    --tekst:         #111111;
    --tekst-mid:     #333333;
    --tekst-zacht:   #555555;
    --bg:            #FFFFFF;
    --bg-subtle:     #F5F5F5;
    --bg-muted:      #EBEBEB;
    --rand:          #BBBBBB;
    --rand-sterk:    #666666;
    --focus:         #C44A00;
}

/* Forceer lichte achtergrond & donkere tekst overal */
html, body,
.stApp,
.stApp > div,
[data-testid="stAppViewContainer"],
[data-testid="stMain"],
[data-testid="block-container"],
[class*="css"] {
    background-color: var(--bg) !important;
    color: var(--tekst) !important;
    font-family: 'Inter', sans-serif !important;
}

section[data-testid="stSidebar"] { display: none !important; }

/* ── Koppen: hard overschreven voor mobiel ── */
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
h1, .stApp h1, [data-testid="stMarkdown"] h1,
[data-testid="stMarkdownContainer"] h1 {
    font-size: clamp(1.8rem, 6vw, 3rem) !important;
    color: var(--oranje) !important;
    -webkit-text-fill-color: var(--oranje) !important;
}

/* ── Labels, paragrafen, captions ── */
label, p, span,
.stMarkdown p,
[data-testid="stMarkdown"] p,
[data-testid="stMarkdownContainer"] p,
[data-testid="stWidgetLabel"],
.stTextInput label,
.stNumberInput label,
.stDateInput label,
.stSelectbox label,
.stMultiSelect label,
.stExpander label,
[data-testid="stExpander"] summary,
[data-testid="stExpander"] summary p,
[data-testid="stExpander"] summary span {
    color: var(--tekst) !important;
    -webkit-text-fill-color: var(--tekst) !important;
    opacity: 1 !important;
}

/* Expander header */
[data-testid="stExpander"] > details > summary,
[data-testid="stExpander"] > details > summary *,
.streamlit-expanderHeader,
.streamlit-expanderHeader * {
    color: var(--tekst) !important;
    -webkit-text-fill-color: var(--tekst) !important;
    background-color: var(--bg-subtle) !important;
    font-weight: 600 !important;
    opacity: 1 !important;
}

/* ── Input velden ── */
input, textarea, select,
.stTextInput input,
.stNumberInput input,
.stDateInput input,
[data-baseweb="input"] input,
[data-baseweb="textarea"] textarea {
    color: var(--tekst) !important;
    -webkit-text-fill-color: var(--tekst) !important;
    background-color: var(--bg) !important;
    border-color: var(--rand-sterk) !important;
    opacity: 1 !important;
}
[data-baseweb="select"] {
    background-color: var(--bg) !important;
    border-color: var(--rand-sterk) !important;
}
[data-baseweb="select"] div,
[data-baseweb="select"] span {
    color: var(--tekst) !important;
    -webkit-text-fill-color: var(--tekst) !important;
    background-color: var(--bg) !important;
}

/* Multiselect dropdown opties */
[data-baseweb="menu"] li,
[data-baseweb="menu"] [role="option"] {
    color: var(--tekst) !important;
    background-color: var(--bg) !important;
}
[data-baseweb="menu"] li:hover,
[data-baseweb="menu"] [role="option"]:hover {
    background-color: var(--oranje-licht) !important;
}
/* Geselecteerde tags in multiselect */
[data-testid="stMultiSelect"] [data-baseweb="tag"],
[data-baseweb="tag"] {
    background-color: var(--oranje-licht) !important;
    border: 1px solid var(--oranje) !important;
    border-radius: 6px !important;
}
[data-testid="stMultiSelect"] [data-baseweb="tag"] span,
[data-baseweb="tag"] span {
    color: var(--oranje) !important;
    -webkit-text-fill-color: var(--oranje) !important;
    font-weight: 600 !important;
}
[data-baseweb="tag"] svg { fill: var(--oranje) !important; }

/* ── Knoppen ── */
.stButton > button {
    font-family: 'Inter', sans-serif !important;
    font-weight: 700 !important;
    font-size: 0.9rem !important;
    border-radius: 8px !important;
    min-height: 2.75rem !important;
    border-width: 2px !important;
}
.stButton > button[kind="primary"],
.stButton > button[data-testid="baseButton-primary"] {
    background-color: var(--oranje) !important;
    color: #FFFFFF !important;
    -webkit-text-fill-color: #FFFFFF !important;
    border-color: var(--oranje) !important;
}
.stButton > button[kind="primary"]:hover {
    background-color: var(--oranje-hover) !important;
    border-color: var(--oranje-hover) !important;
}
.stButton > button[kind="secondary"],
.stButton > button[data-testid="baseButton-secondary"] {
    background-color: var(--bg-subtle) !important;
    color: var(--zwart) !important;
    -webkit-text-fill-color: var(--zwart) !important;
    border-color: var(--rand-sterk) !important;
}
.stButton > button:focus-visible {
    outline: 3px solid var(--focus) !important;
    outline-offset: 2px !important;
}

/* ── Info / success / warning meldingen ── */
[data-testid="stAlert"] {
    color: var(--tekst) !important;
}
[data-testid="stAlert"] p,
[data-testid="stAlert"] span {
    color: var(--tekst) !important;
    -webkit-text-fill-color: var(--tekst) !important;
    opacity: 1 !important;
}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    background: var(--bg-subtle) !important;
    border: 1px solid var(--rand) !important;
    border-radius: 8px;
    padding: 4px;
    gap: 4px;
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    color: var(--tekst-mid) !important;
    -webkit-text-fill-color: var(--tekst-mid) !important;
    border-radius: 6px;
    font-family: 'Bebas Neue', sans-serif;
    letter-spacing: 1px;
    font-size: 1rem;
}
.stTabs [aria-selected="true"] {
    background: var(--oranje) !important;
    color: #FFFFFF !important;
    -webkit-text-fill-color: #FFFFFF !important;
}

/* ── Data tabel ── */
.stDataFrame { border: 1px solid var(--rand); border-radius: 8px; }

/* ── Custom componenten ── */
.stat-card {
    background: var(--bg-subtle);
    border: 1px solid var(--rand);
    border-top: 4px solid var(--oranje);
    border-radius: 8px;
    padding: clamp(10px, 3vw, 18px);
    text-align: center;
    margin-bottom: 10px;
}
.stat-card.dim { border-top-color: var(--rand-sterk); }
.stat-number {
    font-family: 'Bebas Neue', sans-serif;
    font-size: clamp(1.6rem, 5vw, 2.8rem);
    color: var(--oranje);
    line-height: 1.1;
    letter-spacing: 1px;
}
.stat-number.alt { color: var(--zwart); }
.stat-label {
    font-size: clamp(0.65rem, 2vw, 0.8rem);
    color: var(--tekst-zacht);
    text-transform: uppercase;
    letter-spacing: 1.5px;
    margin-top: 2px;
    font-weight: 700;
}

.team-row {
    display: flex;
    align-items: center;
    gap: 12px;
    background: var(--bg-subtle);
    border: 1px solid var(--rand);
    border-left: 4px solid var(--oranje);
    border-radius: 8px;
    padding: 10px 14px;
    margin-bottom: 8px;
}
.team-row:hover { background: var(--oranje-licht); }
.team-nr {
    width: 36px; height: 36px; border-radius: 50%;
    background: var(--oranje); color: #FFFFFF;
    font-family: 'Bebas Neue', sans-serif; font-size: 16px;
    display: flex; align-items: center; justify-content: center;
    flex-shrink: 0;
}
.team-naam { font-weight: 700; font-size: 0.95rem; color: var(--tekst); }
.team-pos  { font-size: 0.78rem; color: var(--tekst-zacht); }

.edit-box {
    background: var(--oranje-licht);
    border: 2px solid var(--oranje);
    border-radius: 10px;
    padding: 16px; margin-bottom: 10px;
}

.speler-card {
    background: var(--bg-subtle);
    border: 1px solid var(--rand);
    border-top: 4px solid var(--oranje);
    border-radius: 8px;
    padding: 14px; margin-bottom: 10px;
}

.badge {
    display: inline-block; padding: 3px 10px;
    border-radius: 20px; font-size: 0.78rem; font-weight: 700;
    margin: 2px 2px 4px 0;
}
.badge-oranje { background: var(--oranje-licht); color: var(--oranje); border: 1px solid var(--oranje); }
.badge-grijs  { background: var(--bg-muted); color: var(--tekst-mid); border: 1px solid var(--rand-sterk); }

.preview-naam { font-size: 0.95rem; padding: 4px 0; color: var(--tekst); font-weight: 600; }
hr { border-color: var(--rand) !important; }
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
        with col2: nieuwe_positie = st.selectbox("Positie", ["Keeper", "Verdediger", "Middenvelder", "Aanvaller"], key="nieuw_pos")
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
        pos_volgorde = {"Keeper": 0, "Verdediger": 1, "Middenvelder": 2, "Aanvaller": 3}
        pos_icons    = {"Keeper": "🧤", "Verdediger": "🛡️", "Middenvelder": "⚙️", "Aanvaller": "⚡"}
        gesorteerd   = sorted(data["spelers"], key=lambda x: (pos_volgorde.get(x["positie"], 9), x["nummer"]))

        for speler in gesorteerd:
            naam       = speler["naam"]
            is_editing = st.session_state.edit_speler == naam

            if is_editing:
                st.markdown('<div class="edit-box">', unsafe_allow_html=True)
                st.markdown(f"**✏️ {naam} bewerken**")
                ec1, ec2, ec3 = st.columns([2, 1, 1])
                with ec1: nieuwe_naam_e = st.text_input("Naam", value=naam, key=f"edit_naam_{naam}")
                with ec2:
                    pos_opties   = ["Keeper", "Verdediger", "Middenvelder", "Aanvaller"]
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
                                                for key in ["afwezig", "blessure"]:
                                                    if naam in sessie.get(key, []):
                                                        sessie[key].remove(naam)
                                                        sessie[key].append(nieuwe_naam_e)
                                    s["naam"] = nieuwe_naam_e; s["positie"] = nieuwe_pos_e; s["nummer"] = int(nieuwe_nr_e)
                                    break
                            save_data(data); st.session_state.edit_speler = None; st.success("✅ Bijgewerkt!"); st.rerun()
                with bc2:
                    if st.button("❌ Annuleren", key=f"cancel_{naam}", use_container_width=True):
                        st.session_state.edit_speler = None; st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
            else:
                icon = pos_icons.get(speler["positie"], "⚽")
                rc1, rc2 = st.columns([5, 2])
                with rc1:
                    st.markdown(f"""
                    <div class="team-row">
                        <div class="team-nr">{speler['nummer']}</div>
                        <div class="team-info">
                            <div class="team-naam">{naam}</div>
                            <div class="team-pos">{icon} {speler['positie']}</div>
                        </div>
                    </div>""", unsafe_allow_html=True)
                with rc2:
                    bc1, bc2 = st.columns(2)
                    with bc1:
                        if st.button("✏️", key=f"edit_{naam}", use_container_width=True, help="Bewerken"):
                            st.session_state.edit_speler = naam; st.rerun()
                    with bc2:
                        if st.button("🗑️", key=f"del_{naam}", use_container_width=True, help="Verwijderen"):
                            data["spelers"] = [s for s in data["spelers"] if s["naam"] != naam]
                            save_data(data); st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# PAGINA 2 — AANWEZIGHEID
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.page == "aanwezigheid":

    echte_wedstrijden  = {k: v for k, v in data["trainingen"].items() if not k.endswith("_notitie")}
    totaal_spelers     = len(data["spelers"])
    totaal_wedstrijden = len(echte_wedstrijden)
    speler_namen       = [s["naam"] for s in data["spelers"]]

    def speler_stats(naam):
        aanwezig = afwezig = blessure = 0
        for sessie in echte_wedstrijden.values():
            if naam in sessie.get("blessure", []):  blessure += 1
            elif naam in sessie.get("afwezig", []): afwezig  += 1
            else:                                    aanwezig += 1
        return aanwezig, afwezig, blessure

    if echte_wedstrijden and data["spelers"]:
        alle_pct         = [(totaal_spelers - len(s.get("afwezig",[])) - len(s.get("blessure",[]))) / totaal_spelers * 100 for s in echte_wedstrijden.values()]
        gem_aanwezigheid = round(sum(alle_pct) / len(alle_pct), 1)
        gem_blessure     = round(sum(len(s.get("blessure",[])) for s in echte_wedstrijden.values()) / totaal_wedstrijden, 1)
    else:
        gem_aanwezigheid = gem_blessure = 0

    r1c1, r1c2 = st.columns(2)
    with r1c1: st.markdown(f'<div class="stat-card"><div class="stat-number">{totaal_spelers}</div><div class="stat-label">Spelers</div></div>', unsafe_allow_html=True)
    with r1c2: st.markdown(f'<div class="stat-card"><div class="stat-number alt">{totaal_wedstrijden}</div><div class="stat-label">Wedstrijden</div></div>', unsafe_allow_html=True)
    r2c1, r2c2 = st.columns(2)
    with r2c1: st.markdown(f'<div class="stat-card"><div class="stat-number">{gem_aanwezigheid}%</div><div class="stat-label">Gem. aanwezigheid</div></div>', unsafe_allow_html=True)
    with r2c2: st.markdown(f'<div class="stat-card dim"><div class="stat-number alt">{gem_blessure}</div><div class="stat-label">Gem. geblesseerd p/wedstrijd</div></div>', unsafe_allow_html=True)

    st.markdown("---")
    tab1, tab2, tab3 = st.tabs(["📋 Registreren", "📊 Overzicht", "👥 Per speler"])

    with tab1:
        st.markdown("## 📋 Aanwezigheid registreren")
        if not data["spelers"]:
            st.info("Voeg eerst spelers toe via het Team-menu.")
        else:
            wedstrijd_datum   = st.date_input("📅 Datum wedstrijd", value=date.today())
            datum_key         = str(wedstrijd_datum)
            wedstrijd_notitie = st.text_input("📝 Notitie (optioneel)", placeholder="Bijv. Uitwedstrijd, bekerwedstrijd...")
            bestaande         = echte_wedstrijden.get(datum_key, {"afwezig": [], "blessure": []})

            st.markdown("### Wie is er afwezig?")
            st.markdown("**❌ Afwezig**")
            afwezig_selectie = st.multiselect("Afwezig", options=speler_namen,
                default=[n for n in bestaande.get("afwezig", []) if n in speler_namen],
                label_visibility="collapsed", key=f"afwezig_{datum_key}")
            st.markdown("**🩹 Geblesseerd**")
            blessure_selectie = st.multiselect("Geblesseerd", options=speler_namen,
                default=[n for n in bestaande.get("blessure", []) if n in speler_namen],
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
                data["trainingen"][datum_key] = {"afwezig": afwezig_selectie, "blessure": blessure_selectie}
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
                    sessie     = echte_wedstrijden[datum]
                    row[datum] = "🩹" if naam in sessie.get("blessure",[]) else ("❌" if naam in sessie.get("afwezig",[]) else "✅")
                row["✅"] = aanwezig; row["❌"] = afwezig; row["🩹"] = blessure
                row["%"]  = f"{round(aanwezig/len(datum_lijst)*100)}%" if datum_lijst else "0%"
                rows.append(row)

            st.dataframe(pd.DataFrame(rows), use_container_width=True, height=400)
            namen = [r["Speler"] for r in rows]
            st.markdown("**✅ Aanwezig**")
            st.bar_chart(pd.DataFrame({"Aanwezig": [r["✅"] for r in rows]}, index=namen))
            st.markdown("**❌ Afwezig**")
            st.bar_chart(pd.DataFrame({"Afwezig":  [r["❌"] for r in rows]}, index=namen))
            st.markdown("**🩹 Geblesseerd**")
            st.bar_chart(pd.DataFrame({"Blessure": [r["🩹"] for r in rows]}, index=namen))

            wedstrijd_data = []
            for datum in sorted(echte_wedstrijden.keys()):
                sessie = echte_wedstrijden[datum]
                n_af   = len(sessie.get("afwezig",[])); n_bl = len(sessie.get("blessure",[]))
                wedstrijd_data.append({"Datum": datum, "✅": totaal_spelers-n_af-n_bl, "❌": n_af, "🩹": n_bl,
                                       "Notitie": data["trainingen"].get(f"{datum}_notitie","")})
            st.markdown("### 📅 Overzicht per wedstrijd")
            st.dataframe(pd.DataFrame(wedstrijd_data).set_index("Datum"), use_container_width=True)
            st.markdown("### 📈 Trend per wedstrijd")
            st.bar_chart(pd.DataFrame(wedstrijd_data).set_index("Datum")[["✅","❌","🩹"]])

    with tab3:
        st.markdown("## 👥 Per speler")
        if not data["spelers"]:
            st.info("Nog geen spelers.")
        else:
            cols = st.columns(2)
            for i, speler in enumerate(sorted(data["spelers"], key=lambda x: x["nummer"])):
                naam = speler["naam"]
                aanwezig, afwezig, blessure = speler_stats(naam)
                totaal = len(echte_wedstrijden)
                pct    = round(aanwezig/totaal*100) if totaal else 0
                with cols[i % 2]:
                    st.markdown(f"""
                    <div class="speler-card">
                        <div style="font-family:'Bebas Neue',sans-serif;font-size:1.15rem;color:#1A1A1A;letter-spacing:0.5px;font-weight:700">
                            #{speler['nummer']} {naam}
                        </div>
                        <div style="color:#555555;font-size:0.8rem;margin-bottom:8px">{speler['positie']}</div>
                        <span class="badge badge-oranje">✅ {aanwezig}x aanwezig</span><br>
                        <span class="badge badge-grijs">❌ {afwezig}x afwezig</span>
                        <span class="badge badge-grijs">🩹 {blessure}x geblesseerd</span>
                        <hr style="margin:8px 0">
                        <div style="color:var(--oranje);font-weight:700;font-size:1.1rem">{pct}%</div>
                        <div style="color:#555555;font-size:0.78rem">{aanwezig}/{totaal} wedstrijden aanwezig</div>
                    </div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# PAGINA 3 — OPSTELLING
# De opstelling wordt opgeslagen via een hidden Streamlit text_input.
# JavaScript schrijft de JSON daarin; Streamlit leest het bij de volgende rerun.
# Geen query params, geen window.parent navigatie — simpel en betrouwbaar.
# ══════════════════════════════════════════════════════════════════════════════
else:
    st.markdown("## 🟠 Opstelling per wedstrijd")

    if not data["spelers"]:
        st.warning("Voeg eerst spelers toe via het Team-menu.")
        st.stop()

    # ── Datumkiezer + terugzoeken ──────────────────────────────────────────────
    alle_opst_keys = list_opstelling_datums(data)
    wedstrijd_keys = sorted([k for k in data.get("trainingen", {}) if not k.endswith("_notitie")], reverse=True)
    alle_datums    = sorted(set(wedstrijd_keys) | set(alle_opst_keys), reverse=True)

    dc1, dc2 = st.columns([1, 1])
    with dc1:
        gekozen_datum = st.date_input("📅 Wedstrijddatum", value=st.session_state.opstelling_datum, key="opst_datum_input")
        if gekozen_datum != st.session_state.opstelling_datum:
            st.session_state.opstelling_datum = gekozen_datum
            st.rerun()
    with dc2:
        if alle_datums:
            labels     = {d: format_datum_label(d, data) for d in alle_datums}
            label_list = ["— Kies een opgeslagen wedstrijd —"] + [labels[d] for d in alle_datums]
            gekozen    = st.selectbox("📂 Terugzoeken", label_list, key="opst_zoek")
            if gekozen != label_list[0]:
                for d, lbl in labels.items():
                    if lbl == gekozen:
                        nieuwe_datum = datetime.strptime(d, "%Y-%m-%d").date()
                        if nieuwe_datum != st.session_state.opstelling_datum:
                            st.session_state.opstelling_datum = nieuwe_datum
                            st.rerun()

    datum_key   = str(st.session_state.opstelling_datum)
    datum_label = st.session_state.opstelling_datum.strftime("%d %B %Y")

    # Haal bestaande opstelling op
    bestaande_entry  = data.get("opstelling", {}).get(datum_key, {})
    posities_huidig  = bestaande_entry.get("posities", {}) if isinstance(bestaande_entry, dict) else {}
    formatie_huidig  = bestaande_entry.get("formatie", "")  if isinstance(bestaande_entry, dict) else ""
    heeft_opgeslagen = datum_key in data.get("opstelling", {})

    notitie = data.get("trainingen", {}).get(f"{datum_key}_notitie", "")
    if notitie:
        st.caption(f"📝 Wedstrijdnotitie: {notitie}")
    if heeft_opgeslagen:
        st.success(f"Opgeslagen opstelling voor **{datum_label}** ({len(posities_huidig)} spelers op het veld).")
    else:
        st.info(f"Nog geen opstelling voor **{datum_label}**. Stel op en klik **Opstelling opslaan**.")

    # ── Verborgen text_input: JavaScript schrijft hierin, Streamlit leest het ──
    # We verbergen het met CSS via een unieke key.
    payload_key = "opst_payload_hidden"
    st.markdown("""
    <style>
    /* Verberg de hidden textarea volledig */
    [data-testid="stTextArea"][aria-label="__opst_hidden__"],
    div:has(> [data-testid="stTextArea"][aria-label="__opst_hidden__"]) {
        display: none !important;
        visibility: hidden !important;
        height: 0 !important;
        overflow: hidden !important;
    }
    </style>
    """, unsafe_allow_html=True)

    hidden_val = st.text_area("__opst_hidden__", value="", key=payload_key, label_visibility="hidden")

    # Verwerk inkomende payload van JavaScript
    if hidden_val and hidden_val.strip() and hidden_val != st.session_state.opst_payload_raw:
        st.session_state.opst_payload_raw = hidden_val
        try:
            payload = json.loads(hidden_val)
            dk      = payload.get("datum", datum_key)
            data["opstelling"][dk] = {
                "posities": payload.get("posities", {}),
                "formatie": payload.get("formatie", ""),
            }
            save_data(data)
            st.session_state.opstelling_datum = datetime.strptime(dk, "%Y-%m-%d").date()
            st.session_state.opst_payload_raw = ""
            st.success(f"✅ Opstelling opgeslagen voor {datetime.strptime(dk, '%Y-%m-%d').strftime('%d %B %Y')}!")
            st.rerun()
        except (json.JSONDecodeError, ValueError) as e:
            st.error(f"Kon opstelling niet verwerken: {e}")

    # ── HTML-veld ──────────────────────────────────────────────────────────────
    spelers_json      = json.dumps(data["spelers"], ensure_ascii=False)
    posities_json     = json.dumps(posities_huidig, ensure_ascii=False)
    formatie_json_str = json.dumps(formatie_huidig, ensure_ascii=False)
    datum_key_json    = json.dumps(datum_key, ensure_ascii=False)

    opstelling_html = f"""
<!DOCTYPE html>
<html lang="nl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ background: #FFFFFF; font-family: 'Inter', sans-serif; color: #111111; padding: 12px; }}
  .container {{ display: flex; flex-direction: column; gap: 16px; max-width: 700px; margin: 0 auto; }}
  h2 {{ font-family: 'Bebas Neue', cursive; color: #111111; font-size: 1.4rem; letter-spacing: 2px; }}

  .veld-wrap {{ position: relative; width: 100%; aspect-ratio: 68/105; max-height: 70vh; margin: 0 auto; }}
  #veld {{
    width:100%; height:100%;
    background: linear-gradient(180deg,#1a5c28 0%,#1e6b2e 25%,#1a5c28 50%,#1e6b2e 75%,#1a5c28 100%);
    border-radius:8px; border:3px solid #fff;
    position:relative; overflow:hidden; touch-action:none;
  }}
  #veld::before {{ content:''; position:absolute; top:50%; left:0; right:0; height:2px; background:rgba(255,255,255,0.6); }}
  .cirkel {{ position:absolute; top:50%; left:50%; transform:translate(-50%,-50%); width:20%; aspect-ratio:1; border:2px solid rgba(255,255,255,0.6); border-radius:50%; pointer-events:none; }}
  .strafschop-boven,.strafschop-onder {{ position:absolute; left:20%; right:20%; height:14%; border:2px solid rgba(255,255,255,0.6); pointer-events:none; }}
  .strafschop-boven {{ top:0; border-top:none; border-radius:0 0 6px 6px; }}
  .strafschop-onder {{ bottom:0; border-bottom:none; border-radius:6px 6px 0 0; }}
  .goal-boven,.goal-onder {{ position:absolute; left:35%; right:35%; height:4%; border:2px solid rgba(255,255,255,0.8); background:rgba(255,255,255,0.1); pointer-events:none; }}
  .goal-boven {{ top:0; border-top:none; }} .goal-onder {{ bottom:0; border-bottom:none; }}
  .gras-streep {{ position:absolute; top:0; bottom:0; width:9.09%; background:rgba(0,0,0,0.08); pointer-events:none; }}

  .speler-token {{ position:absolute; transform:translate(-50%,-50%); cursor:grab; touch-action:none; user-select:none; z-index:10; display:flex; flex-direction:column; align-items:center; gap:2px; }}
  .speler-token:active {{ cursor:grabbing; }}
  .token-cirkel {{
    width:clamp(32px,7vw,44px); height:clamp(32px,7vw,44px);
    border-radius:50%; background:#C44A00; border:2.5px solid #FFFFFF;
    display:flex; align-items:center; justify-content:center;
    font-family:'Bebas Neue',cursive; font-size:clamp(12px,3vw,16px);
    color:#FFFFFF; font-weight:700; letter-spacing:0.5px;
    box-shadow:0 2px 10px rgba(196,74,0,0.5); transition:box-shadow 0.15s;
  }}
  .speler-token.dragging .token-cirkel {{ box-shadow:0 4px 20px rgba(196,74,0,0.7); }}
  .token-naam {{
    background:#FFFFFF; color:#111111; font-weight:600;
    font-size:clamp(7px,1.8vw,10px); padding:2px 5px;
    border-radius:3px; white-space:nowrap;
    max-width:clamp(50px,12vw,70px); overflow:hidden; text-overflow:ellipsis; text-align:center;
    border:1px solid #C44A00;
  }}

  .bench {{ background:#F5F5F5; border:1px solid #BBBBBB; border-top:4px solid #C44A00; border-radius:8px; padding:12px; }}
  .bench-titel {{ font-family:'Bebas Neue',cursive; color:#333333; letter-spacing:1px; font-size:1rem; margin-bottom:10px; }}
  .bench-lijst {{ display:flex; flex-wrap:wrap; gap:8px; }}
  .bench-item {{
    display:flex; align-items:center; gap:6px;
    background:#FFFFFF; border:1.5px solid #BBBBBB;
    border-radius:20px; padding:5px 12px 5px 6px;
    cursor:pointer; font-size:clamp(11px,2.5vw,13px); color:#111111;
    transition:border-color 0.15s,background 0.15s;
  }}
  .bench-item:hover {{ border-color:#C44A00; background:#FFF0E6; }}
  .bench-item.geplaatst {{ opacity:0.4; cursor:default; pointer-events:none; }}
  .bench-item.actief {{ border-color:#C44A00; background:#FFF0E6; font-weight:700; }}
  .bench-nr {{
    width:26px; height:26px; border-radius:50%;
    background:#C44A00; color:#FFFFFF; font-weight:700;
    font-family:'Bebas Neue',cursive; font-size:13px;
    display:flex; align-items:center; justify-content:center; flex-shrink:0;
  }}

  .hint {{ color:#C44A00; font-size:0.82rem; margin-top:8px; width:100%; cursor:pointer; text-decoration:underline; font-weight:600; }}

  .knoppen {{ display:flex; gap:8px; flex-wrap:wrap; }}
  .btn {{
    flex:1; min-width:120px; padding:11px 16px; border-radius:8px;
    font-family:'Bebas Neue',cursive; font-size:1rem; letter-spacing:1px;
    cursor:pointer; transition:background 0.15s; font-weight:700; border:2px solid transparent;
  }}
  .btn-primary {{ background:#C44A00; color:#FFFFFF; border-color:#C44A00; }}
  .btn-primary:hover {{ background:#9A3A00; }}
  .btn-secondary {{ background:#F5F5F5; color:#111111; border-color:#666666; }}
  .btn-secondary:hover {{ background:#EBEBEB; }}

  .status {{ font-size:0.9rem; font-family:'Bebas Neue',cursive; letter-spacing:1px; font-weight:700; min-height:1.4rem; }}
  .status.ok  {{ color:#1B6B38; }}
  .status.err {{ color:#CC0000; }}

  .formation-select {{
    background:#FFFFFF; color:#111111;
    border:2px solid #666666; border-radius:8px;
    padding:8px 12px; font-size:0.9rem; cursor:pointer; flex:1; min-width:140px;
  }}
  .formation-select:focus {{ outline:3px solid #C44A00; outline-offset:2px; }}
</style>
<link href="https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Inter:wght@400;600;700&display=swap" rel="stylesheet">
</head>
<body>
<div class="container">

  <div style="display:flex;align-items:center;gap:12px;flex-wrap:wrap;">
    <h2>⚽ OPSTELLING — {datum_label}</h2>
    <select class="formation-select" id="formatie" onchange="zetFormatie()">
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
      <div class="strafschop-boven"></div><div class="strafschop-onder"></div>
      <div class="goal-boven"></div><div class="goal-onder"></div>
      <div class="gras-streep" style="left:0%"></div>
      <div class="gras-streep" style="left:18.18%"></div>
      <div class="gras-streep" style="left:36.36%"></div>
      <div class="gras-streep" style="left:54.54%"></div>
      <div class="gras-streep" style="left:72.72%"></div>
      <div class="gras-streep" style="left:90.9%"></div>
    </div>
  </div>

  <div class="bench">
    <div class="bench-titel">🪑 BANK — klik speler aan, tik dan op het veld</div>
    <div class="bench-lijst" id="bench-lijst"></div>
  </div>

  <div class="knoppen">
    <button type="button" class="btn btn-primary" onclick="slaOpOp()">💾 Opstelling opslaan</button>
    <button type="button" class="btn btn-secondary" onclick="reset()">🔄 Reset veld</button>
  </div>
  <div class="status" id="status-msg"></div>
</div>

<script>
const SPELERS       = {spelers_json};
const DATUM_KEY     = {datum_key_json};
const OPST_FORMATIE = {formatie_json_str};
let   posities      = {posities_json};
let   plaatsMode    = null;

// Zoek de verborgen textarea van Streamlit op basis van aria-label
function getHiddenTextarea() {{
  // Streamlit rendert textarea's met een uniek label
  const all = document.querySelectorAll('textarea');
  for (const ta of all) {{
    if (ta.closest('[data-testid="stTextArea"]')) return ta;
  }}
  return null;
}}

function writeToStreamlit(value) {{
  // We moeten via window.parent communiceren omdat het iframe is
  try {{
    const ta = window.parent.document.querySelector('textarea[aria-label="__opst_hidden__"]');
    if (ta) {{
      const nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.parent.HTMLTextAreaElement.prototype, 'value').set;
      nativeInputValueSetter.call(ta, value);
      ta.dispatchEvent(new Event('input', {{ bubbles: true }}));
      return true;
    }}
  }} catch(e) {{}}
  return false;
}}

function init() {{
  if (OPST_FORMATIE) document.getElementById('formatie').value = OPST_FORMATIE;
  renderBench(); renderVeld();
}}

function renderBench() {{
  const lijst = document.getElementById('bench-lijst');
  lijst.innerHTML = '';
  SPELERS.sort((a,b) => a.nummer - b.nummer).forEach(s => {{
    const opVeld = posities.hasOwnProperty(s.naam);
    const actief = plaatsMode === s.naam;
    const div    = document.createElement('div');
    div.className = 'bench-item' + (opVeld?' geplaatst':'') + (actief?' actief':'');
    div.innerHTML = `<div class="bench-nr">${{s.nummer}}</div><span>${{s.naam}}</span>`;
    if (!opVeld) div.onclick = () => startPlaatsen(s.naam);
    lijst.appendChild(div);
  }});
  if (plaatsMode) {{
    const hint = document.createElement('div');
    hint.className = 'hint';
    hint.textContent = `Tik op het veld om ${{plaatsMode}} te plaatsen · klik hier om te annuleren`;
    hint.onclick = () => {{ plaatsMode = null; renderBench(); }};
    lijst.appendChild(hint);
  }}
}}

function startPlaatsen(naam) {{ plaatsMode = naam; renderBench(); }}

document.getElementById('veld').addEventListener('click', function(e) {{
  if (!plaatsMode) return;
  const rect = this.getBoundingClientRect();
  posities[plaatsMode] = {{ x:((e.clientX-rect.left)/rect.width)*100, y:((e.clientY-rect.top)/rect.height)*100 }};
  plaatsMode = null; renderBench(); renderVeld();
}});

function renderVeld() {{
  document.querySelectorAll('.speler-token').forEach(el => el.remove());
  const veld = document.getElementById('veld');

  Object.entries(posities).forEach(([naam, pos]) => {{
    const speler = SPELERS.find(s => s.naam === naam);
    if (!speler) return;
    const token = document.createElement('div');
    token.className  = 'speler-token';
    token.style.left = pos.x + '%';
    token.style.top  = pos.y + '%';
    token.innerHTML  = `<div class="token-cirkel">${{speler.nummer}}</div><div class="token-naam">${{naam.split(' ')[0]}}</div>`;

    token.addEventListener('dblclick', e => {{
      e.stopPropagation();
      delete posities[naam]; renderBench(); renderVeld();
    }});

    let dragging=false, sX,sY,sL,sT;
    token.addEventListener('mousedown', e => {{
      if(plaatsMode) return; e.preventDefault();
      dragging=true; sX=e.clientX; sY=e.clientY; sL=pos.x; sT=pos.y;
      token.classList.add('dragging');
    }});
    document.addEventListener('mousemove', e => {{
      if(!dragging) return;
      const r=veld.getBoundingClientRect();
      const nx=Math.max(2,Math.min(98,sL+((e.clientX-sX)/r.width)*100));
      const ny=Math.max(2,Math.min(98,sT+((e.clientY-sY)/r.height)*100));
      token.style.left=nx+'%'; token.style.top=ny+'%'; posities[naam]={{x:nx,y:ny}};
    }});
    document.addEventListener('mouseup', ()=>{{ if(dragging){{dragging=false;token.classList.remove('dragging');}} }});

    let tX,tY,tL,tT;
    token.addEventListener('touchstart',e=>{{
      if(plaatsMode)return;
      const t=e.touches[0]; tX=t.clientX;tY=t.clientY;tL=pos.x;tT=pos.y;
      token.classList.add('dragging');
    }},{{passive:true}});
    token.addEventListener('touchmove',e=>{{
      e.preventDefault();
      const t=e.touches[0]; const r=veld.getBoundingClientRect();
      const nx=Math.max(2,Math.min(98,tL+((t.clientX-tX)/r.width)*100));
      const ny=Math.max(2,Math.min(98,tT+((t.clientY-tY)/r.height)*100));
      token.style.left=nx+'%'; token.style.top=ny+'%'; posities[naam]={{x:nx,y:ny}};
    }},{{passive:false}});
    token.addEventListener('touchend',()=>token.classList.remove('dragging'));

    veld.appendChild(token);
  }});
}}

const FORMATIES = {{
  '4-3-3':   [[50,88],[18,72],[38,72],[62,72],[82,72],[30,52],[50,48],[70,52],[20,28],[50,22],[80,28]],
  '4-4-2':   [[50,88],[18,72],[38,72],[62,72],[82,72],[18,52],[38,52],[62,52],[82,52],[35,25],[65,25]],
  '4-2-3-1': [[50,88],[18,72],[38,72],[62,72],[82,72],[35,58],[65,58],[20,40],[50,38],[80,40],[50,18]],
  '3-5-2':   [[50,88],[25,72],[50,70],[75,72],[15,52],[35,50],[55,50],[75,50],[90,52],[35,25],[65,25]],
  '5-3-2':   [[50,88],[10,72],[28,72],[50,68],[72,72],[90,72],[25,50],[50,48],[75,50],[35,25],[65,25]],
  '3-4-3':   [[50,88],[25,72],[50,70],[75,72],[18,52],[40,50],[60,50],[82,52],[20,28],[50,22],[80,28]],
}};

function zetFormatie() {{
  const f=document.getElementById('formatie').value; if(!f) return;
  const gesorteerd=[...SPELERS].sort((a,b)=>a.nummer-b.nummer).slice(0,11);
  posities={{}};
  gesorteerd.forEach((s,i)=>{{ if(FORMATIES[f][i]) posities[s.naam]={{x:FORMATIES[f][i][0],y:FORMATIES[f][i][1]}}; }});
  renderBench(); renderVeld();
}}

function slaOpOp() {{
  const msg = document.getElementById('status-msg');
  const payload = JSON.stringify({{
    datum:    DATUM_KEY,
    posities: posities,
    formatie: document.getElementById('formatie').value || ''
  }});

  const ok = writeToStreamlit(payload);
  if (ok) {{
    msg.className = 'status ok';
    msg.textContent = '✅ Versturen naar Streamlit... pagina herlaadt zo.';
  }} else {{
    msg.className = 'status err';
    msg.textContent = '⚠️ Kon niet communiceren met Streamlit. Probeer de pagina te herladen.';
  }}
}}

function reset() {{
  posities={{}};plaatsMode=null;
  document.getElementById('formatie').value='';
  document.getElementById('status-msg').textContent='';
  renderBench();renderVeld();
}}

init();
</script>
</body>
</html>
"""

    st.components.v1.html(opstelling_html, height=860, scrolling=True)

    st.caption("💡 Klik een speler op de bank, tik op het veld om te plaatsen. Sleep om te verplaatsen. Dubbelklik op een token om te verwijderen.")

    # ── Archief ────────────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### 📚 Opgeslagen opstellingen")
    archief = list_opstelling_datums(data)
    if not archief:
        st.caption("Er zijn nog geen opstellingen opgeslagen.")
    else:
        for dk in archief:
            entry     = data["opstelling"].get(dk, {})
            n_sp      = len(entry.get("posities", {}))
            fmt       = entry.get("formatie", "")
            try:    titel = datetime.strptime(dk, "%Y-%m-%d").strftime("%d %B %Y")
            except: titel = dk
            nt = data.get("trainingen", {}).get(f"{dk}_notitie", "")
            if nt: titel += f" — {nt}"

            ac1, ac2, ac3 = st.columns([4, 1, 1])
            with ac1:
                extra = f" · {fmt}" if fmt else ""
                st.markdown(f"**{titel}** — {n_sp} spelers{extra}")
            with ac2:
                if st.button("👁️ Bekijken", key=f"bekijk_{dk}", use_container_width=True):
                    st.session_state.opstelling_datum = datetime.strptime(dk, "%Y-%m-%d").date()
                    st.rerun()
            with ac3:
                if st.button("🗑️", key=f"del_opst_{dk}", help="Verwijderen", use_container_width=True):
                    del data["opstelling"][dk]
                    save_data(data)
                    st.rerun()
