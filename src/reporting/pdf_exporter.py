import os
from datetime import datetime
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

def ajouter_journal_detaille(story, df_journal_global):
    """Génère le détail des 20 dernières transactions par opérateur."""
    styles = getSampleStyleSheet()
    story.append(Spacer(1, 15))
    story.append(Paragraph("3. JOURNAL DÉTAILLÉ DES TRANSACTIONS (FIL DE L'EAU)", 
                           ParagraphStyle('H3', parent=styles['Heading2'], fontSize=12, textColor=colors.HexColor('#2C5282'))))
    
    operateurs = {"52121": "ORANGE", "52122": "MTN", "52123": "MOOV", "52124": "WAVE"}
    
    for code, nom in operateurs.items():
        df_op = df_journal_global[df_journal_global["Compte"] == code].tail(20)
        if df_op.empty: continue
            
        story.append(Paragraph(f"<b>Opérateur : {nom}</b>", 
                               ParagraphStyle('Sub', parent=styles['Normal'], fontSize=10, spaceBefore=10)))
        
        data = [["Date", "Libellé", "Débit", "Crédit", "Réf"]]
        for _, row in df_op.iterrows():
            data.append([str(row["Date"]), row["Libelle"], f"{row['Debit']:,.0f}", f"{row['Credit']:,.0f}", str(row["Ref_Tx"])])
            
        t = Table(data, colWidths=[70, 180, 70, 70, 80])
        t.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#EDF2F7')),
            ('ALIGN', (2, 0), (3, -1), 'RIGHT')
        ]))
        story.append(t)
        story.append(Spacer(1, 10))

