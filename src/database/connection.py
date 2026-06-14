import sqlite3
from pathlib import Path

# Définition du chemin de la base de données dans data/
ROOT_DIR = Path(__file__).resolve().parents[2]
DB_PATH = ROOT_DIR / "data" / "mvp_fintech.db"

def get_connection():
    """Retourne une connexion active à la base de données SQLite."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Permet d'accéder aux colonnes par leur nom
    return conn

def initialiser_bdd():
    """Crée les tables si elles n'existent pas et charge la balance initiale."""
    # Assurer que le dossier data existe
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    conn = get_connection()
    cursor = conn.cursor()

    # 1. Table des Comptes (Balance/Soldes) - CORRIGÉ : C'est la table 'comptes' !
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS comptes (
        code_compte TEXT PRIMARY KEY,
        intitule TEXT NOT NULL,
        solde_initial REAL DEFAULT 0.0,
        solde_actuel REAL DEFAULT 0.0
    );
    """)

    # 2. Table du Journal Comptable (Pour persister les écritures) - CORRIGÉ : Avec id_gerant intégré d'office
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS journal (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date_ecriture TEXT NOT NULL,
        ref_tx TEXT NOT NULL,
        compte TEXT NOT NULL,
        libelle TEXT NOT NULL,
        debit REAL NOT NULL,
        credit REAL NOT NULL,
        id_gerant TEXT DEFAULT 'Gérard KOUADIO',
        FOREIGN KEY(compte) REFERENCES comptes(code_compte)
    );
    """)

    # 3. Injection de la balance de départ (si vide)
    cursor.execute("SELECT COUNT(*) FROM comptes")
    if cursor.fetchone()[0] == 0:
        comptes_depart = [
            ("5711", "Caisse Espèces", 400000.0, 400000.0),
            ("52121", "Stock UV Orange", 400000.0, 400000.0),
            ("52122", "Stock UV MTN", 400000.0, 400000.0),
            ("52123", "Stock UV Moov", 400000.0, 400000.0),
            ("52124", "Stock UV Wave", 400000.0, 400000.0), # Total Actif initial = 2M FCFA
            ("1011", "Capital Social", 2000000.0, 2000000.0),
            ("706", "Produits Commissions", 0.0, 0.0)
        ]
        cursor.executemany("""
        INSERT INTO comptes (code_compte, intitule, solde_initial, solde_actuel)
        VALUES (?, ?, ?, ?)
        """, comptes_depart)
        
        conn.commit()
        print("🗄️ Base de données initialisée avec la balance de départ (2 000 000 F CFA).")
    
    conn.close()

if __name__ == "__main__":
    # Petit test d'exécution rapide du fichier
    initialiser_bdd()