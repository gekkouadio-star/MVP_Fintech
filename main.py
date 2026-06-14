from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import pandas as pd
import os
import sqlite3
from datetime import datetime
from functools import lru_cache
from src.database.connection import initialiser_bdd, get_connection
from src.parser.orange_parser import parse_sms_universel
from src.accounting.journal import JournalComptable
from src.accounting.income_statement import CompteDeResultat
from src.accounting.report import BilanComptable
from fastapi.responses import FileResponse
from src.reporting.pdf_exporter import exporter_etats_financiers_pdf

# 1. Initialisation de l'application FastAPI et de la BDD locale
app = FastAPI(title="MVP Fintech - Moteur Comptable Temps Réel")
initialiser_bdd()

class SMSPayload(BaseModel):
    sender: str
    text: str

def charger_historique_journal_db() -> pd.DataFrame:
    conn = get_connection()
    try:
        # --- VÉRIFICATION DE LA BASE ---
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print(f"DEBUG: Tables trouvées dans la BDD : {tables}")
        
        # Vérifions s'il y a des lignes dans la table 'journal'
        count = cursor.execute("SELECT COUNT(*) FROM journal").fetchone()[0]
        print(f"DEBUG: Nombre de lignes dans la table 'journal' : {count}")
        # -------------------------------

        query = "SELECT date_ecriture as Date, ref_tx as Ref_Tx, compte as Compte, libelle as Libelle, debit as Debit, credit as Credit, id_gerant as Gerant FROM journal"
        df = pd.read_sql_query(query, conn)
        return df
    except Exception as e:
        print(f"❌ Erreur lors du chargement SQL : {e}")
        return pd.DataFrame(columns=["Date", "Ref_Tx", "Compte", "Libelle", "Debit", "Credit", "Gerant"])
    finally:
        conn.close()

def executer_pipeline_comptable(sms_texte: str):
    """
    Orchestre le traitement automatique du SMS jusqu'à l'édition
    des états financiers consolidés (Actif / Passif / Résultat).
    """
    journal = JournalComptable()
    
    # 1. Parsing automatique multi-opérateurs
    tx = parse_sms_universel(sms_texte)
    if not tx:
        print(f"⚠️ SMS ignoré ou non reconnu : '{sms_texte}'")
        return None

    # 2. Génération automatique de l'écriture de la transaction courante
    journal.generer_ecriture(tx)
    
    # 3. Sauvegarde physique immédiate dans le fichier SQLite (purge la mémoire de l'instance)
    journal.sauvegarder_en_bdd()
    
    # 4. Chargement de l'HISTORIQUE GLOBAL COMPLET depuis SQLite pour les calculs de synthèse
    df_journal_global = charger_historique_journal_db()
    
    # 5. ÉDITION DU COMPTE DE RÉSULTAT CONSOLIDÉ
    moteur_cr = CompteDeResultat(df_journal_global)
    df_cr = moteur_cr.generer_sig()
    
    print("\n==================================================")
    print("      🔄 COMPTE DE RÉSULTAT HISTORIQUE MIS À JOUR   ")
    print("==================================================")
    for _, row in df_cr.iterrows():
        if row["Categorie"] != "SEPARATEUR":
            print(f"{row['Poste']:<40} : {row['Montant (FCFA)']:>7,.0f} F")
            
    res_net = df_cr[df_cr["Categorie"] == "RESULTAT"]["Montant (FCFA)"].values[0]

    # 6. ÉDITION DU BILAN PATRIMONIAL GLOBAL (ACTIF / PASSIF)
    moteur_bilan = BilanComptable(df_journal_global, resultat_net=res_net)
    df_bilan = moteur_bilan.generer_bilan()
    
    print("\n==================================================")
    print("     🔄 BILAN COMPTABLE CONSOLIDÉ (ACTIF/PASSIF)  ")
    print("==================================================")
    for _, row in df_bilan.iterrows():
        if row["Type"] == "SEPARATEUR":
            print("-" * 50)
        elif row["Type"] == "TOTAL":
            print(f"==> {row['Rubrique']:<36} : {row['Montant (FCFA)']:>7,.0f} F")
        else:
            print(f"{row['Rubrique']:<40} : {row['Montant (FCFA)']:>7,.0f} F")
    print("==================================================\n")
    
    return tx

