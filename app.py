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
    return {"spelers": [], "trainingen": {}}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

if "data" not in st.session_state:
    st.session_state.data = load_data()

data = st.session_state.data

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Inter:wght@400;600&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

h1 {
    font-family: 'Bebas Neue', sans-serif;
    font-size: clamp(1.8rem, 6vw, 3rem);
    letter-spacing: 2px;
    color: #00c853;
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

/* Mobiel: multiselect en inputs wat ruimer */
.stMultiSelect > div { font-size: clamp(0.85rem, 3vw, 1rem); }
.stButton > button {
    font-size: clamp(0.85rem, 3vw, 1rem);
    padding: 0.5rem 1rem;
    width: 100%;
}

/* Aanwezigheidslijst op mobiel netjes onder elkaar */
.preview-naam {
    font-size: clamp(0.85rem, 3vw, 1rem);
    padding: 3px 0;
}

@media (max-width: 640px) {
    .stat-card { padding: 10px 6px; }
    .speler-card { padding: 12px; }
}
</style>
""", unsafe_allow_html=True)

# ─── Header ───────────────────────────────────────────────────────────────────
st.markdown("# ⚽ VOETBAL DASHBOARD BV O19-1")
st.markdown("---")

# ─── Sidebar ──────────────────────────────────────────────────────────────────
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

# ─── Hulpfuncties ─────────────────────────────────────────────────────────────
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

# ─── Statistieken: 2x2 grid op mobiel, 4 kolommen op desktop ─────────────────
if echte_wedstrijden and data["spelers"]:
    alle_pct = []
    for sessie in echte_wedstrijden.values():
        n_af = len(sessie.get("afwezig", [])) + len(sessie.get("blessure", []))
        alle_pct.append((totaal_spelers - n_af) / totaal_spelers * 100 if totaal_spelers else 0)
    gem_aanwezigheid = round(sum(alle_pct) / len(alle_pct), 1)
    gem_blessure     = round(sum(len(s.get("blessure", [])) for s in echte_wedstrijden.values()) / totaal_wedstrijden, 1)
else:
    gem_aanwezigheid = gem_blessure = 0

# Rij 1
r1c1, r1c2 = st.columns(2)
with r1c1:
    st.markdown(f"""<div class="stat-card">
        <div class="stat-number">{totaal_spelers}</div>
        <div class="stat-label">Spelers</div>
    </div>""", unsafe_allow_html=True)
with r1c2:
    st.markdown(f"""<div class="stat-card">
        <div class="stat-number">{totaal_wedstrijden}</div>
        <div class="stat-label">Wedstrijden</div>
    </div>""", unsafe_allow_html=True)

# Rij 2
r2c1, r2c2 = st.columns(2)
with r2c1:
    st.markdown(f"""<div class="stat-card">
        <div class="stat-number">{gem_aanwezigheid}%</div>
        <div class="stat-label">Gem. aanwezigheid</div>
    </div>""", unsafe_allow_html=True)
with r2c2:
    st.markdown(f"""<div class="stat-card oranje">
        <div class="stat-number oranje">{gem_blessure}</div>
        <div class="stat-label">Gem. geblesseerd p/wedstrijd</div>
    </div>""", unsafe_allow_html=True)

st.markdown("---")

# ─── Tabs ─────────────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["📋 Registreren", "📊 Overzicht", "👥 Spelers"])

# ══════════════════════════════════════════════════════════════════════════════
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

        # Op mobiel: drie losse expanders i.p.v. kolommen
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

# ══════════════════════════════════════════════════════════════════════════════
with tab2:
    st.markdown("## 📊 Aanwezigheidsoverzicht")
    if not echte_wedstrijden or not data["spelers"]:
        st.info("Nog geen aanwezigheidsdata beschikbaar.")
    else:
        datum_lijst = sorted(echte_wedstrijden.keys(), reverse=True)

        st.markdown("### 📋 Overzicht per speler")
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
        aanwezig_l = [r["✅"]     for r in rows]
        afwezig_l  = [r["❌"]     for r in rows]
        blessure_l = [r["🩹"]     for r in rows]

        st.markdown("**✅ Aanwezig**")
        st.bar_chart(pd.DataFrame({"Aanwezig": aanwezig_l}, index=namen))
        st.markdown("**❌ Afwezig**")
        st.bar_chart(pd.DataFrame({"Afwezig": afwezig_l}, index=namen))
        st.markdown("**🩹 Geblesseerd**")
        st.bar_chart(pd.DataFrame({"Blessure": blessure_l}, index=namen))

        st.markdown("### 📅 Overzicht per wedstrijd")
        wedstrijd_data = []
        for datum in sorted(echte_wedstrijden.keys()):
            sessie  = echte_wedstrijden[datum]
            n_af    = len(sessie.get("afwezig",  []))
            n_bl    = len(sessie.get("blessure", []))
            n_aan   = totaal_spelers - n_af - n_bl
            notitie = data["trainingen"].get(f"{datum}_notitie", "")
            wedstrijd_data.append({"Datum": datum, "✅": n_aan, "❌": n_af, "🩹": n_bl, "Notitie": notitie})

        df_w = pd.DataFrame(wedstrijd_data).set_index("Datum")
        st.dataframe(df_w, use_container_width=True)

        st.markdown("### 📈 Trend per wedstrijd")
        df_trend = pd.DataFrame(wedstrijd_data).set_index("Datum")[["✅", "❌", "🩹"]]
        st.bar_chart(df_trend)

# ══════════════════════════════════════════════════════════════════════════════
with tab3:
    st.markdown("## 👥 Spelersoverzicht")
    if not data["spelers"]:
        st.info("Nog geen spelers toegevoegd.")
    else:
        # 1 kolom op mobiel, 2 op tablet, 3 op desktop
        cols = st.columns([1, 1])
        for i, speler in enumerate(sorted(data["spelers"], key=lambda x: x["nummer"])):
            naam = speler["naam"]
            aanwezig, afwezig, blessure = speler_stats(naam)
            totaal = len(echte_wedstrijden)
            pct    = round(aanwezig / totaal * 100) if totaal else 0
            with cols[i % 2]:
                st.markdown(f"""
                <div class="speler-card">
                    <div style="font-size:1.4rem">⚽</div>
                    <div style="font-family:'Bebas Neue',sans-serif;font-size:1.1rem;color:#fff">
                        #{speler['nummer']} {naam}
                    </div>
                    <div style="color:#9e9e9e;font-size:0.8rem;margin-bottom:8px">{speler['positie']}</div>
                    <span class="badge badge-groen">✅ {aanwezig}x</span>
                    <span class="badge badge-rood">❌ {afwezig}x</span>
                    <span class="badge badge-oranje">🩹 {blessure}x</span>
                    <hr style="border-color:#333;margin:8px 0">
                    <div style="color:#00c853;font-weight:600">{pct}% aanwezig</div>
                    <div style="color:#9e9e9e;font-size:0.78rem">{aanwezig}/{totaal} wedstrijden</div>
                </div>
                """, unsafe_allow_html=True)
