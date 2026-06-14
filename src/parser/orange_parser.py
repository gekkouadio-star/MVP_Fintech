import re
from typing import Optional
from pydantic import BaseModel, Field

class TransactionMobileMoney(BaseModel):
    id_transaction: str
    operateur: str        # ORANGE, MTN, MOOV, WAVE
    type_operation: str   # DEPOT_CLIENT, RETRAIT_CLIENT
    montant: float = Field(..., gt=0)
    compte_comptable: str # 52121, 52122, 52123, 52124
    telephone_client: str
    commission_agent: float
    id_gerant: str = "Gérard KOUADIO"  # <--- Ajoute cette ligne avec ta signature par défaut

def parse_sms_universel(sms_text: str) -> Optional[TransactionMobileMoney]:
    # Grille théorique moyenne de commission gérant (0.5%)
    TAUX_COMMISSION = 0.005
    
    # 1. ORANGE
    if "Trx ID: ORG" in sms_text or "Orange" in sms_text:
        # Sous-cas A : DÉPÔT CLIENT
        if "Depot de" in sms_text:
            # Remplacement de \S+ par [\w-]+ pour isoler proprement l'ID sans déborder sur le point
            match = re.search(r"Depot de (?P<montant>\d+) F fait au (?P<tel>\d+) .* Trx ID: (?P<id>[\w-]+)\.", sms_text)
            if match:
                res = match.groupdict()
                return TransactionMobileMoney(
                    id_transaction=res["id"], operateur="ORANGE", type_operation="DEPOT_CLIENT",
                    montant=float(res["montant"]), compte_comptable="52121", telephone_client=res["tel"],
                    commission_agent=float(res["montant"]) * TAUX_COMMISSION
                )
        # Sous-cas B : RETRAIT CLIENT
        elif "Retrait de" in sms_text:
            # Remplacement de \S+ par [\w-]+ ici aussi
            match = re.search(r"Retrait de (?P<montant>\d+) F fait par le (?P<tel>\d+) .* Trx ID: (?P<id>[\w-]+)\.", sms_text)
            if match:
                res = match.groupdict()
                return TransactionMobileMoney(
                    id_transaction=res["id"], operateur="ORANGE", type_operation="RETRAIT_CLIENT",
                    montant=float(res["montant"]), compte_comptable="52121", telephone_client=res["tel"],
                    commission_agent=float(res["montant"]) * TAUX_COMMISSION
                )
                
    # 2. MTN (Version ultra-souple pour debug)
    if "MTN" in sms_text or "Ref:" in sms_text:
        # On utilise une regex qui ignore les caractères intermédiaires
        match = re.search(r"Transfert de (?P<montant>\d+) F.*Ref: (?P<id>[\w-]+)", sms_text)
        if match:
            res = match.groupdict()
            # On force le téléphone si absent de la regex souple
            tel = "0000000000" 
            return TransactionMobileMoney(
                id_transaction=res["id"], operateur="MTN", type_operation="DEPOT_CLIENT",
                montant=float(res["montant"]), compte_comptable="52122", telephone_client=tel,
                commission_agent=float(res["montant"]) * TAUX_COMMISSION
            )

    # 3. MOOV
    if "Moov" in sms_text or "MOV" in sms_text:
        match = re.search(r"Depot reussi de (?P<montant>\d+) F au (?P<tel>\d+)\. Trx: (?P<id>\w+)\.", sms_text)
        if match:
            res = match.groupdict()
            return TransactionMobileMoney(
                id_transaction=res["id"], operateur="MOOV", type_operation="DEPOT_CLIENT",
                montant=float(res["montant"]), compte_comptable="52123", telephone_client=res["tel"],
                commission_agent=float(res["montant"]) * TAUX_COMMISSION
            )

    # 4. WAVE
    if "Wave" in sms_text or "WV" in sms_text:
        match = re.search(r"Vous avez envoye (?P<montant>\d+) F a (?P<tel>\d+) avec Wave\. Id: (?P<id>\S+)", sms_text)
        if match:
            res = match.groupdict()
            return TransactionMobileMoney(
                id_transaction=res["id"], operateur="WAVE", type_operation="DEPOT_CLIENT",
                montant=float(res["montant"]), compte_comptable="52124", telephone_client=res["tel"],
                commission_agent=float(res["montant"]) * TAUX_COMMISSION
            )

    return None