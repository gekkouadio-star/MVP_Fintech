# Kiosque Multi-Opérateurs Fintech

Cette application est un tableau de bord de gestion comptable temps réel conçu pour le suivi des transactions des kiosques multiservices (Orange, MTN, Moov, Wave). Elle permet une visualisation précise des flux financiers et facilite l'audit des opérations quotidiennes.

## Fonctionnalités Principales

* **Tableau de bord comptable** : 
    * Visualisation dynamique des volumes par opérateur.
    * Suivi de l'évolution des transactions en temps réel avec identification par opérateur.
* **Journal des transactions** : 
    * Consultation détaillée du "fil de l'eau" (entrées/sorties).
    * Codage couleur automatique pour identifier instantanément les débits (retraits).
* **Export de données** : 
    * Génération et téléchargement automatique de bilans comptables au format PDF.

## Stack Technique

* **Backend** : Python (API Flask)
* **Frontend** : Streamlit
* **Visualisation** : Altair
* **Gestion des données** : Pandas

## Installation & Lancement

1.  **Clonage du projet** :
    ```bash
    git clone [URL_DE_VOTRE_DEPOT]
    cd [NOM_DU_DOSSIER]
    ```

2.  **Installation des dépendances** :
    ```bash
    pip install -r requirements.txt
    ```

3.  **Lancement** :
    L'application lance automatiquement le serveur API local si celui-ci n'est pas détecté.
    ```bash
    streamlit run main_dashboard.py
    ```

## Utilisation

1.  **Dashboard Comptable** : Accédez à la vue principale pour visualiser les graphiques d'évolution des flux. Utilisez le menu latéral pour filtrer les opérateurs.
2.  **Export PDF** : Cliquez sur le bouton "Générer et Télécharger" dans la barre latérale pour obtenir l'état financier mensuel certifié.
3.  **Journal des transactions** : Accédez à la vue "Gestion des SMS" pour consulter la liste exhaustive des transactions avec leurs détails (Débit/Crédit).

## Audit & Conformité

* **Auditeur Principal** : Gérard KOUADIO
* **Version** : MVP v1.0
* *Système de gestion comptable temps réel avec haute intégrité des données.*

---
*Note : Assurez-vous que votre serveur API est actif sur le port 8080 pour permettre la communication avec le tableau de bord.*