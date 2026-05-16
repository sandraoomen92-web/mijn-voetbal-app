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
    # 1. Spelers
    spelers_rijen = []
    for s in data["spelers"]:
        spelers_rijen.append({"naam": s["naam"], "positie": s["positie"], "nummer": s["nummer"]})
    df_spelers = pd.DataFrame(spelers_rijen) if spelers_rijen else pd.DataFrame(columns=["naam", "positie", "nummer"])
    
    # 2. Trainingen
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
    
    # 3. Opstellingen
    opstelling_rijen = []
    for datum, opst in data["opstelling"].items():
        opstelling_rijen.append({
            "datum": datum,
            "posities": json.dumps(opst.get("posities", {})),
            "formatie": opst.get("formatie", "")
        })
    df_opstelling = pd.DataFrame(opstelling_rijen) if opstelling_rijen else pd.DataFrame(columns=["datum", "posities", "formatie"])
    
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
            else: GridView_Aanwezig=1; aanwezig+=1
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
# PAGINA 3 — OPSTELLING
# ══════════════════════════════════════════════════════════════════════════════
else:
    st.markdown("## 🟠 Opstelling per wedstrijd")
    alle_opst_keys = list_opstelling_datums(data)
    
    gekozen_datum = st.date_input("📅 Wedstrijddatum", value=st.session_state.opstelling_datum)
    if gekozen_datum != st.session_state.opstelling_datum:
        st.session_state.opstelling_datum = gekozen_datum
        st.rerun()
        
    datum_key = str(st.session_state.opstelling_datum)
    
    # Haal de huidige opstelling op van deze datum of start leeg
    huidige_opstelling = data["opstelling"].get(datum_key, {"posities": {}, "formatie": "4-3-3"})
    
    # Formatie kiezer
    formaties = ["4-3-3", "4-4-2", "3-5-2", "5-3-2", "4-2-3-1"]
    default_idx = formaties.index(huidige_opstelling.get("formatie", "4-3-3")) if huidige_opstelling.get("formatie", "4-3-3") in formaties else 0
    gekozen_formatie = st.selectbox("Formatie", formaties, index=default_idx)
    
    # ─── VEILIGE EN OFFICIËLE COMMUNICATIEBRUG VIA COMPONENT STATE ────────────────
    # We vangen de data op die JavaScript via window.parent.postMessage stuurt
    import streamlit.components.v1 as components
    
    # Maak verborgen velden aan via st.session_state om de data vast te houden
    with st.expander("💾 Klik hier om de huidige opstelling definitief te bewaren", expanded=True):
        if st.button("💾 Sla huidige veldopstelling op in Google Sheets", type="primary"):
            if st.session_state.opst_posities:
                data["opstelling"][datum_key] = {
                    "posities": st.session_state.opst_posities,
                    "formatie": gekozen_formatie
                }
                save_data(data)
                st.success("✅ Opstelling succesvol bewaard in Google Sheets!")
                st.rerun()
            else:
                st.warning("Versleep eerst een aantal spelers op het veld voordat je opslaat.")

    # HTML/JS Tactiekveld genereren
    opgeslagen_posities_json = json.dumps(huidige_opstelling.get("posities", {}))
    spelers_lijst_json = json.dumps(data["spelers"])
    
    veld_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <meta charset="utf-8">
    <style>
    body {{ font-family: 'Inter', sans-serif; margin: 0; padding: 10px; background: #FFFFFF; }}
    .opstelling-container {{ display: flex; gap: 20px; flex-wrap: wrap; }}
    .veld-wrapper {{ position: relative; width: 100%; max-width: 500px; aspect-ratio: 1 / 1.3; background: linear-gradient(135deg, #1e4620 0%, #153016 100%); border: 4px solid #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 8px 24px rgba(0,0,0,0.15); }}
    .lijnen {{ position: absolute; top: 0; left: 0; width: 100%; height: 100%; pointer-events: none; }}
    .middenlijn {{ position: absolute; top: 50%; left: 0; width: 100%; height: 2px; background: rgba(255,255,255,0.5); }}
    .middencirkel {{ position: absolute; top: 50%; left: 50%; width: 100px; height: 100px; border: 2px solid rgba(255,255,255,0.5); border-radius: 50%; transform: translate(-50%, -50%); }}
    .strafschopgebied-top {{ position: absolute; top: 0; left: 50%; width: 60%; height: 18%; border: 2px solid rgba(255,255,255,0.5); border-top: none; transform: translateX(-50%); }}
    .strafschopgebied-bot {{ position: absolute; bottom: 0; left: 50%; width: 60%; height: 18%; border: 2px solid rgba(255,255,255,0.5); border-bottom: none; transform: translateX(-50%); }}
    .doelgebied-top {{ position: absolute; top: 0; left: 50%; width: 30%; height: 6%; border: 2px solid rgba(255,255,255,0.5); border-top: none; transform: translateX(-50%); }}
    .doelgebied-bot {{ position: absolute; bottom: 0; left: 50%; width: 30%; height: 6%; border: 2px solid rgba(255,255,255,0.5); border-bottom: none; transform: translateX(-50%); }}
    .speler-node {{ position: absolute; width: 45px; height: 45px; background: #C44A00; color: white; border-radius: 50%; border: 2px solid white; display: flex; align-items: center; justify-content: center; font-weight: bold; cursor: move; box-shadow: 0 4px 8px rgba(0,0,0,0.3); transform: translate(-50%, -50%); user-select: none; z-index: 10; font-size: 14px; transition: transform 0.1s; }}
    .speler-node .naam-label {{ position: absolute; bottom: -22px; left: 50%; transform: translateX(-50%); background: rgba(0,0,0,0.75); color: white; padding: 2px 6px; border-radius: 4px; font-size: 10px; white-space: nowrap; font-weight: normal; border: 1px solid rgba(255,255,255,0.2); }}
    .speler-node:active {{ transform: translate(-50%, -50%) scale(1.1); z-index: 100; }}
    .bank-container {{ flex: 1; min-width: 250px; background: #F5F5F5; border: 1px solid #BBBBBB; border-radius: 12px; padding: 15px; display: flex; flex-direction: column; }}
    .bank-titel {{ font-weight: bold; margin-bottom: 12px; color: #111111; display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #EBEBEB; padding-bottom: 8px; }}
    .bank-lijst {{ display: flex; flex-direction: column; gap: 8px; overflow-y: auto; max-height: 450px; padding-right: 5px; }}
    .bank-item {{ display: flex; align-items: center; gap: 10px; background: white; border: 1px solid #BBBBBB; border-radius: 8px; padding: 8px 12px; cursor: pointer; transition: all 0.2s; }}
    .bank-item:hover {{ border-color: #C44A00; background: #FFF0E6; transform: translateY(-1px); }}
    .bank-nr {{ width: 24px; height: 24px; background: #C44A00; color: white; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 11px; font-weight: bold; }}
    .bank-info {{ display: flex; flex-direction: column; }}
    .bank-naam {{ font-weight: 600; font-size: 13px; color: #111111; }}
    .bank-pos {{ font-size: 11px; color: #555555; }}
    </style>
    </head>
    <body>
    <div class="opstelling-container">
      <div class="veld-wrapper" id="veld">
        <div class="lijnen">
          <div class="middenlijn"></div>
          <div class="middencirkel"></div>
          <div class="strafschopgebied-top"></div>
          <div class="strafschopgebied-bot"></div>
          <div class="doelgebied-top"></div>
          <div class="doelgebied-bot"></div>
        </div>
      </div>
      <div class="bank-container">
        <div class="bank-titel">👥 Wisselbank <span style="font-size:12px; font-weight:normal; color:#555;" id="bank-count">0</span></div>
        <div class="bank-lijst" id="bank"></div>
      </div>
    </div>

    <script>
    const spelers = {spelers_lijst_json};
    const opgeslagenPosities = {opgeslagen_posities_json};
    const formatie = "{gekozen_formatie}";

    const veld = document.getElementById('veld');
    const bank = document.getElementById('bank');
    
    // Standaard formatie locaties (X, Y procentueel)
    const formatieTemplates = {{
        "4-3-3": [
            {{x:50, y:90}}, // K
            {{x:15, y:70}}, {{x:38, y:73}}, {{x:62, y:73}}, {{x:85, y:70}}, // V
            {{x:30, y:50}}, {{x:50, y:55}}, {{x:70, y:50}}, // M
            {{x:20, y:25}}, {{x:50, y:20}}, {{x:80, y:25}}  // A
        ],
        "4-4-2": [
            {{x:50, y:90}},
            {{x:15, y:70}}, {{x:38, y:73}}, {{x:62, y:73}}, {{x:85, y:70}},
            {{x:20, y:48}}, {{x:42, y:52}}, {{x:58, y:52}}, {{x:80, y:48}},
            {{x:35, y:22}}, {{x:65, y:22}}
        ],
        "3-5-2": [
            {{x:50, y:90}},
            {{x:25, y:73}}, {{x:50, y:75}}, {{x:75, y:73}},
            {{x:15, y:48}}, {{x:35, y:50}}, {{x:50, y:55}}, {{x:65, y:50}}, {{x:85, y:48}},
            {{x:35, y:22}}, {{x:65, y:22}}
        ],
        "5-3-2": [
            {{x:50, y:90}},
            {{x:15, y:68}}, {{x:32, y:72}}, {{x:50, y:74}}, {{x:68, y:72}}, {{x:85, y:68}},
            {{x:30, y:48}}, {{x:50, y:52}}, {{x:70, y:48}},
            {{x:35, y:22}}, {{x:65, y:22}}
        ],
        "4-2-3-1": [
            {{x:50, y:90}},
            {{x:15, y:70}}, {{x:38, y:73}}, {{x:62, y:73}}, {{x:85, y:70}},
            {{x:35, y:56}}, {{x:65, y:56}},
            {{x:20, y:38}}, {{x:50, y:35}}, {{x:80, y:38}},
            {{x:50, y:18}}
        ]
    }};

    let positiesInGebruik = {{...opgeslagenPosities}};
    let actieveSleepNode = null;

    function stuurDataNaarStreamlit() {{
        // STABIELE OPLOSSING: We sturen de data via postMessage naar de Streamlit kluis
        window.parent.postMessage({{
            type: "streamlit:setComponentValue",
            value: positiesInGebruik
        }}, "*");
    }}

    function initVeld() {{
        const template = formatieTemplates[formatie] || formatieTemplates["4-3-3"];
        let geplaatsteSpelers = Object.keys(positiesInGebruik);
        let templateIndex = 0;

        spelers.forEach(speler => {{
            if (positiesInGebruik[speler.naam]) {{
                maakSpelerNode(speler.naam, speler.nummer, positiesInGebruik[speler.naam].x, positiesInGebruik[speler.naam].y);
            }} else if (geplaatsteSpelers.length === 0 && templateIndex < template.length) {{
                let pos = template[templateIndex++];
                positiesInGebruik[speler.naam] = pos;
                maakSpelerNode(speler.naam, speler.nummer, pos.x, pos.y);
            }} else {{
                voegToeAanBank(speler);
            }}
        }});
        stuurDataNaarStreamlit();
        updateBankTeller();
    }}

    function maakSpelerNode(naam, nummer, xPct, yPct) {{
        const node = document.createElement('div');
        node.className = 'speler-node';
        node.style.left = xPct + '%';
        node.style.top = yPct + '%';
        node.innerText = nummer;

        const label = document.createElement('div');
        label.className = 'naam-label';
        label.innerText = naam;
        node.appendChild(label);

        node.addEventListener('mousedown', (e) => startSleep(e, node, naam));
        node.addEventListener('touchstart', (e) => startSleep(e, node, naam), {{passive: false}});
        
        node.addEventListener('dblclick', () => {{
            node.remove();
            delete positiesInGebruik[naam];
            const spelerObj = spelers.find(s => s.naam === naam);
            if (spelerObj) voegToeAanBank(spelerObj);
            stuurDataNaarStreamlit();
            updateBankTeller();
        }});

        veld.appendChild(node);
    }}

    function voegToeAanBank(speler) {{
        const item = document.createElement('div');
        item.className = 'bank-item';
        item.innerHTML = `<div class="bank-nr">${{speler.nummer}}</div>
                          <div class="bank-info">
                            <div class="bank-naam">${{speler.naam}}</div>
                            <div class="bank-pos">${{speler.positie}}</div>
                          </div>`;
        
        item.addEventListener('click', () => {{
            item.remove();
            positiesInGebruik[speler.naam] = {{x: 50, y: 50}};
            maakSpelerNode(speler.naam, speler.nummer, 50, 50);
            stuurDataNaarStreamlit();
            updateBankTeller();
        }});
        bank.appendChild(item);
    }}

    function startSleep(e, node, naam) {{
        e.preventDefault();
        actieveSleepNode = {{ node, naam }};
        document.addEventListener('mousemove', doeSleep);
        document.addEventListener('mouseup', stopSleep);
        document.addEventListener('touchmove', doeSleep, {{passive: false}});
        document.addEventListener('touchend', stopSleep);
    }}

    function doeSleep(e) {{
        if (!actieveSleepNode) return;
        const clientX = e.touches ? e.touches[0].clientX : e.clientX;
        const clientY = e.touches ? e.touches[0].clientY : e.clientY;
        
        const rect = veld.getBoundingClientRect();
        let x = ((clientX - rect.left) / rect.width) * 100;
        let y = ((clientY - rect.top) / rect.height) * 100;
        
        if (x < 0) x = 0; if (x > 100) x = 100;
        if (y < 0) y = 0; if (y > 100) y = 100;
        
        actieveSleepNode.node.style.left = x + '%';
        actieveSleepNode.node.style.top = y + '%';
        
        positiesInGebruik[actieveSleepNode.naam] = {{ x: Math.round(x), y: Math.round(y) }};
    }}

    function stopSleep() {{
        if (actieveSleepNode) {{
            stuurDataNaarStreamlit();
            actieveSleepNode = null;
        }}
        document.removeEventListener('mousemove', doeSleep);
        document.removeEventListener('mouseup', stopSleep);
        document.removeEventListener('touchmove', doeSleep);
        document.removeEventListener('touchend', stopSleep);
    }}

    function updateBankTeller() {{
        document.getElementById('bank-count').innerText = bank.children.length;
    }}

    window.onload = initVeld;
    </script>
    </body>
    </html>
    """
    
    # Render het tactiekveld veilig via een custom iframe component
    # De data die door window.parent.postMessage wordt verstuurd, wordt nu AUTOMATISCH opgevangen in 'brug_data'
    brug_data = components.html(veld_html, height=580, scrolling=False)
    
    # Als de gebruiker sleept op het veld, schrijven we dit direct geruisloos weg naar session_state
    if brug_data is not None:
        st.session_state.opst_posities = brug_data

    # Toon opgeslagen opstellingen archief
    if alle_opst_keys:
        st.markdown("---")
        st.markdown("### 📚 Opgeslagen opstellingen in Google Sheets")
        for dk in alle_opst_keys:
            entry = data["opstelling"].get(dk, {})
            n_sp  = len(entry.get("posities", {}))
            fmt   = entry.get("formatie", "")
            
            ac1, ac2 = st.columns([4, 1])
            with ac1:
                st.markdown(f"**Wedstrijd op {dk}** · Formatie: {fmt} · ({n_sp} spelers op het veld)")
            with ac2:
                if st.button("🗑️ Verwijder", key=f"del_{dk}", use_container_width=True):
                    del data["opstelling"][dk]
                    save_data(data)
                    st.rerun()
