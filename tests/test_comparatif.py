import os
import pandas as pd
from src.reporting.pdf_exporter import exporter_etats_financiers_pdf

def simuler_test_comparatif():
    print("⏳ Préparation des données de test (Mois N vs N-1)...")
    
    # 1. Simulation du bilan du mois précédent (Mai 2026 - N-1)
    donnees_mai = {
        "Rubrique": ["Caisse Espèces", "Stock UV Orange", "Stock UV MTN", "Stock UV Moov", "Stock UV Wave", "TOTAL ACTIF", "Capital Social", "Résultat Net", "TOTAL PASSIF"],
        "Type": ["5711", "52121", "52122", "52123", "52124", "TOTAL", "1011", "131", "TOTAL"],
        "Montant Mai (FCFA)": [350000, 420000, 390000, 400000, 410000, 1970000, 2000000, -30000, 1970000]
    }
    df_mai = pd.DataFrame(donnees_mai)
    
    # 2. Simulation du bilan du mois actuel (Juin 2026 - N) -> Avec augmentation !
    donnees_juin = {
        "Rubrique": ["Caisse Espèces", "Stock UV Orange", "Stock UV MTN", "Stock UV Moov", "Stock UV Wave", "TOTAL ACTIF", "Capital Social", "Résultat Net", "TOTAL PASSIF"],
        "Type": ["5711", "52121", "52122", "52123", "52124", "TOTAL", "1011", "131", "TOTAL"],
        "Montant Juin (FCFA)": [450000, 480000, 410000, 400000, 430000, 2170000, 2000000, 170000, 2170000]
    }
    df_juin = pd.DataFrame(donnees_juin)
    
    # 3. Fusion des deux mois (Le fameux merge terrain préparé)
    df_bilan_comparatif = pd.merge(df_mai, df_juin, on=["Rubrique", "Type"])
    
    # 4. Simulation d'un journal global minimal pour le compte de résultat
    donnees_journal = {
        "Date": ["2026-06-11", "2026-06-11"],
        "Ref_Tx": ["TX1001", "TX1002"],
        "Compte": ["706", "706"],
        "Libelle": ["Commission Orange", "Commission MTN"],
        "Debit": [0.0, 0.0],
        "Credit": [120000.0, 50000.0],
        "Gerant": ["Gérard KOUADIO", "Gérard KOUADIO"]
    }
    df_journal_global = pd.DataFrame(donnees_journal)
    
    # Simulation d'un compte de résultat simple
    df_cr_simule = pd.DataFrame() 

    print("📊 Dataframe comparatif prêt pour injection :")
    print(df_bilan_comparatif.to_string(index=False))
    print("-" * 60)
    
    # 5. Appel de l'exportateur PDF (qui va détecter automatiquement les 2 colonnes de montants)
    chemin_rapport = exporter_etats_financiers_pdf(
        df_bilan=df_bilan_comparatif,
        df_cr=df_cr_simule,
        df_journal_global=df_journal_global,
        dossier_sortie="exports/tests",
        titre_periode="Analyse Comparative — Mai vs Juin 2026"
    )
    
    print(f"✨ Test réussi ! Le fichier a été généré dans : {chemin_rapport}")

if __name__ == "__main__":
    # S'assurer que le dossier src est accessible au script
    import sys
    sys.path.append(os.path.abspath(os.path.dirname(__file__)))
    
    simuler_test_comparatif()