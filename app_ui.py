import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import altair as alt

# Configuration de la page
st.set_page_config(page_title="Dashboard Fintech", layout="wide")

# Port unique
API_PORT = "8080"
BASE_URL = f"http://127.0.0.1:{API_PORT}"

# --- CSS Personnalisé pour l'entête encadré ---
st.markdown("""
    <style>
    .header-box {
        border: 2px solid #4A90E2;
        padding: 10px;
        border-radius: 10px;
        text-align: center;
        background-color: #f0f7ff;
        color: #4A90E2;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

# Affichage de l'entête
st.markdown('<div class="header-box"><h1>TABLEAU DE BORD COMPTABLE FINTECH</h1></div>', unsafe_allow_html=True)
st.write("") # Espace

# --- Actions Sidebar ---
st.sidebar.header("⚙️ ACTIONS")
if st.sidebar.button("Générer et Télécharger le Rapport"):
    try:
        response = requests.get(f"{BASE_URL}/export/pdf", timeout=10)
        if response.status_code == 200:
            result = response.json()
            filename = result.get("fichier_pdf").split('/')[-1]
            pdf_file = requests.get(f"{BASE_URL}/download/{filename}", timeout=10)
            st.sidebar.success("PDF généré !")
            st.sidebar.download_button("📥 TÉLÉCHARGER LE PDF", pdf_file.content, filename, "application/pdf")
        else:
            st.sidebar.error("Erreur génération API")
    except Exception as e:
        st.sidebar.error(f"Erreur : {e}")

# --- Stats Section ---
with st.container():
    st.subheader("VOLUME DES TRANSACTIONS PAR OPÉRATEUR")
    
    try:
        params = {"t": datetime.now().timestamp()}
        stats_resp = requests.get(f"{BASE_URL}/stats/operateurs", timeout=10, params=params)
        
        if stats_resp.status_code == 200:
            data = stats_resp.json().get("total_par_operateur", {})
            if data:
                df = pd.DataFrame(list(data.items()), columns=["Opérateur", "Montant"])
                
                # --- AJOUT DE LA CORRECTION ICI ---
                # On définit la liste des noms autorisés
                operateurs_autorises = ["ORANGE", "MTN", "MOOV", "WAVE"]
                
                # On filtre le DataFrame pour ne garder que ceux-là
                df = df[df["Opérateur"].isin(operateurs_autorises)]
                # -----------------------------------
                
                # Couleurs personnalisées par opérateur
                couleurs = alt.Scale(domain=['ORANGE', 'MTN', 'MOOV', 'WAVE'],
                                     range=['#FF7900', '#FFCC00', '#007A33', '#00AEEF'])
                
                chart = alt.Chart(df).mark_bar().encode(
                    x=alt.X('Opérateur', sort=None), # sort=None garde ton ordre
                    y='Montant',
                    color=alt.Color('Opérateur', scale=couleurs)
                ).properties(height=400)
                
                st.altair_chart(chart, use_container_width=True)
                
                with st.expander("🔍 Voir les données brutes"):
                    st.dataframe(df, use_container_width=True)
            else:
                st.info("Aucune donnée disponible.")
        else:
            st.warning("Impossible de joindre l'API.")
    except Exception as e:
        st.error(f"❌ Serveur non joignable : {e}")