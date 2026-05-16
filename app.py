import streamlit as st
import pandas as pd
from datetime import date, datetime
import json
import os
from st_gsheets_connection import GSheetsConnection

st.set_page_config(page_title="⚽ BV O19-1 Dashboard", page_icon="⚽", layout="wide")

# Maak verbinding met Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    try:
        df_spelers = conn.read(worksheet="spelers", ttl=0)
        df_trainingen = conn.read(worksheet="trainingen", ttl=0)
        df_opstelling = conn.read(worksheet="opstelling", ttl=0)
        
        data = {"spelers": [], "trainingen": {}, "opstelling": {}}
        
        # 1. Spelers inladen
        if df_spelers is not None and not df_spelers.empty:
            for _, row in df_spelers.iterrows():
                if pd.notna(row['naam']):
                    data["spelers"].append({
                        "naam": str(row['naam']),
                        "positie": str(row['positie']),
                        "nummer": int(row['nummer'])
                    })
                    
        # 2. Trainingen/Aanwezigheid inladen
        if df_trainingen is not None and not df_trainingen.empty:
            for _, row in df_trainingen.iterrows():
                if pd.notna(row['datum']):
                    d_key = str(row['datum'])
                    data["trainingen"][d_key] = {
                        "afwezig": json.loads(row['afwezig']) if pd.notna(row['afwezig']) else [],
                        "blessure": json.loads(row['blessure']) if pd.notna(row['blessure']) else []
                    }
                    if 'notitie' in df_trainingen.columns and pd.notna(row['notitie']) and str(row['notitie']).strip():
                        data["trainingen"][f"{d_key}_notitie"] = str(row['notitie'])
                    
        # 3. Opstellingen inladen
        if df_opstelling is not None and not df_opstelling.empty:
            for _, row in df_opstelling.iterrows():
                if pd.notna(row['datum']):
                    d_key = str(row['datum'])
                    data["opstelling"][d_key] = {
                        "posities": json.loads(row['posities']) if pd.notna(row['posities']) else {},
                        "formatie": str(row['formatie']) if pd.notna(row['formatie']) else ""
                    }

        # Veiligheid: Voeg een basisspeler toe als de lijst leeg is om JS crash te voorkomen
        if not data["spelers"]:
            data["spelers"].append({"naam": "Eerste Speler (Test)", "positie": "Keeper", "nummer": 1})

        return data
    except Exception as e:
        return {"spelers": [{"naam": "Eerste Speler (Test)", "positie": "Keeper", "nummer": 1}], "trainingen": {}, "opstelling": {}}

def save_data(data):
    # 1. Spelers dataframe bouwen
    spelers_rijen = []
    for s in data["spelers"]:
        spelers_rijen.append({"naam": s["naam"], "positie": s["positie"], "nummer": s["nummer"]})
    df_spelers = pd.DataFrame(spelers_rijen) if spelers_rijen else pd.DataFrame(columns=["naam", "positie", "nummer"])
    
    # 2. Trainingen dataframe bouwen
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
    
    # 3. Opstellingen dataframe bouwen
    opstelling_rijen = []
    for datum, opst in data["opstelling"].items():
        opstelling_rijen.append({
            "datum": datum,
            "posities": json.dumps(opst.get("posities", {})),
            "formatie": opst.get("formatie", "")
        })
    df_opstelling = pd.DataFrame(opstelling_rijen) if opstelling_rijen else pd.DataFrame(columns=["datum", "posities", "formatie"])
    
    # Schrijf live naar de Google Sheet tabbladen
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

data = st.session_state.data
if "opstelling" not in data:
    data["opstelling"] = {}

