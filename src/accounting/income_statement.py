import pandas as pd

class CompteDeResultat:
    def __init__(self, df_journal: pd.DataFrame):
        self.df_journal = df_journal

    def generer_sig(self) -> pd.DataFrame:
        """
        Génère les Soldes Intermédiaires de Gestion (SIG) et le Résultat Net.
        """
        if self.df_journal.empty:
            return pd.DataFrame()

        # Groupement par compte
        recap = self.df_journal.groupby("Compte").agg({"Debit": "sum", "Credit": "sum"}).reset_index()
        soldes = dict(zip(recap["Compte"], recap["Debit"] - recap["Credit"]))

        # 1. Produits (Commissions encaissées - Compte 706)
        # En comptabilité, les produits ont un solde créditeur (négatif ici), on prend l'inverse
        produits_commissions = abs(soldes.get("706", 0.0))

        # 2. Charges (Frais de réseau, SMS, écarts de caisse - Compte 60 / 61 / 62)
        # Les charges ont un solde débiteur (positif)
        charges_techniques = soldes.get("628", 0.0)  # Exemple: Frais de télécom/services

        # 3. Calcul du Résultat Net
        resultat_net = produits_commissions - charges_techniques

        lignes_resultat = [
            {"Poste": "PRODUITS : Commissions perçues (706)", "Montant (FCFA)": produits_commissions, "Categorie": "PRODUIT"},
            {"Poste": "CHARGES : Frais techniques & Réseau (628)", "Montant (FCFA)": charges_techniques, "Categorie": "CHARGE"},
            {"Poste": "-----------------------------------------", "Montant (FCFA)": 0.0, "Categorie": "SEPARATEUR"},
            {"Poste": "RÉSULTAT NET DE L'EXERCICE (Bénéfice)", "Montant (FCFA)": resultat_net, "Categorie": "RESULTAT"}
        ]

        return pd.DataFrame(lignes_resultat)