def exporter_etats_financiers_pdf(df_bilan: pd.DataFrame, df_cr: pd.DataFrame, df_journal_global: pd.DataFrame, dossier_sortie="exports", titre_periode=None):
    """
    Génère un PDF contenant le Bilan global (classique ou comparatif N vs N-1) et le Compte de Résultat,
    avec mise en gras des totaux. S'adapte dynamiquement au nombre de colonnes fournies.
    """
    if not os.path.exists(dossier_sortie):
        os.makedirs(dossier_sortie)
        
    # Dynamisation du nom de fichier et de la période
    periode_label = titre_periode if titre_periode else f"Mensuelle — {datetime.now().strftime('%m/%Y')}"
    horodatage = datetime.now().strftime("%B_%Y") if not titre_periode else titre_periode.replace(" ", "_")
    nom_fichier = f"{dossier_sortie}/Etats_Financiers_{horodatage}.pdf"
    
    doc = SimpleDocTemplate(nom_fichier, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    story = []
    
    # Styles de mise en page
    styles = getSampleStyleSheet()
    style_titre = ParagraphStyle(
        'TitreFintech', parent=styles['Heading1'], fontSize=22, leading=26, textColor=colors.HexColor('#1A365D'), spaceAfter=15
    )
    style_sous_titre = ParagraphStyle(
        'SousTitreFintech', parent=styles['Normal'], fontSize=10, textColor=colors.HexColor('#4A5568'), spaceAfter=20
    )
    style_h2 = ParagraphStyle(
        'H2Fintech', parent=styles['Heading2'], fontSize=14, leading=18, textColor=colors.HexColor('#2C5282'), spaceBefore=15, spaceAfter=10
    )
    style_badge_gerant = ParagraphStyle(
        'BadgeGerant', parent=styles['Normal'], fontSize=11, fontName="Helvetica-Bold", textColor=colors.HexColor('#2B6CB0'), spaceBefore=8, spaceAfter=5
    )
    
    # 1. En-tête
    story.append(Paragraph("<b>KIOSQUE MULTI-OPÉRATEURS FINTECH</b>", style_titre))
    story.append(Paragraph(f"États Financiers Réglementaires — Clôture {periode_label}<br/>"
                           f"Auditeur Principal : <b>Gérard KOUADIO</b>", style_sous_titre))
    story.append(Spacer(1, 10))
    
    # 2. Section BILAN COMPTABLE (Adaptation dynamique)
    story.append(Paragraph("1. BILAN COMPTABLE CONSOLIDÉ (ACTIF / PASSIF)", style_h2))
    
    colonnes_montants = [col for col in df_bilan.columns if "MONTANT" in col.upper()]
    headers = ["Rubrique", "Type / Compte"] + colonnes_montants
    data_bilan = [headers]
    
    style_commandes_bilan = [
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1A365D')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
    ]
    
    for col_idx in range(2, len(headers)):
        style_commandes_bilan.append(('ALIGN', (col_idx, 0), (col_idx, -1), 'RIGHT'))
    
    idx_ligne = 1
    for _, row in df_bilan.iterrows():
        if row["Type"] != "SEPARATEUR":
            ligne_data = [row["Rubrique"], row["Type"]]
            
            for col in colonnes_montants:
                valeur = row[col]
                if pd.notnull(valeur):
                    ligne_data.append(f"{valeur:,.0f} F".replace(",", " "))
                else:
                    ligne_data.append("0 F")
            
            if "TOTAL" in str(row["Rubrique"]).upper() or row["Type"] == "TOTAL":
                ligne_data[0] = f"====> {ligne_data[0]}"
                data_bilan.append(ligne_data)
                style_commandes_bilan.append(('FONTNAME', (0, idx_ligne), (-1, idx_ligne), 'Helvetica-Bold'))
                style_commandes_bilan.append(('BACKGROUND', (0, idx_ligne), (-1, idx_ligne), colors.HexColor('#EDF2F7')))
            else:
                data_bilan.append(ligne_data)
                if idx_ligne % 2 == 0:
                    style_commandes_bilan.append(('BACKGROUND', (0, idx_ligne), (-1, idx_ligne), colors.HexColor('#F7FAFC')))
                    
            idx_ligne += 1
            
    largeur_rubrique = 240 if len(colonnes_montants) == 1 else 200
    largeur_montant = 130 if len(colonnes_montants) == 1 else 100
    col_widths = [largeur_rubrique, 130] + [largeur_montant] * len(colonnes_montants)
    
    table_bilan = Table(data_bilan, colWidths=col_widths)
    table_bilan.setStyle(TableStyle(style_commandes_bilan))
    story.append(table_bilan)
    story.append(Spacer(1, 20))
    
    # 3. Section COMPTE DE RÉSULTAT PAR GÉRANT
    story.append(Paragraph("2. PERFORMANCES ET COMPTES DE RÉSULTAT PAR GÉRANT", style_h2))
    
    liste_gerants = ["Gérard KOUADIO"]
    if "Gerant" in df_journal_global.columns:
        liste_gerants = df_journal_global["Gerant"].dropna().unique().tolist()
    
    for gerant in liste_gerants:
        story.append(Paragraph(f"👤 Portefeuille Performance : {str(gerant).upper()}", style_badge_gerant))
        
        df_filtre_gerant = df_journal_global[df_journal_global["Gerant"] == gerant]
        total_commissions_gerant = df_filtre_gerant[df_filtre_gerant["Compte"] == "706"]["Credit"].sum()
        
        data_cr_gerant = [
            ["Poste Comptable", "Code", "Montant (FCFA)"],
            [f"Commissions perçues par {gerant}", "706", f"{total_commissions_gerant:,.0f} F".replace(",", " ")],
            ["Frais techniques & Réseau", "628", "0 F"],
            [f"RÉSULTAT NET ATTRIBUABLE", "131", f"{total_commissions_gerant:,.0f} F".replace(",", " ")]
        ]
        
        table_cr = Table(data_cr_gerant, colWidths=[240, 130, 130])
        table_cr.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2C5282')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E0')),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            
            ('FONTNAME', (0, 3), (-1, 3), 'Helvetica-Bold'), 
            ('BACKGROUND', (0, 3), (-1, 3), colors.HexColor('#C6F6D5')), 
            ('TEXTCOLOR', (0, 3), (-1, 3), colors.HexColor('#22543D'))     
        ]))
        story.append(table_cr)
        story.append(Spacer(1, 15))
        
    # Appel de la section ajoutée
    ajouter_journal_detaille(story, df_journal_global)
        
    doc.build(story)
    print(f"📄 Rapport PDF prêt pour l'analyse comparative généré : {nom_fichier}")
    return nom_fichier

    # Exemple de logique à ajouter dans ton exporter_etats_financiers_pdf
    pdf.set_y(-30) # Positionne en bas de page
    pdf.set_font("Arial", 'I', 8)
    pdf.cell(0, 10, "Signé par : Gérard KOUADIO - Auditeur Principal", align='C')