import streamlit as st
import pandas as pd
from datetime import date
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

if "data" not in st.session_state:
    st.session_state.data = load_data()
if "page" not in st.session_state:
    st.session_state.page = "aanwezigheid"

data = st.session_state.data

# Zorg dat opstelling key altijd bestaat
if "opstelling" not in data:
    data["opstelling"] = {}

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Inter:wght@400;600&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

h1 {
    font-family: 'Bebas Neue', sans-serif;
    font-size: clamp(1.8rem, 6vw, 3rem);
    letter-spacing: 2px;
    color: #00c853;
    margin-bottom: 0;
}
h2, h3 {
    font-family: 'Bebas Neue', sans-serif;
    letter-spacing: 1px;
    color: #e0e0e0;
    font-size: clamp(1.2rem, 4vw, 1.8rem);
}

.stat-card {
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
    border: 1px solid #00c853;
    border-radius: 12px;
    padding: clamp(10px, 3vw, 20px);
    text-align: center;
    margin-bottom: 10px;
}
.stat-card.oranje { border-color: #ffab40; }
.stat-number {
    font-size: clamp(1.4rem, 5vw, 2.5rem);
    font-weight: 700;
    color: #00c853;
    line-height: 1.2;
}
.stat-number.oranje { color: #ffab40; }
.stat-label {
    font-size: clamp(0.65rem, 2vw, 0.85rem);
    color: #9e9e9e;
    text-transform: uppercase;
    letter-spacing: 1px;
}

.speler-card {
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
    border: 1px solid #00c853;
    border-radius: 12px;
    padding: 14px;
    margin-bottom: 10px;
}
.badge {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 20px;
    font-size: clamp(0.65rem, 2vw, 0.78rem);
    font-weight: 600;
    margin: 2px 2px 4px 0;
}
.badge-groen  { background: #00c85322; color: #00c853; }
.badge-rood   { background: #ff525222; color: #ff5252; }
.badge-oranje { background: #ffab4022; color: #ffab40; }
.preview-naam { font-size: clamp(0.85rem, 3vw, 1rem); padding: 3px 0; }

/* Nav knoppen */
.nav-btn {
    display: inline-block;
    padding: 10px 24px;
    border-radius: 8px;
    font-family: 'Bebas Neue', sans-serif;
    font-size: 1.1rem;
    letter-spacing: 1px;
    cursor: pointer;
    border: 2px solid #00c853;
    color: #00c853;
    background: transparent;
    transition: all 0.2s;
    margin-right: 8px;
}
.nav-btn.active { background: #00c853; color: #0a0a0a; }

@media (max-width: 640px) {
    .stat-card { padding: 10px 6px; }
    .speler-card { padding: 12px; }
}
</style>
""", unsafe_allow_html=True)

# ─── Header + navigatie ────────────────────────────────────────────────────────
st.markdown("# ⚽ VOETBAL DASHBOARD BV O19-1")

col_nav1, col_nav2, _ = st.columns([1, 1, 3])
with col_nav1:
    if st.button("📋 Aanwezigheid", use_container_width=True,
                 type="primary" if st.session_state.page == "aanwezigheid" else "secondary"):
        st.session_state.page = "aanwezigheid"
        st.rerun()
with col_nav2:
    if st.button("🟢 Opstelling", use_container_width=True,
                 type="primary" if st.session_state.page == "opstelling" else "secondary"):
        st.session_state.page = "opstelling"
        st.rerun()

st.markdown("---")

# ══════════════════════════════════════════════════════════════════════════════
# PAGINA 1 — AANWEZIGHEID
# ══════════════════════════════════════════════════════════════════════════════
if st.session_state.page == "aanwezigheid":

    # ─── Sidebar ──────────────────────────────────────────────────────────────
    with st.sidebar:
        st.markdown("## 👤 Spelers beheren")
        with st.expander("➕ Nieuwe speler toevoegen", expanded=True):
            nieuwe_naam    = st.text_input("Naam", placeholder="Jan de Vries")
            nieuwe_positie = st.selectbox("Positie", ["Keeper", "Verdediger", "Middenvelder", "Aanvaller"])
            nieuwe_nummer  = st.number_input("Rugnummer", min_value=1, max_value=99, value=1)
            if st.button("✅ Speler toevoegen"):
                if nieuwe_naam.strip():
                    if nieuwe_naam.strip() in [s["naam"] for s in data["spelers"]]:
                        st.error("Speler bestaat al!")
                    else:
                        data["spelers"].append({"naam": nieuwe_naam.strip(), "positie": nieuwe_positie, "nummer": int(nieuwe_nummer)})
                        save_data(data)
                        st.success(f"✅ {nieuwe_naam} toegevoegd!")
                        st.rerun()
                else:
                    st.warning("Vul een naam in.")

        if data["spelers"]:
            with st.expander("🗑️ Speler verwijderen"):
                te_verwijderen = st.selectbox("Selecteer speler", [s["naam"] for s in data["spelers"]], key="del_select")
                if st.button("❌ Verwijder speler"):
                    data["spelers"] = [s for s in data["spelers"] if s["naam"] != te_verwijderen]
                    save_data(data)
                    st.success(f"🗑️ {te_verwijderen} verwijderd.")
                    st.rerun()

    # ─── Hulpfuncties ─────────────────────────────────────────────────────────
    echte_wedstrijden  = {k: v for k, v in data["trainingen"].items() if not k.endswith("_notitie")}
    totaal_spelers     = len(data["spelers"])
    totaal_wedstrijden = len(echte_wedstrijden)
    speler_namen       = [s["naam"] for s in data["spelers"]]

    def speler_stats(naam):
        aanwezig = afwezig = blessure = 0
        for sessie in echte_wedstrijden.values():
            if naam in sessie.get("blessure", []):
                blessure += 1
            elif naam in sessie.get("afwezig", []):
                afwezig += 1
            else:
                aanwezig += 1
        return aanwezig, afwezig, blessure

    # ─── Statistieken ─────────────────────────────────────────────────────────
    if echte_wedstrijden and data["spelers"]:
        alle_pct = []
        for sessie in echte_wedstrijden.values():
            n_af = len(sessie.get("afwezig", [])) + len(sessie.get("blessure", []))
            alle_pct.append((totaal_spelers - n_af) / totaal_spelers * 100 if totaal_spelers else 0)
        gem_aanwezigheid = round(sum(alle_pct) / len(alle_pct), 1)
        gem_blessure     = round(sum(len(s.get("blessure", [])) for s in echte_wedstrijden.values()) / totaal_wedstrijden, 1)
    else:
        gem_aanwezigheid = gem_blessure = 0

    r1c1, r1c2 = st.columns(2)
    with r1c1:
        st.markdown(f"""<div class="stat-card"><div class="stat-number">{totaal_spelers}</div><div class="stat-label">Spelers</div></div>""", unsafe_allow_html=True)
    with r1c2:
        st.markdown(f"""<div class="stat-card"><div class="stat-number">{totaal_wedstrijden}</div><div class="stat-label">Wedstrijden</div></div>""", unsafe_allow_html=True)

    r2c1, r2c2 = st.columns(2)
    with r2c1:
        st.markdown(f"""<div class="stat-card"><div class="stat-number">{gem_aanwezigheid}%</div><div class="stat-label">Gem. aanwezigheid</div></div>""", unsafe_allow_html=True)
    with r2c2:
        st.markdown(f"""<div class="stat-card oranje"><div class="stat-number oranje">{gem_blessure}</div><div class="stat-label">Gem. geblesseerd p/wedstrijd</div></div>""", unsafe_allow_html=True)

    st.markdown("---")

    tab1, tab2, tab3 = st.tabs(["📋 Registreren", "📊 Overzicht", "👥 Spelers"])

    with tab1:
        st.markdown("## 📋 Aanwezigheid registreren")
        if not data["spelers"]:
            st.info("Voeg eerst spelers toe via het menu links.")
        else:
            wedstrijd_datum   = st.date_input("📅 Datum wedstrijd", value=date.today())
            datum_key         = str(wedstrijd_datum)
            wedstrijd_notitie = st.text_input("📝 Notitie (optioneel)", placeholder="Bijv. Uitwedstrijd, bekerwedstrijd...")

            bestaande = echte_wedstrijden.get(datum_key, {"afwezig": [], "blessure": []})

            st.markdown("### Wie is er afwezig?")
            st.markdown("**❌ Afwezig**")
            afwezig_selectie = st.multiselect(
                "Afwezig", options=speler_namen,
                default=[n for n in bestaande.get("afwezig", []) if n in speler_namen],
                label_visibility="collapsed", key=f"afwezig_{datum_key}"
            )
            st.markdown("**🩹 Geblesseerd**")
            blessure_selectie = st.multiselect(
                "Geblesseerd", options=speler_namen,
                default=[n for n in bestaande.get("blessure", []) if n in speler_namen],
                label_visibility="collapsed", key=f"blessure_{datum_key}"
            )

            aanwezig_namen = [n for n in speler_namen if n not in afwezig_selectie and n not in blessure_selectie]

            st.markdown("---")
            with st.expander(f"✅ Aanwezig ({len(aanwezig_namen)})", expanded=True):
                for n in aanwezig_namen:
                    st.markdown(f'<div class="preview-naam">🟢 {n}</div>', unsafe_allow_html=True)
            with st.expander(f"❌ Afwezig ({len(afwezig_selectie)})"):
                for n in afwezig_selectie:
                    st.markdown(f'<div class="preview-naam">🔴 {n}</div>', unsafe_allow_html=True)
            with st.expander(f"🩹 Geblesseerd ({len(blessure_selectie)})"):
                for n in blessure_selectie:
                    st.markdown(f'<div class="preview-naam">🟠 {n}</div>', unsafe_allow_html=True)

            st.markdown("")
            if st.button("💾 Opslaan", type="primary"):
                data["trainingen"][datum_key] = {"afwezig": afwezig_selectie, "blessure": blessure_selectie}
                if wedstrijd_notitie:
                    data["trainingen"][f"{datum_key}_notitie"] = wedstrijd_notitie
                save_data(data)
                st.success(f"✅ Aanwezigheid voor {wedstrijd_datum.strftime('%d %B %Y')} opgeslagen!")

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
                    sessie = echte_wedstrijden[datum]
                    if naam in sessie.get("blessure", []):
                        row[datum] = "🩹"
                    elif naam in sessie.get("afwezig", []):
                        row[datum] = "❌"
                    else:
                        row[datum] = "✅"
                row["✅"] = aanwezig
                row["❌"] = afwezig
                row["🩹"] = blessure
                row["%"]  = f"{round(aanwezig / len(datum_lijst) * 100)}%" if datum_lijst else "0%"
                rows.append(row)

            df = pd.DataFrame(rows)
            st.dataframe(df, use_container_width=True, height=400)

            st.markdown("### 📊 Statistieken per speler")
            namen      = [r["Speler"] for r in rows]
            st.markdown("**✅ Aanwezig**")
            st.bar_chart(pd.DataFrame({"Aanwezig": [r["✅"] for r in rows]}, index=namen))
            st.markdown("**❌ Afwezig**")
            st.bar_chart(pd.DataFrame({"Afwezig":  [r["❌"] for r in rows]}, index=namen))
            st.markdown("**🩹 Geblesseerd**")
            st.bar_chart(pd.DataFrame({"Blessure": [r["🩹"] for r in rows]}, index=namen))

            st.markdown("### 📅 Overzicht per wedstrijd")
            wedstrijd_data = []
            for datum in sorted(echte_wedstrijden.keys()):
                sessie  = echte_wedstrijden[datum]
                n_af    = len(sessie.get("afwezig",  []))
                n_bl    = len(sessie.get("blessure", []))
                wedstrijd_data.append({"Datum": datum, "✅": totaal_spelers - n_af - n_bl, "❌": n_af, "🩹": n_bl,
                                       "Notitie": data["trainingen"].get(f"{datum}_notitie", "")})
            df_w = pd.DataFrame(wedstrijd_data).set_index("Datum")
            st.dataframe(df_w, use_container_width=True)
            st.markdown("### 📈 Trend per wedstrijd")
            st.bar_chart(pd.DataFrame(wedstrijd_data).set_index("Datum")[["✅", "❌", "🩹"]])

    with tab3:
        st.markdown("## 👥 Spelersoverzicht")
        if not data["spelers"]:
            st.info("Nog geen spelers toegevoegd.")
        else:
            cols = st.columns(2)
            for i, speler in enumerate(sorted(data["spelers"], key=lambda x: x["nummer"])):
                naam = speler["naam"]
                aanwezig, afwezig, blessure = speler_stats(naam)
                totaal = len(echte_wedstrijden)
                pct    = round(aanwezig / totaal * 100) if totaal else 0
                with cols[i % 2]:
                    st.markdown(f"""
                    <div class="speler-card">
                        <div style="font-size:1.4rem">⚽</div>
                        <div style="font-family:'Bebas Neue',sans-serif;font-size:1.1rem;color:#fff">#{speler['nummer']} {naam}</div>
                        <div style="color:#9e9e9e;font-size:0.8rem;margin-bottom:8px">{speler['positie']}</div>
                        <span class="badge badge-groen">✅ {aanwezig}x</span>
                        <span class="badge badge-rood">❌ {afwezig}x</span>
                        <span class="badge badge-oranje">🩹 {blessure}x</span>
                        <hr style="border-color:#333;margin:8px 0">
                        <div style="color:#00c853;font-weight:600">{pct}% aanwezig</div>
                        <div style="color:#9e9e9e;font-size:0.78rem">{aanwezig}/{totaal} wedstrijden</div>
                    </div>""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGINA 2 — OPSTELLING
# ══════════════════════════════════════════════════════════════════════════════
else:
    st.markdown("## 🟢 Opstelling")

    speler_namen = [s["naam"] for s in data["spelers"]]
    spelers_json = json.dumps(data["spelers"])
    opst_json    = json.dumps(data.get("opstelling", {}))

    opstelling_html = f"""
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    background: #0d1117;
    font-family: 'Inter', sans-serif;
    color: #fff;
    padding: 12px;
    min-height: 100vh;
  }}

  .container {{
    display: flex;
    flex-direction: column;
    gap: 16px;
    max-width: 700px;
    margin: 0 auto;
  }}

  h2 {{
    font-family: 'Bebas Neue', cursive;
    color: #00c853;
    font-size: 1.4rem;
    letter-spacing: 1px;
  }}

  /* ── Veld ── */
  .veld-wrap {{
    position: relative;
    width: 100%;
    aspect-ratio: 68 / 105;
    max-height: 70vh;
    margin: 0 auto;
  }}
  #veld {{
    width: 100%;
    height: 100%;
    background: #2d7a3a;
    border-radius: 8px;
    border: 3px solid #fff;
    position: relative;
    overflow: hidden;
    touch-action: none;
  }}

  /* Veldlijnen */
  #veld::before {{
    content: '';
    position: absolute;
    top: 50%; left: 0; right: 0;
    height: 2px;
    background: rgba(255,255,255,0.5);
  }}
  .cirkel {{
    position: absolute;
    top: 50%; left: 50%;
    transform: translate(-50%, -50%);
    width: 20%; aspect-ratio: 1;
    border: 2px solid rgba(255,255,255,0.5);
    border-radius: 50%;
    pointer-events: none;
  }}
  .strafschop-boven, .strafschop-onder {{
    position: absolute;
    left: 20%; right: 20%;
    height: 14%;
    border: 2px solid rgba(255,255,255,0.5);
    pointer-events: none;
  }}
  .strafschop-boven {{ top: 0; border-top: none; border-radius: 0 0 6px 6px; }}
  .strafschop-onder {{ bottom: 0; border-bottom: none; border-radius: 6px 6px 0 0; }}
  .goal-boven, .goal-onder {{
    position: absolute;
    left: 35%; right: 35%;
    height: 4%;
    border: 2px solid rgba(255,255,255,0.7);
    background: rgba(255,255,255,0.08);
    pointer-events: none;
  }}
  .goal-boven {{ top: 0; border-top: none; }}
  .goal-onder {{ bottom: 0; border-bottom: none; }}

  /* Grasstrepen */
  .gras-streep {{
    position: absolute;
    top: 0; bottom: 0;
    width: 9.09%;
    background: rgba(0,0,0,0.06);
    pointer-events: none;
  }}

  /* ── Speler op het veld ── */
  .speler-token {{
    position: absolute;
    transform: translate(-50%, -50%);
    cursor: grab;
    touch-action: none;
    user-select: none;
    z-index: 10;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 2px;
  }}
  .speler-token:active {{ cursor: grabbing; }}
  .token-cirkel {{
    width: clamp(32px, 7vw, 44px);
    height: clamp(32px, 7vw, 44px);
    border-radius: 50%;
    background: #00c853;
    border: 2px solid #fff;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 700;
    font-size: clamp(10px, 2.5vw, 14px);
    color: #0a1a0a;
    box-shadow: 0 2px 8px rgba(0,0,0,0.5);
    transition: box-shadow 0.15s;
  }}
  .speler-token:hover .token-cirkel,
  .speler-token.dragging .token-cirkel {{
    box-shadow: 0 4px 16px rgba(0,200,83,0.6);
  }}
  .token-naam {{
    background: rgba(0,0,0,0.75);
    color: #fff;
    font-size: clamp(7px, 1.8vw, 10px);
    padding: 1px 4px;
    border-radius: 3px;
    white-space: nowrap;
    max-width: clamp(50px, 12vw, 70px);
    overflow: hidden;
    text-overflow: ellipsis;
    text-align: center;
  }}

  /* ── Bench ── */
  .bench {{
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 10px;
    padding: 12px;
  }}
  .bench h2 {{ margin-bottom: 10px; font-size: 1rem; color: #ccc; }}
  .bench-lijst {{
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
  }}
  .bench-item {{
    display: flex;
    align-items: center;
    gap: 6px;
    background: #21262d;
    border: 1px solid #30363d;
    border-radius: 20px;
    padding: 5px 12px 5px 6px;
    cursor: pointer;
    transition: border-color 0.15s, background 0.15s;
    font-size: clamp(11px, 2.5vw, 13px);
  }}
  .bench-item:hover {{ border-color: #00c853; background: #00c85315; }}
  .bench-item.geplaatst {{ opacity: 0.35; cursor: default; pointer-events: none; }}
  .bench-nr {{
    width: 26px; height: 26px;
    border-radius: 50%;
    background: #00c853;
    color: #0a1a0a;
    font-weight: 700;
    font-size: 11px;
    display: flex; align-items: center; justify-content: center;
    flex-shrink: 0;
  }}

  /* ── Knoppen ── */
  .knoppen {{
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
  }}
  .btn {{
    flex: 1;
    min-width: 120px;
    padding: 10px 16px;
    border-radius: 8px;
    border: none;
    font-family: 'Bebas Neue', cursive;
    font-size: 1rem;
    letter-spacing: 1px;
    cursor: pointer;
    transition: opacity 0.15s;
  }}
  .btn:hover {{ opacity: 0.85; }}
  .btn-groen {{ background: #00c853; color: #0a1a0a; }}
  .btn-grijs  {{ background: #21262d; color: #ccc; border: 1px solid #30363d; }}

  .opgeslagen {{ color: #00c853; font-size: 0.9rem; display: none; }}
  .formation-select {{
    background: #21262d;
    color: #fff;
    border: 1px solid #30363d;
    border-radius: 8px;
    padding: 8px 12px;
    font-size: 0.9rem;
    cursor: pointer;
    flex: 1;
    min-width: 140px;
  }}
</style>
<link href="https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Inter:wght@400;600&display=swap" rel="stylesheet">
</head>
<body>
<div class="container">

  <div style="display:flex;align-items:center;gap:12px;flex-wrap:wrap;">
    <h2>🟢 OPSTELLING</h2>
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

  <!-- Veld -->
  <div class="veld-wrap">
    <div id="veld">
      <div class="cirkel"></div>
      <div class="strafschop-boven"></div>
      <div class="strafschop-onder"></div>
      <div class="goal-boven"></div>
      <div class="goal-onder"></div>
      <!-- grasstrepen -->
      <div class="gras-streep" style="left:0%"></div>
      <div class="gras-streep" style="left:18.18%"></div>
      <div class="gras-streep" style="left:36.36%"></div>
      <div class="gras-streep" style="left:54.54%"></div>
      <div class="gras-streep" style="left:72.72%"></div>
      <div class="gras-streep" style="left:90.9%"></div>
    </div>
  </div>

  <!-- Bank -->
  <div class="bench">
    <h2>🪑 BANK — klik op speler om te plaatsen</h2>
    <div class="bench-lijst" id="bench-lijst"></div>
  </div>

  <!-- Knoppen -->
  <div class="knoppen">
    <button class="btn btn-groen" onclick="slaOpOp()">💾 Opstelling opslaan</button>
    <button class="btn btn-grijs"  onclick="reset()">🔄 Reset veld</button>
  </div>
  <span class="opgeslagen" id="opgeslagen-msg">✅ Opstelling opgeslagen!</span>
</div>

<script>
const SPELERS  = {spelers_json};
const OPST_IN  = {opst_json};

// State
let posities = {{}};   // naam -> {{x%, y%}}
let plaatsMode = null; // naam van speler die geplaatst wordt

// ── Init ──────────────────────────────────────────────────────────────────
function init() {{
  // Laad opgeslagen opstelling
  if (OPST_IN && Object.keys(OPST_IN).length > 0) {{
    posities = OPST_IN;
  }}
  renderBench();
  renderVeld();
}}

// ── Bank ──────────────────────────────────────────────────────────────────
function renderBench() {{
  const lijst = document.getElementById('bench-lijst');
  lijst.innerHTML = '';
  SPELERS.sort((a,b) => a.nummer - b.nummer).forEach(s => {{
    const opVeld = posities.hasOwnProperty(s.naam);
    const div = document.createElement('div');
    div.className = 'bench-item' + (opVeld ? ' geplaatst' : '');
    div.id = 'bench-' + s.naam;
    div.innerHTML = `<div class="bench-nr">${{s.nummer}}</div><span>${{s.naam}}</span>`;
    if (!opVeld) {{
      div.onclick = () => startPlaatsen(s.naam);
    }}
    lijst.appendChild(div);
  }});

  // Plaatsmodus hint
  if (plaatsMode) {{
    const hint = document.createElement('div');
    hint.style.cssText = 'width:100%;color:#00c853;font-size:0.85rem;margin-top:6px;';
    hint.textContent = `Tik op het veld om ${{plaatsMode}} te plaatsen — of klik hier om te annuleren`;
    hint.style.cursor = 'pointer';
    hint.onclick = () => {{ plaatsMode = null; renderBench(); }};
    lijst.appendChild(hint);
  }}
}}

// ── Plaatsmodus ───────────────────────────────────────────────────────────
function startPlaatsen(naam) {{
  plaatsMode = naam;
  renderBench();
}}

document.getElementById('veld').addEventListener('click', function(e) {{
  if (!plaatsMode) return;
  const rect  = this.getBoundingClientRect();
  const xPct  = ((e.clientX - rect.left) / rect.width)  * 100;
  const yPct  = ((e.clientY - rect.top)  / rect.height) * 100;
  posities[plaatsMode] = {{ x: xPct, y: yPct }};
  plaatsMode = null;
  renderBench();
  renderVeld();
}});

// ── Veld renderen ─────────────────────────────────────────────────────────
function renderVeld() {{
  // Verwijder bestaande tokens
  document.querySelectorAll('.speler-token').forEach(el => el.remove());
  const veld = document.getElementById('veld');

  Object.entries(posities).forEach(([naam, pos]) => {{
    const speler = SPELERS.find(s => s.naam === naam);
    if (!speler) return;

    const token = document.createElement('div');
    token.className = 'speler-token';
    token.id = 'token-' + naam;
    token.style.left = pos.x + '%';
    token.style.top  = pos.y + '%';
    token.innerHTML  = `
      <div class="token-cirkel">${{speler.nummer}}</div>
      <div class="token-naam">${{naam.split(' ')[0]}}</div>
    `;

    // Verwijder bij dubbelklik
    token.addEventListener('dblclick', (e) => {{
      e.stopPropagation();
      delete posities[naam];
      renderBench();
      renderVeld();
    }});

    // ── Drag (muis) ───────────────────────────────────────────────────────
    let dragging = false, startX, startY, startLeft, startTop;

    token.addEventListener('mousedown', (e) => {{
      if (plaatsMode) return;
      e.preventDefault();
      dragging  = true;
      startX    = e.clientX;
      startY    = e.clientY;
      startLeft = pos.x;
      startTop  = pos.y;
      token.classList.add('dragging');
    }});

    document.addEventListener('mousemove', (e) => {{
      if (!dragging) return;
      const rect   = veld.getBoundingClientRect();
      const dxPct  = ((e.clientX - startX) / rect.width)  * 100;
      const dyPct  = ((e.clientY - startY) / rect.height) * 100;
      const newX   = Math.max(2, Math.min(98, startLeft + dxPct));
      const newY   = Math.max(2, Math.min(98, startTop  + dyPct));
      token.style.left = newX + '%';
      token.style.top  = newY + '%';
      posities[naam]   = {{ x: newX, y: newY }};
    }});

    document.addEventListener('mouseup', () => {{
      if (dragging) {{ dragging = false; token.classList.remove('dragging'); }}
    }});

    // ── Drag (touch) ─────────────────────────────────────────────────────
    let touchStartX, touchStartY, touchStartLeft, touchStartTop;

    token.addEventListener('touchstart', (e) => {{
      if (plaatsMode) return;
      const t      = e.touches[0];
      touchStartX    = t.clientX;
      touchStartY    = t.clientY;
      touchStartLeft = pos.x;
      touchStartTop  = pos.y;
      token.classList.add('dragging');
    }}, {{ passive: true }});

    token.addEventListener('touchmove', (e) => {{
      e.preventDefault();
      const t      = e.touches[0];
      const rect   = veld.getBoundingClientRect();
      const dxPct  = ((t.clientX - touchStartX) / rect.width)  * 100;
      const dyPct  = ((t.clientY - touchStartY) / rect.height) * 100;
      const newX   = Math.max(2, Math.min(98, touchStartLeft + dxPct));
      const newY   = Math.max(2, Math.min(98, touchStartTop  + dyPct));
      token.style.left = newX + '%';
      token.style.top  = newY + '%';
      posities[naam]   = {{ x: newX, y: newY }};
    }}, {{ passive: false }});

    token.addEventListener('touchend', () => {{
      token.classList.remove('dragging');
    }});

    veld.appendChild(token);
  }});
}}

// ── Formatie ──────────────────────────────────────────────────────────────
const FORMATIES = {{
  '4-3-3':   [[50,88],[18,72],[38,72],[62,72],[82,72],[30,52],[50,48],[70,52],[20,28],[50,22],[80,28]],
  '4-4-2':   [[50,88],[18,72],[38,72],[62,72],[82,72],[18,52],[38,52],[62,52],[82,52],[35,25],[65,25]],
  '4-2-3-1': [[50,88],[18,72],[38,72],[62,72],[82,72],[35,58],[65,58],[20,40],[50,38],[80,40],[50,18]],
  '3-5-2':   [[50,88],[25,72],[50,70],[75,72],[15,52],[35,50],[55,50],[75,50],[90,52],[35,25],[65,25]],
  '5-3-2':   [[50,88],[10,72],[28,72],[50,68],[72,72],[90,72],[25,50],[50,48],[75,50],[35,25],[65,25]],
  '3-4-3':   [[50,88],[25,72],[50,70],[75,72],[18,52],[40,50],[60,50],[82,52],[20,28],[50,22],[80,28]],
}};

function zetFormatie() {{
  const f = document.getElementById('formatie').value;
  if (!f) return;
  const coords = FORMATIES[f];
  const gesorteerd = [...SPELERS].sort((a,b) => a.nummer - b.nummer).slice(0, 11);
  posities = {{}};
  gesorteerd.forEach((s, i) => {{
    if (coords[i]) posities[s.naam] = {{ x: coords[i][0], y: coords[i][1] }};
  }});
  renderBench();
  renderVeld();
}}

// ── Opslaan ───────────────────────────────────────────────────────────────
function slaOpOp() {{
  // Stuur naar Streamlit via query param hack
  const encoded = encodeURIComponent(JSON.stringify(posities));
  const url = new URL(window.location.href);
  url.searchParams.set('opstelling', encoded);
  window.history.replaceState(null, '', url.toString());

  // Toon bevestiging
  const msg = document.getElementById('opgeslagen-msg');
  msg.style.display = 'block';
  setTimeout(() => msg.style.display = 'none', 3000);
}}

// ── Reset ──────────────────────────────────────────────────────────────────
function reset() {{
  posities = {{}};
  plaatsMode = null;
  document.getElementById('formatie').value = '';
  renderBench();
  renderVeld();
}}

init();
</script>
</body>
</html>
"""

    st.components.v1.html(opstelling_html, height=900, scrolling=True)

    st.info("💡 **Tip:** Klik een speler op de bank aan om hem te plaatsen, tik dan op het veld. Sleep tokens om ze te verplaatsen. Dubbelklik een token om hem te verwijderen. Kies een formatie om automatisch op te stellen.")