# ─── CSS (Jouw originele styling) ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Inter:wght@400;600;700&display=swap');
:root {
    --oranje:      #C44A00; --oranje-dim:  #FFF0E6; --zwart:       #111111;
    --tekst:       #111111; --tekst-mid:   #333333; --tekst-zacht: #555555;
    --bg:          #FFFFFF; --bg-subtle:   #F5F5F5; --bg-muted:    #EBEBEB;
    --rand:        #BBBBBB; --rand-sterk:  #555555;
}
html, body, .stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"], [data-testid="block-container"] {
    background-color: var(--bg) !important; color: var(--tekst) !important; font-family: 'Inter', sans-serif !important;
}
section[data-testid="stSidebar"] { display: none !important; }
h1, h2, h3 { font-family: 'Bebas Neue', sans-serif !important; letter-spacing: 2px !important; color: var(--zwart) !important; }
h1 { color: var(--oranje) !important; font-size: clamp(1.8rem, 6vw, 3rem) !important; }
.stButton > button { font-weight: 700 !important; border-radius: 8px !important; min-height: 2.75rem !important; }
.stButton > button[kind="primary"] { background-color: var(--oranje) !important; color: #FFF !important; }
.stat-card { background: var(--bg-subtle); border: 1px solid var(--rand); border-top: 4px solid var(--oranje); border-radius: 8px; padding: 15px; text-align: center; margin-bottom: 10px;}
.stat-number { font-family: 'Bebas Neue', sans-serif; font-size: 2.2rem; color: var(--oranje); }
.team-row { display: flex; align-items: center; gap: 12px; background: var(--bg-subtle); border: 1px solid var(--rand); border-left: 4px solid var(--oranje); border-radius: 8px; padding: 10px; margin-bottom: 8px; }
.team-nr { width:36px; height:36px; border-radius:50%; background:var(--oranje); color:#FFF; font-family:'Bebas Neue',sans-serif; display:flex; align-items:center; justify-content:center; }
.speler-card { background:var(--bg-subtle); border:1px solid var(--rand); border-top:4px solid var(--oranje); border-radius:8px; padding:14px; margin-bottom:10px; }
.badge { display:inline-block; padding:3px 10px; border-radius:20px; font-size:0.78rem; font-weight:700; margin:2px; }
.badge-oranje { background:var(--oranje-dim); color:var(--oranje); border:1px solid var(--oranje); }
.badge-grijs  { background:var(--bg-muted); color:var(--tekst-mid); border:1px solid var(--rand-sterk); }
.preview-naam { font-size:0.95rem; padding:4px 0; color:var(--tekst); font-weight:600; }
</style>
""", unsafe_allow_html=True)

# ─── Header + navigatie ────────────────────────────────────────────────────────
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
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1: nieuwe_naam = st.text_input("Naam", placeholder="Jan de Vries", key="nieuw_naam")
        with col2: nieuwe_positie = st.selectbox("Positie", ["Keeper","Verdediger","Middenvelder","Aanvaller"], key="nieuw_pos")
        with col3: nieuwe_nummer = st.number_input("Rugnummer", min_value=1, max_value=99, value=1, key="nieuw_nr")
        if st.button("✅ Speler toevoegen", type="primary"):
            if nieuwe_naam.strip():
                if nieuwe_naam.strip() in [s["naam"] for s in data["spelers"]]:
                    st.error("Speler bestaat al!")
                else:
                    data["spelers"].append({"naam": nieuwe_naam.strip(), "positie": nieuwe_positie, "nummer": int(nieuwe_nummer)})
                    save_data(data); st.success(f"✅ {nieuwe_naam.strip()} toegevoegd!"); st.rerun()
            else: st.warning("Vul een naam in.")

    st.markdown("---")
    st.markdown(f"### Spelerslijst ({len(data['spelers'])} spelers)")
    pos_volgorde = {"Keeper":0,"Verdediger":1,"Middenvelder":2,"Aanvaller":3}
    pos_icons = {"Keeper":"🧤","Verdediger":"🛡️","Middenvelder":"⚙️","Aanvaller":"⚡"}
    gesorteerd = sorted(data["spelers"], key=lambda x: (pos_volgorde.get(x["positie"],9), x["nummer"]))
    
    for speler in gesorteerd:
        naam = speler["naam"]
        if st.session_state.edit_speler == naam:
            st.markdown('<div class="edit-box">', unsafe_allow_html=True)
            ec1, ec2, ec3 = st.columns([2,1,1])
            with ec1: nieuwe_naam_e = st.text_input("Naam", value=naam, key=f"edit_naam_{naam}")
            with ec2: 
                pos_opties = ["Keeper","Verdediger","Middenvelder","Aanvaller"]
                nieuwe_pos_e = st.selectbox("Positie", pos_opties, index=pos_opties.index(speler["positie"]), key=f"edit_pos_{naam}")
            with ec3: nieuwe_nr_e = st.number_input("Rugnummer", min_value=1, max_value=99, value=speler["nummer"], key=f"edit_nr_{naam}")
            bc1, bc2 = st.columns(2)
            with bc1:
                if st.button("💾 Opslaan", key=f"save_{naam}", type="primary", use_container_width=True):
                    for s in data["spelers"]:
                        if s["naam"] == naam:
                            s["naam"]=nieuwe_naam_e.strip(); s["positie"]=nieuwe_pos_e; s["nummer"]=int(nieuwe_nr_e)
                            break
                    save_data(data); st.session_state.edit_speler=None; st.rerun()
            with bc2:
                if st.button("❌ Annuleren", key=f"cancel_{naam}", use_container_width=True):
                    st.session_state.edit_speler=None; st.rerun()
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
                    if st.button("✏️", key=f"edit_{naam}", use_container_width=True):
                        st.session_state.edit_speler=naam; st.rerun()
                with bc2:
                    if st.button("🗑️", key=f"del_{naam}", use_container_width=True):
                        data["spelers"]=[s for s in data["spelers"] if s["naam"]!=naam]
                        save_data(data); st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# PAGINA 2 — AANWEZIGHEID
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.page == "aanwezigheid":
    echte_wedstrijden = {k:v for k,v in data["trainingen"].items() if not k.endswith("_notitie")}
    totaal_spelers = len(data["spelers"])
    totaal_wedstrijden = len(echte_wedstrijden)
    speler_namen = [s["naam"] for s in data["spelers"]]

    def speler_stats(naam):
        aanwezig=afwezig=blessure=0
        for sessie in echte_wedstrijden.values():
            if naam in sessie.get("blessure",[]): blessure+=1
            elif naam in sessie.get("afwezig",[]): afwezig+=1
            else: aanwezig+=1
        return aanwezig, afwezig, blessure

    r1c1, r1c2 = st.columns(2)
    with r1c1: st.markdown(f'<div class="stat-card"><div class="stat-number">{totaal_spelers}</div><div class="stat-label">Spelers</div></div>', unsafe_allow_html=True)
    with r1c2: st.markdown(f'<div class="stat-card"><div class="stat-number">{totaal_wedstrijden}</div><div class="stat-label">Wedstrijden</div></div>', unsafe_allow_html=True)
    st.markdown("---")

    tab1, tab2 = st.tabs(["📋 Registreren","📊 Overzicht"])
    with tab1:
        st.markdown("## 📋 Aanwezigheid registreren")
        wedstrijd_datum = st.date_input("📅 Datum wedstrijd", value=date.today())
        datum_key = str(wedstrijd_datum)
        wedstrijd_notitie = st.text_input("📝 Notitie (optioneel)", placeholder="Bijv. Uitwedstrijd...")
        bestaande = echte_wedstrijden.get(datum_key, {"afwezig":[],"blessure":[]})
        
        afwezig_selectie = st.multiselect("❌ Afwezig", options=speler_namen, default=[n for n in bestaande.get("afwezig",[]) if n in speler_namen])
        blessure_selectie = st.multiselect("🩹 Geblesseerd", options=speler_namen, default=[n for n in bestaande.get("blessure",[]) if n in speler_namen])
        
        if st.button("💾 Aanwezigheid opslaan", type="primary"):
            data["trainingen"][datum_key] = {"afwezig":afwezig_selectie,"blessure":blessure_selectie}
            if wedstrijd_notitie: data["trainingen"][f"{datum_key}_notitie"] = wedstrijd_notitie
            save_data(data); st.success("✅ Opgeslagen!"); st.rerun()

    with tab2:
        if not echte_wedstrijden: st.info("Nog geen data.")
        else:
            rows = []
            for naam in speler_namen:
                aanwezig, afwezig, blessure = speler_stats(naam)
                rows.append({"Speler": naam, "✅ Aanwezig": aanwezig, "❌ Afwezig": afwezig, "🩹 Blessure": blessure})
            st.dataframe(pd.DataFrame(rows), use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# PAGINA 3 — OPSTELLING (100% Veilige Modus)
# ══════════════════════════════════════════════════════════════════════════════
else:
    st.markdown("## 🟠 Opstelling per wedstrijd")
    alle_opst_keys = list_opstelling_datums(data)
    
    gekozen_datum = st.date_input("📅 Wedstrijddatum", value=st.session_state.opstelling_datum)
    if gekozen_datum != st.session_state.opstelling_datum:
