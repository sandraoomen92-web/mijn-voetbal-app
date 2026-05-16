import streamlit as st
import pandas as pd
import requests
import json
import base64

# --- GITHUB CONFIGURATIE VIA SECRETS ---
GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
REPO = st.secrets["GITHUB_REPO"]  # sandraoomen92-web/mijn-voetbal-app
FILE_PATH = "voetbal_data.json"
URL = f"https://api.github.com/repos/{REPO}/contents/{FILE_PATH}"
HEADERS = {"Authorization": f"token {GITHUB_TOKEN}"}

# --- FUNCTIES VOOR DATA-BEHEER VIA GITHUB ---
def laad_data_van_github():
    response = requests.get(URL, headers=HEADERS)
    if response.status_code == 200:
        # Bestand bestaat, database inlezen
        content = response.json()
        file_content = base64.b64decode(content["content"]).decode("utf-8")
        return json.loads(file_content), content["sha"]
    elif response.status_code == 404:
        # Bestand bestaat nog niet, maak een lege basisstructuur
        basis_data = {"spelers": [], "trainingen": [], "opstellingen": []}
        return basis_data, None
    else:
        st.error(f"Fout bij laden van GitHub: {response.status_code}")
        return {"spelers": [], "trainingen": [], "opstellingen": []}, None

def sla_data_op_naar_github(data, sha):
    data_string = json.dumps(data, indent=4)
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

# --- DATA INLADEN ---
data, file_sha = laad_data_van_github()

# Maak dataframes van de JSON data voor gebruik in de app
df_spelers = pd.DataFrame(data.get("spelers", []))
df_trainingen = pd.DataFrame(data.get("trainingen", []))
df_opstellingen = pd.DataFrame(data.get("opstellingen", []))

# --- STREAMLIT INTERFACE ---
st.title("⚽ Mijn Voetbal App")

tab1, tab2, tab3 = st.tabs(["📋 Spelersbeheer", "⏱️ Trainingen", "🧠 Opstelling"])

with tab1:
    st.header("Spelerslijst")
    if not df_spelers.empty:
        st.dataframe(df_spelers, use_container_width=True)
    else:
        st.info("Er zijn nog geen spelers toegevoegd.")
        
    st.subheader("Nieuwe speler toevoegen")
    nieuwe_speler = st.text_input("Naam van de speler:")
    if st.button("Speler Opslaan"):
        if nieuwe_speler:
            data["spelers"].append({"Naam": nieuwe_speler, "Aanwezig": True})
            sla_data_op_naar_github(data, file_sha)
        else:
            st.warning("Vul eerst een naam in.")

with tab2:
    st.header("Trainingen")
    st.info("Hier kun je later trainingen beheren.")

with tab3:
    st.header("Opstelling")
    st.info("Hier kun je later de opstellingen beheren.")
