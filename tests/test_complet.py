import requests
import json
import time

# On utilise le port 8080 car ton serveur FastAPI tourne dessus
BASE_URL = "http://127.0.0.1:8080"

def test_pipeline():
    print("🚀 Démarrage du test multicanal complet...")
    
    payloads = [
        {"sender": "ORANGE", "text": "Depot de 50000 F fait au 0707070707 le 12/06/2026. Trx ID: ORG123456."},
        {"sender": "MTN", "text": "Transfert de 20000 F effectue vers le 0707070707. Ref: MTN999999."},
        {"sender": "MOOV", "text": "Depot reussi de 30000 F au 0707070707. Trx: MOV888888."},
        {"sender": "WAVE", "text": "Vous avez envoye 40000 F a 0707070707 avec Wave. Id: WV7777777"}
    ]

    for p in payloads:
        time.sleep(0.3) 
        try:
            resp = requests.post(f"{BASE_URL}/webhook/sms", json=p)
            if resp.status_code == 200:
                print(f"✅ Injection {p['sender']} réussie")
            else:
                print(f"❌ Erreur {p['sender']} : {resp.text}")
        except requests.exceptions.ConnectionError:
            print("❌ Erreur : Le serveur n'est pas lancé.")
            return
    
    print("\n⏳ Génération du rapport PDF consolidé...")
    resp_pdf = requests.get(f"{BASE_URL}/export/pdf")
    
    if resp_pdf.status_code == 200:
        data = resp_pdf.json()
        print(f"✨ Succès : {data.get('message', 'PDF généré')}")
    else:
        print(f"❌ Erreur PDF : {resp_pdf.text}")

if __name__ == "__main__":
    test_pipeline()