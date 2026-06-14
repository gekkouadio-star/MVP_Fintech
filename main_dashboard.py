import streamlit as st
import subprocess
import requests
import pandas as pd
import altair as alt
import time
from datetime import datetime

# --- CONFIGURATION ---
st.set_page_config(page_title="Fintech Manager", layout="wide")
API_PORT = "8080"
BASE_URL = f"http://127.0.0.1:{API_PORT}"

# --- GESTION DU SERVEUR ---
def start_api():
    try:
        requests.get(f"{BASE_URL}/stats/operateurs", timeout=1)
    except:
        subprocess.Popen(["python", "main.py"])
        time.sleep(3)

start_api()

# --- CSS POUR LE LOOK PRO ---
st.markdown("""
    <style>
    .header-box { border: 2px solid #4A90E2; padding: 15px; border-radius: 10px; text-align: center; background-color: #f0f7ff; color: #4A90E2; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# --- NAVIGATION ---
st.sidebar.title("NAVIGATION")
page = st.sidebar.radio("Choisir une vue", ["Dashboard Comptable", "Gestion des SMS"])

# --- VUE DASHBOARD COMPTABLE ---
if page == "Dashboard Comptable":
    st.markdown('<div class="header-box"><h1>TABLEAU DE BORD COMPTABLE</h1></div>', unsafe_allow_html=True)
    
    with st.sidebar:
        st.header("RAPPORTS COMPTABLES")
        if st.button("📥 Générer et Télécharger le Bilan Comptable"):
            try:
                resp = requests.get(f"{BASE_URL}/export/pdf")
                if resp.status_code == 200:
                    filename = resp.json().get("fichier_pdf").split('/')[-1]
                    pdf_file = requests.get(f"{BASE_URL}/download/{filename}")
                    st.download_button("CLIQUEZ POUR TÉLÉCHARGER", pdf_file.content, filename, "application/pdf")
            except: st.error("Erreur génération PDF")

    st.subheader("VOLUME PAR OPÉRATEUR")
    try:
        data = requests.get(f"{BASE_URL}/stats/operateurs", params={"t": datetime.now().timestamp()}).json().get("total_par_operateur", {})
        df = pd.DataFrame(list(data.items()), columns=["Opérateur", "Montant"])
        df = df[df["Opérateur"].isin(["ORANGE", "MTN", "MOOV", "WAVE"])]
        
        chart = alt.Chart(df).mark_bar().encode(
            x='Opérateur', y='Montant',
            color=alt.Color('Opérateur', scale=alt.Scale(domain=['ORANGE', 'MTN', 'MOOV', 'WAVE'], range=['#FF7900', '#FFCC00', '#007A33', '#00AEEF']))
        )
        st.altair_chart(chart, use_container_width=True)

        # --- GRAPHIQUE AVEC COULEURS PROPRES À CHAQUE OPÉRATEUR ---
        st.subheader("📊 ÉVOLUTION DES FLUX PAR OPÉRATEUR")
        resp_hist = requests.get(f"{BASE_URL}/journal")
        if resp_hist.status_code == 200:
            df_hist = pd.DataFrame(resp_hist.json().get("lignes", []))
            if not df_hist.empty:
                df_hist['Date'] = pd.to_datetime(df_hist['Date'])
                df_hist['Debit'] = pd.to_numeric(df_hist['Debit'], errors='coerce').fillna(0)
                df_hist['Credit'] = pd.to_numeric(df_hist['Credit'], errors='coerce').fillna(0)
                
                # Détection de l'opérateur
                def detecter_operateur(libelle):
                    lib = str(libelle).upper()
                    if "ORANGE" in lib: return "ORANGE"
                    if "MTN" in lib: return "MTN"
                    if "MOOV" in lib: return "MOOV"
                    if "WAVE" in lib: return "WAVE"
                    return "AUTRE"
                
                df_hist['Operateur'] = df_hist['Libelle'].apply(detecter_operateur)
                
                # Couleurs personnalisées (Orange, Jaune, Vert, Bleu)
                couleurs_ope = alt.Scale(
                    domain=['ORANGE', 'MTN', 'MOOV', 'WAVE'],
                    range=['#FF7900', '#FFCC00', '#007A33', '#00AEEF']
                )

                # ===============================
                # Evolution des transactions
                # ===============================

                # Agrégation par jour et opérateur
                df_evolution = (
                    df_hist
                    .groupby(
                        [pd.Grouper(key="Date", freq="D"), "Operateur"],
                        as_index=False
                    )["Credit"]
                    .sum()
                )

                chart = (
                    alt.Chart(df_evolution)
                    .mark_line(point=True, strokeWidth=3)
                    .encode(
                        x=alt.X(
                            "Date:T",
                            title="Date"
                        ),
                        y=alt.Y(
                            "Credit:Q",
                            title="Volume des transactions (FCFA)"
                        ),
                        color=alt.Color(
                            "Operateur:N",
                            scale=couleurs_ope,
                            legend=alt.Legend(title="Opérateur")
                        ),
                        tooltip=[
                            alt.Tooltip("Date:T", title="Date"),
                            alt.Tooltip("Operateur:N", title="Opérateur"),
                            alt.Tooltip("Credit:Q", title="Montant", format=",.0f")
                        ]
                    )
                    .properties(height=400)
                    .interactive()
                )

                st.altair_chart(chart, use_container_width=True)
                
    except: st.warning("Serveur en cours de démarrage...")

elif page == "Gestion des SMS":
    st.header("📲 JOURNAL DES TRANSACTIONS (ENTRÉES/SORTIES)")
    
    # Bouton d'actualisation
    if st.button("Actualiser le journal"):
        st.rerun()
        
    try:
        # Requête pour obtenir le journal complet depuis l'API
        resp = requests.get(f"{BASE_URL}/journal", timeout=10)
        
        if resp.status_code == 200:
            journal_data = resp.json().get("lignes", [])
            df_journal = pd.DataFrame(journal_data)
            
            if not df_journal.empty:
                # Normalisation : cherche une colonne qui contient "debit" (insensible à la casse)
                col_debit = next((col for col in df_journal.columns if "debit" in col.lower()), None)
                
                if col_debit:
                    # Conversion propre pour le style
                    df_journal[col_debit] = pd.to_numeric(df_journal[col_debit], errors='coerce').fillna(0)
                    
                    def color_debit(val):
                        # Retourne rouge si c'est un retrait (débit > 0), sinon noir
                        color = 'red' if val > 0 else 'black'
                        return f'color: {color}'
                    
                    st.dataframe(
                        df_journal.style.map(color_debit, subset=[col_debit]),
                        use_container_width=True
                    )
                else:
                    # Si aucune colonne "debit" n'est trouvée, on affiche le tableau brut
                    st.warning("Colonne de débit introuvable, affichage des données brutes :")
                    st.dataframe(df_journal, use_container_width=True)
            else:
                st.info("Le journal est vide pour le moment.")
        else:
            st.warning("Impossible de charger le journal.")
    except Exception as e:
        st.error(f"Erreur de connexion : {e}")
# --- PIED DE PAGE CENTRAL ---
st.markdown("---")
st.markdown(
    """
    <div style="text-align: center; color: #b0b0b0; font-size: 10px; margin-top: 20px;">
        MVP Fintech v1.0 | Système de gestion comptable temps réel | Confidentialité assurée
    </div>
    """, 
    unsafe_allow_html=True
)        
# --- FOOTER PROFESSIONNEL (VERT CLAIR) ---
st.sidebar.markdown("---")
st.sidebar.markdown(
    """
    <div style="
        border: 1px solid #c8e6c9; 
        padding: 15px; 
        border-radius: 10px; 
        text-align: center; 
        background-color: #f1f8f0;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.03);
    ">
        <p style="margin: 0; font-size: 11px; color: #2e7d32; text-transform: uppercase; letter-spacing: 1.5px; font-weight: bold;">
            Audit certifié
        </p>
        <p style="margin: 8px 0 0 0; font-size: 14px; color: #333;">
            <b>Gérard KOUADIO</b><br>
            <span style="font-size: 12px; color: #555;">Auditeur Principal</span>
        </p>
    </div>
    """, 
    unsafe_allow_html=True
)