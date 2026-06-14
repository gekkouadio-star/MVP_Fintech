from datetime import datetime
import pandas as pd
from src.parser.orange_parser import TransactionMobileMoney
from src.database.connection import get_connection

class JournalComptable:
    def __init__(self):
        self.ecritures = []

    def generer_ecriture(self, tx: TransactionMobileMoney):
        """Génère automatiquement les lignes réglementaires en partie double."""
        date_actuelle = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        # Récupération de l'identifiant du gérant depuis l'objet transaction
        # Si le champ n'existe pas encore sur une ancienne version de l'objet, sécurité par défaut.
        nom_gerant = getattr(tx, "id_gerant", "Gérard KOUADIO")
        
        if tx.type_operation == "DEPOT_CLIENT":
            self.ecritures.append({"Date": date_actuelle, "Ref_Tx": tx.id_transaction, "Compte": "5711", "Libelle": f"Cash Recu - Dépôt {tx.operateur}", "Debit": tx.montant, "Credit": 0.0, "Gerant": nom_gerant})
            self.ecritures.append({"Date": date_actuelle, "Ref_Tx": tx.id_transaction, "Compte": tx.compte_comptable, "Libelle": f"Sortie UV - Dépôt {tx.operateur}", "Debit": 0.0, "Credit": tx.montant, "Gerant": nom_gerant})
            self.ecritures.append({"Date": date_actuelle, "Ref_Tx": tx.id_transaction, "Compte": tx.compte_comptable, "Libelle": f"Commission - {tx.operateur}", "Debit": tx.commission_agent, "Credit": 0.0, "Gerant": nom_gerant})
            self.ecritures.append({"Date": date_actuelle, "Ref_Tx": tx.id_transaction, "Compte": "706", "Libelle": f"Produits Com - {tx.operateur}", "Debit": 0.0, "Credit": tx.commission_agent, "Gerant": nom_gerant})

        elif tx.type_operation == "RETRAIT_CLIENT":
            # INVERSION : L'agent reçoit des UV sur son compte d'opérateur (Débit)
            self.ecritures.append({"Date": date_actuelle, "Ref_Tx": tx.id_transaction, "Compte": tx.compte_comptable, "Libelle": f"Entrée UV - Retrait {tx.operateur}", "Debit": tx.montant, "Credit": 0.0, "Gerant": nom_gerant})
            # INVERSION : L'agent décaisse du cash physique de sa caisse (Crédit)
            self.ecritures.append({"Date": date_actuelle, "Ref_Tx": tx.id_transaction, "Compte": "5711", "Libelle": f"Cash Donné - Retrait {tx.operateur}", "Debit": 0.0, "Credit": tx.montant, "Gerant": nom_gerant})
            
            # La commission reste un produit acquis (UV en + au Débit, CA au Crédit)
            self.ecritures.append({"Date": date_actuelle, "Ref_Tx": tx.id_transaction, "Compte": tx.compte_comptable, "Libelle": f"Commission Retrait - {tx.operateur}", "Debit": tx.commission_agent, "Credit": 0.0, "Gerant": nom_gerant})
            self.ecritures.append({"Date": date_actuelle, "Ref_Tx": tx.id_transaction, "Compte": "706", "Libelle": f"Produits Com Retrait - {tx.operateur}", "Debit": 0.0, "Credit": tx.commission_agent, "Gerant": nom_gerant})
            
    def sauvegarder_en_bdd(self):
        """Persiste les données en base SQLite."""
        if not self.ecritures:
            return
        conn = get_connection()
        cursor = conn.cursor()
        try:
            # Correction ici : 'in' à la place de 'on'
            for ec in self.ecritures:
                cursor.execute("""
                INSERT INTO journal (date_ecriture, ref_tx, compte, libelle, debit, credit, id_gerant)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (ec["Date"], ec["Ref_Tx"], ec["Compte"], ec["Libelle"], ec["Debit"], ec["Credit"], ec["Gerant"]))
            conn.commit()
            print(f"💾 {len(self.ecritures)} lignes comptables sécurisées en base de données.")
            self.ecritures = [] # Purge de la mémoire vive
        except Exception as e:
            conn.rollback()
            print(f"❌ Crash de sauvegarde journal : {e}")
        finally:
            conn.close()

    def obtenir_journal_df(self) -> pd.DataFrame:
        return pd.DataFrame(self.ecritures)