@app.post("/webhook/sms")
async def recevoir_sms_relais(payload: SMSPayload):
    transaction = executer_pipeline_comptable(payload.text)
    
    if not transaction:
        raise HTTPException(
            status_code=400, 
            detail="Échec du traitement : syntaxe SMS non reconnue."
        )
        
    return {
        "status": "success",
        "message": f"Inscription automatique validée à l'Actif/Passif ({transaction.operateur})",
        "id_transaction": transaction.id_transaction,
        "montant": transaction.montant,
        "commission": transaction.commission_agent
    }

@app.get("/export/pdf")
async def clore_le_mois_et_exporter_pdf():
    """
    Déclenche la clôture comptable et génère le fichier PDF officiel.
    """
    # 0. SÉCURITÉ : Vérification/Création du dossier d'export
    if not os.path.exists("exports"):
        os.makedirs("exports")
        print("📁 Dossier 'exports/' créé.")
    
    # 1. Récupération de tout l'historique depuis SQLite
    df_journal_global = charger_historique_journal_db()
    
    if df_journal_global.empty:
        raise HTTPException(
            status_code=400, 
            detail="Le journal comptable est vide. Impossible de compiler les états financiers."
        )
    
    # 2. Génération intermédiaire des DataFrames de synthèse
    moteur_cr = CompteDeResultat(df_journal_global)
    df_cr = moteur_cr.generer_sig()
    
    res_net = df_cr[df_cr["Categorie"] == "RESULTAT"]["Montant (FCFA)"].values[0]
    
    moteur_bilan = BilanComptable(df_journal_global, resultat_net=res_net)
    df_bilan = moteur_bilan.generer_bilan()
    
    # 3. Compilation et enregistrement du PDF officiel avec le journal historique complet passé en paramètre
    chemin_pdf = exporter_etats_financiers_pdf(
        df_bilan, df_cr, df_journal_global,
        titre_periode=f"Mensuelle_{datetime.now().strftime('%m_%Y')}"
    )
    
    return {
        "status": "success",
        "message": "Clôture comptable mensuelle effectuée avec succès.",
        "fichier_pdf": chemin_pdf,
        "date_generation": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

@app.get("/export/pdf/annuel")
async def clore_annee_et_exporter_pdf(annee: str = None):
    """
    Déclenche la clôture annuelle comptable pour une année spécifique (ex: 2026).
    Filtre l'historique global pour ne conserver que les entrées de l'année ciblée.
    """
    # Détermination de l'année cible (par défaut l'année civile en cours)
    annee_cible = annee if annee else datetime.now().strftime("%Y")
    
    # 1. Récupération de tout l'historique depuis SQLite
    df_journal_global = charger_historique_journal_db()
    
    if df_journal_global.empty:
        raise HTTPException(
            status_code=400, 
            detail="Le journal comptable est vide. Impossible de compiler le bilan annuel."
        )
    
    # 2. Isolation des écritures appartenant à l'année cible
    df_journal_annuel = df_journal_global[df_journal_global["Date"].astype(str).str.startswith(annee_cible)]
    
    if df_journal_annuel.empty:
        raise HTTPException(
            status_code=404, 
            detail=f"Aucune donnée ou écriture comptable trouvée pour l'année {annee_cible}."
        )
    
    # 3. Traitement comptable des écritures de l'année
    moteur_cr = CompteDeResultat(df_journal_annuel)
    df_cr_annuel = moteur_cr.generer_sig()
    
    res_net_annuel = df_cr_annuel[df_cr_annuel["Categorie"] == "RESULTAT"]["Montant (FCFA)"].values[0]
    
    moteur_bilan = BilanComptable(df_journal_annuel, resultat_net=res_net_annuel)
    df_bilan_annuel = moteur_bilan.generer_bilan()
    
    # 4. Compilation et sauvegarde du rapport annuel consolidé
    dossier_annuel = "exports/annuels"
    chemin_pdf = exporter_etats_financiers_pdf(
        df_bilan_annuel, 
        df_cr_annuel, 
        df_journal_annuel, 
        dossier_sortie=dossier_annuel,
        titre_periode=f"Annuelle — {annee_cible}"
    )
    
    # Renommage du fichier généré pour refléter la nature de l'exercice annuel
    chemin_final = f"{dossier_annuel}/Bilan_Annuel_Consolide_{annee_cible}.pdf"
    if os.path.exists(chemin_pdf):
        os.rename(chemin_pdf, chemin_final)
        
    return {
        "status": "success",
        "message": f"Clôture comptable ANNUELLE {annee_cible} validée avec succès.",
        "fichier_pdf": chemin_final,
        "date_generation": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

@app.get("/stats/operateurs")
async def stats_operateurs(mois: int = None, annee: int = None):
    print(f"DEBUG: Requête reçue pour {mois}/{annee}")
    
    # On appelle directement la fonction de chargement SQL à chaque fois
    df = charger_historique_journal_db()
    
    if df is None or df.empty:
        print("DEBUG: Aucune donnée trouvée dans la BDD.")
        return {"total_par_operateur": {}}
    
    df_work = df.copy()
    
    try:
        df_work['Date'] = pd.to_datetime(df_work['Date'], errors='coerce')
        if mois:
            df_work = df_work[df_work['Date'].dt.month == mois]
        if annee:
            df_work = df_work[df_work['Date'].dt.year == annee]
            
        df_work['Credit'] = pd.to_numeric(df_work['Credit'], errors='coerce').fillna(0)
        
        # Conversion du compte en string pour assurer le mapping
        df_work['Compte'] = df_work['Compte'].astype(str)
        
        stats = df_work.groupby("Compte")["Credit"].sum().to_dict()
        
        mapping = {"52121": "ORANGE", "52122": "MTN", "52123": "MOOV", "52124": "WAVE"}
        stats_libellees = {mapping.get(k, k): v for k, v in stats.items()}
        
        print(f"DEBUG: Calcul terminé pour {len(df_work)} lignes.")
        return {"total_par_operateur": stats_libellees}
        
    except Exception as e:
        print(f"DEBUG: Erreur critique : {e}")
        return {"error": str(e)}

@app.get("/download/{filename}")
async def download_file(filename: str):
    # Utilise le chemin absolu pour éviter les erreurs de répertoire
    base_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_dir, "exports", filename)
    
    if os.path.exists(file_path):
        return FileResponse(file_path, media_type='application/pdf', filename=filename)
    else:
        return {"error": f"Fichier introuvable à : {file_path}"}

@app.get("/journal")
async def get_journal():
    # CORRECTION : Utilisation de get_connection() et fermeture de la connexion
    conn = get_connection()
    conn.row_factory = sqlite3.Row 
    try:
        cursor = conn.cursor()
        # On sélectionne les colonnes avec des alias explicites pour le Dashboard
        cursor.execute("""
            SELECT 
                date_ecriture as Date, 
                debit as Debit, 
                credit as Credit, 
                libelle as Libelle, 
                compte as Compte 
            FROM journal ORDER BY id DESC LIMIT 50
        """)
        rows = [dict(row) for row in cursor.fetchall()]
        return {"lignes": rows}
    finally:
        conn.close()

if __name__ == "__main__":
    import uvicorn
    # Assure-toi que c'est bien écrit 8080 ici
    uvicorn.run("main:app", host="127.0.0.1", port=8080, reload=False)