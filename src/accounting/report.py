import pandas as pd
from src.database.connection import get_connection

class BilanComptable:
    def __init__(self, df_journal: pd.DataFrame, resultat_net: float):
        self.df_journal = df_journal
        self.resultat_net = resultat_net
        
        # Chargement dynamique depuis SQLite
        self.soldes_initiaux = self.charger_soldes_initiaux()

    def charger_soldes_initiaux(self) -> dict:
        """Récupère la balance de départ stockée en base de données."""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT code_compte, solde_initial FROM comptes")
        rows = cursor.fetchall()
        conn.close()
        return {row["code_compte"]: row["solde_initial"] for row in rows}

    def generer_bilan(self) -> pd.DataFrame:
        # Initialisation complète des 4 opérateurs de Côte d'Ivoire
        solde_mouvements = {"5711": 0.0, "52121": 0.0, "52122": 0.0, "52123": 0.0, "52124": 0.0}

        if not self.df_journal.empty:
            recap = self.df_journal.groupby("Compte").agg({"Debit": "sum", "Credit": "sum"}).reset_index()
            recap["Solde"] = recap["Debit"] - recap["Credit"]
            for _, row in recap.iterrows():
                if row["Compte"] in solde_mouvements:
                    solde_mouvements[row["Compte"]] = row["Solde"]

        # Équations de bilans patrimoniaux dynamiques
        cash_final = self.soldes_initiaux.get("5711", 0.0) + solde_mouvements["5711"]
        orange_final = self.soldes_initiaux.get("52121", 0.0) + solde_mouvements["52121"]
        mtn_final = self.soldes_initiaux.get("52122", 0.0) + solde_mouvements["52122"]
        moov_final = self.soldes_initiaux.get("52123", 0.0) + solde_mouvements["52123"]
        wave_final = self.soldes_initiaux.get("52124", 0.0) + solde_mouvements["52124"]
        
        total_actif = cash_final + orange_final + mtn_final + moov_final + wave_final
        capital_social = self.soldes_initiaux.get("1011", 2000000.0)

        lignes_bilan = [
            {"Rubrique": "ACTIF : Caisse Espèces (5711)", "Montant (FCFA)": cash_final, "Type": "ACTIF"},
            {"Rubrique": "ACTIF : Stock UV Orange (52121)", "Montant (FCFA)": orange_final, "Type": "ACTIF"},
            {"Rubrique": "ACTIF : Stock UV MTN (52122)", "Montant (FCFA)": mtn_final, "Type": "ACTIF"},
            {"Rubrique": "ACTIF : Stock UV Moov (52123)", "Montant (FCFA)": moov_final, "Type": "ACTIF"},
            {"Rubrique": "ACTIF : Stock UV Wave (52124)", "Montant (FCFA)": wave_final, "Type": "ACTIF"},
            {"Rubrique": "TOTAL ACTIF", "Montant (FCFA)": total_actif, "Type": "TOTAL"},
            {"Rubrique": "-----------------------------------------", "Montant (FCFA)": 0.0, "Type": "SEPARATEUR"},
            {"Rubrique": "PASSIF : Capital Social (1011)", "Montant (FCFA)": capital_social, "Type": "PASSIF"},
            {"Rubrique": "PASSIF : Résultat de l'exercice (131)", "Montant (FCFA)": self.resultat_net, "Type": "PASSIF"},
            {"Rubrique": "TOTAL PASSIF", "Montant (FCFA)": capital_social + self.resultat_net, "Type": "TOTAL"}
        ]
        return pd.DataFrame(lignes_bilan)