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

# Zorg dat de mappen altijd correct aanwezig zijn
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
    st.info("Aanwezigheidsbeheer module is actief.")

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

    # ── Knoppen boven het veld ─────────────────────────────────────────
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
        posities_te_slaan = st.session_state.get("opst_posities", {})
        formatie_te_slaan = st.session_state.get("opst_formatie", "")
        if not posities_te_slaan:
            st.warning("⚠️ Er staan geen spelers op het veld. Plaats eerst spelers.")
        else:
            data["opstellingen"][datum_key] = {
                "posities": posities_te_slaan,
                "formatie": formatie_te_slaan,
            }
            save_data(data)
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
            st.rerun()
        except json.JSONDecodeError:
            pass

    # ── INTERACTIEF SPEELVELD HTML + JAVASCRIPT ────────────────────────────────────────
    spelers_json = json.dumps(data["spelers"], ensure_ascii=False)
    posities_json_str = json.dumps(st.session_state.opst_posities, ensure_ascii=False)
    formatie_json_str = json.dumps(st.session_state.opst_formatie, ensure_ascii=False)
    datum_json = json.dumps(datum_key, ensure_ascii=False)

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

/* Veld Opbouw */
.veld-wrap {{ width:100%; aspect-ratio:68/105; max-height:65vh; margin:0 auto; position:relative; }}
#veld {{
    width:100%; height:100%; background:#1B6B38; border:4px solid #FFF; border-radius:8px;
    position:relative; overflow:hidden; box-shadow:0 6px 16px rgba(0,0,0,0.15);
    background-image: linear-gradient(rgba(255,255,255,0.05) 50%, transparent 50%);
    background-size: 100% 18%;
}}
.lijn-midden {{ position:absolute; top:50%; left:0; width:100%; height:2px; background:#FFF; transform:translateY(-50%); }}
.cirkel {{ position:absolute; top:50%; left:50%; width:25%; aspect-ratio:1; border:2px solid #FFF; border-radius:50%; transform:translate(-50%,-50%); }}
.gb,.go {{ position:absolute; left:35%; right:35%; height:4%; border:2px solid rgba(255,255,255,.8); background:rgba(255,255,255,.1); pointer-events:none; }}
.gb {{ top:0; border-top:none; }} .go {{ bottom:0; border-bottom:none; }}
.gs {{ position:absolute; top:0; bottom:0; width:9.09%; background:rgba(0,0,0,.08); pointer-events:none; }}

/* Speler Tokens */
.token {{ position:absolute; transform:translate(-50%,-50%); cursor:grab; touch-action:none; user-select:none; z-index:10; display:flex; flex-direction:column; align-items:center; gap:2px; }}
.token:active {{ cursor:grabbing; }}
.tc {{
    width:clamp(32px,9vw,46px); height:clamp(32px,9vw,46px); border-radius:50%;
    background:linear-gradient(135deg, #FF6600, #C44A00); color:#FFF; font-weight:700;
    display:flex; align-items:center; justify-content:center; font-size:clamp(12px,3.5vw,16px);
    box-shadow:0 4px 8px rgba(0,0,0,0.3); border:2px solid #FFF; transition: transform 0.1s;
}}
.token.dragging .tc {{ transform: scale(1.15); box-shadow: 0 8px 16px rgba(0,0,0,0.4); }}
.tn {{
    background:rgba(0,0,0,0.75); color:#FFF; font-size:clamp(9px,2.8vw,12px); padding:2px 6px;
    border-radius:4px; font-weight:600; white-space:nowrap; pointer-events:none;
    max-width:clamp(44px,12vw,64px); overflow:hidden; text-overflow:ellipsis; text-align:center;
    border:1px solid #C44A00;
}}

/* Wisselbank */
.bank {{ background:#F5F5F5; border:1px solid #BBB; border-top:4px solid #C44A00; border-radius:8px; padding:10px; }}
.bank-titel {{ font-family:'Bebas Neue',cursive; color:#333; letter-spacing:1px; font-size:.95rem; margin-bottom:8px; }}
.bank-lijst {{ display:flex; flex-wrap:wrap; gap:6px; }}
.bank-item {{
    background:#FFF; border:1px solid #CCC; border-radius:6px; padding:4px 8px;
    font-size:.85rem; font-weight:600; cursor:pointer; display:flex; align-items:center; gap:6px;
    box-shadow:0 2px 4px rgba(0,0,0,0.05); user-select:none;
}}
.bank-item:hover {{ border-color:#C44A00; background:#FFF5EE; }}
.bank-item.selected {{ background:#FF6600 !important; color:#FFF !important; border-color:#C44A00; }}
.bnr {{
    background:#EAEAEA; color:#444; width:18px; height:18px; border-radius:50%;
    font-family:'Bebas Neue',cursive; font-size:12px; display:flex; align-items:center; justify-content:center; flex-shrink:0;
}}
.bank-item.selected .bnr {{ background:#FFF; color:#C44A00; }}
.hint {{ color:#C44A00; font-size:.8rem; margin-top:6px; width:100%; cursor:pointer; text-decoration:underline; font-weight:600; }}

/* Formatie regels */
.form-row {{ display:flex; align-items:center; gap:10px; flex-wrap:wrap; }}
.fsel {{ background:#fff; color:#111; border:2px solid #666; border-radius:8px; padding:7px 11px; font-size:.88rem; cursor:pointer; flex:1; min-width:130px; }}
.fsel:focus {{ outline:3px solid #C44A00; outline-offset:2px; }}
.status {{ font-family:'Bebas Neue',cursive; letter-spacing:1px; font-size:.9rem; min-height:1.3rem; font-weight:700; }}
</style>
<link href="https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Inter:wght@400;600;700&display=swap" rel="stylesheet">
</head>
<body>
<div class="wrap">
    <div class="form-row">
        <h3>📋 OPSTELLING FORMATIE:</h3>
        <select class="fsel" id="formatieSelect" onchange="onFormatieChange()">
            <option value="">-- Vrije opstelling --</option>
            <option value="4-3-3">4-3-3</option>
            <option value="4-4-2">4-4-2</option>
            <option value="3-5-2">3-5-2</option>
            <option value="3-4-3">3-4-3</option>
            <option value="5-3-2">5-3-2</option>
        </select>
    </div>
    <div class="veld-wrap">
        <div id="veld">
            <div class="lijn-midden"></div>
            <div class="cirkel"></div>
            <div class="gb"></div><div class="go"></div>
            <div class="gs" style="left:18.18%"></div><div class="gs" style="left:36.36%"></div>
            <div class="gs" style="left:54.54%"></div><div class="gs" style="left:72.72%"></div><div class="gs" style="left:90.9%"></div>
        </div>
    </div>
    <div class="bank">
        <div class="bank-titel">🪑 BANK — klik speler, tik dan op het veld</div>
        <div class="bank-lijst" id="bank"></div>
    </div>
    <div class="status" id="status"></div>
</div>

<script>
const SPELERS = {spelers_json};
const INIT_POS = {posities_json_str};
const INIT_FMT = {formatie_json_str};

let posities = structuredClone(INIT_POS);
let plaatsMode = null;

function stuurNaarStreamlit() {{
    const fmt = document.getElementById('formatieSelect').value;
    const payload = JSON.stringify({{ posities: posities, formatie: fmt }});
    
    // Zoek de onzichtbare invoerbrug in het Streamlit parent frame
    const inputEl = window.parent.document.querySelector('input[aria-label="opst_brug_input"]');
    if(inputEl) {{
        inputEl.value = payload;
        inputEl.dispatchEvent(new Event('input', {{ bubbles: true }}));
    }}
}}

function onChange() {{
    stuurNaarStreamlit();
}}

function renderBank() {{
    const lijst = document.getElementById('bank');
    lijst.innerHTML = '';
    SPELERS.forEach(s => {{
        const opVeld = posities[s.naam];
        const div = document.createElement('div');
        div.className = 'bank-item' + (plaatsMode === s.naam ? ' selected' : '');
        if(opVeld) div.style.opacity = '0.4';
        div.innerHTML = `<div class="bnr">${{s.nummer}}</div> <span>${{s.naam}}</span>`;
        if (!opVeld) div.onclick = () => {{ plaatsMode=(plaatsMode===s.naam)?null:s.naam; renderBank(); }};
        lijst.appendChild(div);
    }});
    
    if (plaatsMode) {{
        const hint = document.createElement('div');
        hint.className = 'hint';
        hint.textContent = `Tik op het veld om ${{plaatsMode}} te plaatsen (of klik hier om te annuleren)`;
        hint.onclick = () => {{ plaatsMode=null; renderBank(); }};
        lijst.appendChild(hint);
    }}
}}

document.getElementById('veld').addEventListener('click', function(e) {{
    if (!plaatsMode) return;
    const r = this.getBoundingClientRect();
    const x = ((e.clientX - r.left) / r.width) * 100;
    const y = ((e.clientY - r.top) / r.height) * 100;
    
    posities[plaatsMode] = {{ x: Math.max(2,Math.min(98,x)), y: Math.max(2,Math.min(98,y)) }};
    plaatsMode = null;
    renderBank();
    renderVeld();
    onChange();
}});

function renderVeld() {{
    const veld = document.getElementById('veld');
    document.querySelectorAll('.token').forEach(t => t.remove());
    
    Object.keys(posities).forEach(naam => {{
        const pos = posities[naam];
        const sp = SPELERS.find(s => s.naam === naam) || {{ nummer: '?' }};
        const tok = document.createElement('div');
        tok.className = 'token';
        tok.style.left = pos.x + '%';
        tok.style.top = pos.y + '%';
        tok.innerHTML = `<div class="tc">${{sp.nummer}}</div><div class="tn">${{naam.split(' ')[0]}}</div>`;
        
        // Dubbelklik om speler terug naar bank te sturen
        tok.addEventListener('dblclick', e => {{
            e.stopPropagation();
            delete posities[naam];
            renderBank();
            renderVeld();
            onChange();
        }});
        
        // --- Drag-and-drop Muis functionaliteit ---
        let dr = false, sX, sY, sL, sT;
        tok.addEventListener('mousedown', e => {{
            if(plaatsMode) return;
            e.preventDefault();
            dr = true; sX = e.clientX; sY = e.clientY; sL = pos.x; sT = pos.y;
            tok.classList.add('dragging');
        }});
        
        document.addEventListener('mousemove', e => {{
            if(!dr) return;
            const r = veld.getBoundingClientRect();
            let nx = sL + ((e.clientX - sX) / r.width) * 100;
            let ny = sT + ((e.clientY - sY) / r.height) * 100;
            pos.x = Math.max(2, Math.min(98, nx));
            pos.y = Math.max(2, Math.min(98, ny));
            tok.style.left = pos.x + '%';
            tok.style.top = pos.y + '%';
        }});
        
        document.addEventListener('mouseup', () => {{
            if(dr) {{ dr = false; tok.classList.remove('dragging'); onChange(); }}
        }});

        // --- Touchscreen/Mobiel Dragfunctionaliteit ---
        let tX, tY, tL, tT;
        tok.addEventListener('touchstart', e => {{
            if(plaatsMode) return;
            const t = e.touches[0];
            tX = t.clientX; tY = t.clientY; tL = pos.x; tT = pos.y;
            tok.classList.add('dragging');
        }}, {{ passive: true }});
        
        tok.addEventListener('touchmove', e => {{
            if(plaatsMode) return;
            const t = e.touches[0];
            const r = veld.getBoundingClientRect();
            let nx = tL + ((t.clientX - tX) / r.width) * 100;
            let ny = tT + ((t.clientY - tY) / r.height) * 100;
            pos.x = Math.max(2, Math.min(98, nx));
            pos.y = Math.max(2, Math.min(98, ny));
            tok.style.left = pos.x + '%';
            tok.style.top = pos.y + '%';
        }}, {{ passive: true }});
        
        tok.addEventListener('touchend', () => {{
            tok.classList.remove('dragging');
            onChange();
        }});
        
        veld.appendChild(tok);
    }});
}}

function onFormatieChange() {{
    onChange();
}}

// Initialisatie van het iframe
document.getElementById('formatieSelect').value = INIT_FMT;
renderBank();
renderVeld();
</script>
</body>
</html>"""

    st.components.v1.html(veld_html, height=750, scrolling=False)
