# -*- coding: utf-8 -*-
"""
Module de génération de PDF pour Crew Taxation
Identité visuelle inspirée de Pan Européenne Air Service
Support complet UTF-8 avec polices TrueType
"""

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, Image, KeepTogether
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from datetime import datetime
import os


# Couleurs de l'identité visuelle Pan Européenne
COLOR_PRIMARY_NAVY = colors.HexColor('#19164B')
COLOR_NAVY_DARK = colors.HexColor('#050237')
COLOR_ACCENT_GOLD = colors.HexColor('#A8987E')
COLOR_WARM_BEIGE = colors.HexColor('#F5F3F1')
COLOR_TEXT_PRIMARY = colors.HexColor('#515050')
COLOR_TEXT_LIGHT = colors.HexColor('#787878')
COLOR_WHITE = colors.white
COLOR_BORDER = colors.HexColor('#E6E6E6')


def register_fonts():
    """Enregistre les polices TrueType pour le support UTF-8"""
    try:
        # Windows fonts directory
        fonts_dir = r'C:\Windows\Fonts'

        # Enregistrer Arial (présent sur tous les Windows)
        pdfmetrics.registerFont(TTFont('ArialUnicode', os.path.join(fonts_dir, 'arial.ttf')))
        pdfmetrics.registerFont(TTFont('ArialUnicode-Bold', os.path.join(fonts_dir, 'arialbd.ttf')))
        pdfmetrics.registerFont(TTFont('ArialUnicode-Italic', os.path.join(fonts_dir, 'ariali.ttf')))
        pdfmetrics.registerFont(TTFont('ArialUnicode-BoldItalic', os.path.join(fonts_dir, 'arialbi.ttf')))

        return True
    except Exception as e:
        print(f"Avertissement: Impossible de charger les polices TrueType: {e}")
        return False


class PDFGenerator:
    """Générateur de PDF avec l'identité visuelle Pan Européenne et support UTF-8"""

    def __init__(self, filename):
        """
        Initialise le générateur de PDF

        Args:
            filename: Chemin du fichier PDF à créer
        """
        self.filename = filename
        self.doc = SimpleDocTemplate(
            filename,
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2.5*cm,
            bottomMargin=2.5*cm
        )
        self.elements = []

        # Enregistrer les polices UTF-8
        self.has_unicode_fonts = register_fonts()

        # Créer les styles avec les bonnes polices
        self.styles = self._create_styles()
        self.width = A4[0] - 4*cm  # Largeur utilisable

    def _create_styles(self):
        """Crée les styles de paragraphe personnalisés avec support UTF-8"""
        styles = getSampleStyleSheet()

        # Choisir la police selon la disponibilité
        if self.has_unicode_fonts:
            font_normal = 'ArialUnicode'
            font_bold = 'ArialUnicode-Bold'
            font_italic = 'ArialUnicode-Italic'
        else:
            # Fallback vers Helvetica
            font_normal = 'Helvetica'
            font_bold = 'Helvetica-Bold'
            font_italic = 'Helvetica-Oblique'

        # Style pour le titre principal (H1)
        styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=styles['Heading1'],
            fontName=font_bold,
            fontSize=24,
            textColor=COLOR_PRIMARY_NAVY,
            spaceAfter=20,
            alignment=TA_CENTER,
            leading=28
        ))

        # Style pour les sous-titres (H2)
        styles.add(ParagraphStyle(
            name='CustomHeading2',
            parent=styles['Heading2'],
            fontName=font_bold,
            fontSize=16,
            textColor=COLOR_PRIMARY_NAVY,
            spaceAfter=12,
            spaceBefore=20,
            leading=20
        ))

        # Style pour les sous-titres (H3)
        styles.add(ParagraphStyle(
            name='CustomHeading3',
            parent=styles['Heading3'],
            fontName=font_bold,
            fontSize=13,
            textColor=COLOR_PRIMARY_NAVY,
            spaceAfter=8,
            spaceBefore=12,
            leading=16
        ))

        # Style pour le corps de texte
        styles.add(ParagraphStyle(
            name='CustomBody',
            parent=styles['Normal'],
            fontName=font_normal,
            fontSize=10,
            textColor=COLOR_TEXT_PRIMARY,
            spaceAfter=8,
            leading=14,
            alignment=TA_JUSTIFY
        ))

        # Style pour le texte en gras
        styles.add(ParagraphStyle(
            name='CustomBodyBold',
            parent=styles['CustomBody'],
            fontName=font_bold
        ))

        # Style pour les légendes/notes
        styles.add(ParagraphStyle(
            name='CustomCaption',
            parent=styles['Normal'],
            fontName=font_italic,
            fontSize=8,
            textColor=COLOR_TEXT_LIGHT,
            spaceAfter=6,
            leading=10
        ))

        # Style pour l'en-tête de page
        styles.add(ParagraphStyle(
            name='CustomHeader',
            parent=styles['Normal'],
            fontName=font_normal,
            fontSize=9,
            textColor=COLOR_TEXT_LIGHT,
            alignment=TA_RIGHT
        ))

        # Style pour le pied de page
        styles.add(ParagraphStyle(
            name='CustomFooter',
            parent=styles['Normal'],
            fontName=font_normal,
            fontSize=8,
            textColor=COLOR_TEXT_LIGHT,
            alignment=TA_CENTER
        ))

        return styles

    def _get_font_name(self, bold=False):
        """Retourne le nom de la police selon la disponibilité"""
        if self.has_unicode_fonts:
            return 'ArialUnicode-Bold' if bold else 'ArialUnicode'
        else:
            return 'Helvetica-Bold' if bold else 'Helvetica'

    def _add_header(self, canvas, doc):
        """Ajoute l'en-tête à chaque page"""
        canvas.saveState()

        # Ligne dorée en haut
        canvas.setStrokeColor(COLOR_ACCENT_GOLD)
        canvas.setLineWidth(2)
        canvas.line(2*cm, A4[1] - 1.5*cm, A4[0] - 2*cm, A4[1] - 1.5*cm)

        # Titre de l'en-tête
        canvas.setFont(self._get_font_name(), 9)
        canvas.setFillColor(COLOR_TEXT_LIGHT)
        canvas.drawRightString(A4[0] - 2*cm, A4[1] - 2*cm, "Crew Taxation - Rapport d'Indemnités")

        canvas.restoreState()

    def _add_footer(self, canvas, doc):
        """Ajoute le pied de page à chaque page"""
        canvas.saveState()

        # Ligne dorée en bas
        canvas.setStrokeColor(COLOR_ACCENT_GOLD)
        canvas.setLineWidth(2)
        canvas.line(2*cm, 1.5*cm, A4[0] - 2*cm, 1.5*cm)

        # Numéro de page
        canvas.setFont(self._get_font_name(), 8)
        canvas.setFillColor(COLOR_TEXT_LIGHT)
        page_num = canvas.getPageNumber()
        text = f"Page {page_num}"
        canvas.drawCentredString(A4[0] / 2, 1*cm, text)

        # Date de génération
        date_text = f"Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}"
        canvas.drawString(2*cm, 1*cm, date_text)

        canvas.restoreState()

    def add_title_page(self, summary_data):
        """
        Ajoute la page de titre avec introduction et résumé

        Args:
            summary_data: Dictionnaire contenant les données du résumé
        """
        # Espaceur initial
        self.elements.append(Spacer(1, 1*cm))

        # Titre principal
        title = Paragraph("Rapport d'Indemnités<br/>Journal de Vol", self.styles['CustomTitle'])
        self.elements.append(title)
        self.elements.append(Spacer(1, 0.5*cm))

        # Date de génération
        date_text = f"Généré le {datetime.now().strftime('%d %B %Y')}"
        date_para = Paragraph(date_text, self.styles['CustomCaption'])
        self.elements.append(date_para)
        self.elements.append(Spacer(1, 1*cm))

        # Section Introduction
        intro_title = Paragraph("Introduction", self.styles['CustomHeading2'])
        self.elements.append(intro_title)

        intro_text = """
        Ce rapport présente le calcul détaillé des indemnités de déplacement
        pour l'équipage, basé sur l'analyse du journal de vol. Les indemnités
        sont calculées selon les barèmes en vigueur et les zones géographiques
        de destination.
        """
        intro_para = Paragraph(intro_text, self.styles['CustomBody'])
        self.elements.append(intro_para)
        self.elements.append(Spacer(1, 1*cm))

        # Section Résumé
        summary_title = Paragraph("Résumé du Traitement", self.styles['CustomHeading2'])
        self.elements.append(summary_title)
        self.elements.append(Spacer(1, 0.3*cm))

        # Tableau résumé avec bordure dorée
        summary_table_data = [
            ['Indicateur', 'Valeur'],
            ['Nombre de rotations', str(summary_data.get('nb_rotations', 0))],
            ['Nombre de vols', str(summary_data.get('nb_vols', 0))],
            ['Total des indemnités', f"{summary_data.get('total_indemnites', 0):.2f} €"],
            ['Problèmes détectés', str(summary_data.get('nb_problemes', 0))]
        ]

        summary_table = Table(summary_table_data, colWidths=[self.width * 0.6, self.width * 0.4])
        summary_table.setStyle(TableStyle([
            # En-tête
            ('BACKGROUND', (0, 0), (-1, 0), COLOR_PRIMARY_NAVY),
            ('TEXTCOLOR', (0, 0), (-1, 0), COLOR_WHITE),
            ('FONTNAME', (0, 0), (-1, 0), self._get_font_name(True)),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('TOPPADDING', (0, 0), (-1, 0), 12),

            # Corps du tableau
            ('BACKGROUND', (0, 1), (-1, -1), COLOR_WHITE),
            ('TEXTCOLOR', (0, 1), (-1, -1), COLOR_TEXT_PRIMARY),
            ('FONTNAME', (0, 1), (-1, -1), self._get_font_name()),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('PADDING', (0, 1), (-1, -1), 10),
            ('ALIGN', (1, 1), (1, -1), 'RIGHT'),

            # Bordures
            ('GRID', (0, 0), (-1, -1), 1, COLOR_BORDER),
            ('LINEABOVE', (0, 0), (-1, 0), 2, COLOR_ACCENT_GOLD),
            ('LINEBELOW', (0, -1), (-1, -1), 2, COLOR_ACCENT_GOLD),

            # Alternance de couleurs
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [COLOR_WHITE, COLOR_WARM_BEIGE])
        ]))

        self.elements.append(summary_table)
        self.elements.append(Spacer(1, 1*cm))

        # Section Répartition par pays
        if summary_data.get('pays_details'):
            pays_title = Paragraph("Répartition par Pays", self.styles['CustomHeading2'])
            self.elements.append(pays_title)
            self.elements.append(Spacer(1, 0.3*cm))

            pays_table_data = [['Pays', 'Nombre de jours', 'Montant total']]
            for pays in summary_data['pays_details'][:10]:  # Top 10 pays
                pays_table_data.append([
                    str(pays['pays']),
                    str(pays['count']),
                    f"{pays['total']:.2f} €"
                ])

            pays_table = Table(pays_table_data, colWidths=[
                self.width * 0.5,
                self.width * 0.25,
                self.width * 0.25
            ])
            pays_table.setStyle(TableStyle([
                # En-tête
                ('BACKGROUND', (0, 0), (-1, 0), COLOR_PRIMARY_NAVY),
                ('TEXTCOLOR', (0, 0), (-1, 0), COLOR_WHITE),
                ('FONTNAME', (0, 0), (-1, 0), self._get_font_name(True)),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('PADDING', (0, 0), (-1, 0), 10),

                # Corps
                ('BACKGROUND', (0, 1), (-1, -1), COLOR_WHITE),
                ('TEXTCOLOR', (0, 1), (-1, -1), COLOR_TEXT_PRIMARY),
                ('FONTNAME', (0, 1), (-1, -1), self._get_font_name()),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('PADDING', (0, 1), (-1, -1), 8),
                ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),

                # Bordures
                ('GRID', (0, 0), (-1, -1), 0.5, COLOR_BORDER),
                ('LINEABOVE', (0, 0), (-1, 0), 2, COLOR_ACCENT_GOLD),

                # Alternance
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [COLOR_WHITE, COLOR_WARM_BEIGE])
            ]))

            self.elements.append(pays_table)

    def add_rotations_page(self, rotations_data):
        """
        Ajoute la page des détails des rotations

        Args:
            rotations_data: Liste des rotations avec leurs vols
        """
        self.elements.append(PageBreak())

        # Titre de la section
        title = Paragraph("Détails des Rotations", self.styles['CustomTitle'])
        self.elements.append(title)
        self.elements.append(Spacer(1, 0.5*cm))

        # Pour chaque rotation
        for rotation in rotations_data:
            # Titre de la rotation avec bordure dorée
            rotation_title = Paragraph(
                f"<b>{rotation['id']}</b> - Total: {rotation['total']:.2f} €",
                self.styles['CustomHeading3']
            )

            # Tableau des vols
            vols_data = [['Date', 'Route', 'Horaires', 'Pays', 'Zone', 'Indemnité']]

            for vol in rotation['vols']:
                date_str = vol.get('date', '')
                if isinstance(date_str, str) and len(date_str) > 10:
                    date_str = date_str[:10]

                route = f"{vol.get('adep', '')} → {vol.get('ades', '')}"
                horaires = f"{vol.get('off', '')} - {vol.get('on', '')}"
                pays = str(vol.get('pays', ''))
                zone = str(vol.get('zone', ''))
                indemnite = f"{vol.get('indemnite', 0):.2f} €"

                # Diagnostic si présent
                if vol.get('diagnostic'):
                    pays = f"{pays}*"

                vols_data.append([
                    str(date_str),
                    route,
                    horaires,
                    pays,
                    zone,
                    indemnite
                ])

            vols_table = Table(vols_data, colWidths=[
                self.width * 0.12,
                self.width * 0.22,
                self.width * 0.20,
                self.width * 0.18,
                self.width * 0.10,
                self.width * 0.18
            ])

            vols_table.setStyle(TableStyle([
                # En-tête
                ('BACKGROUND', (0, 0), (-1, 0), COLOR_PRIMARY_NAVY),
                ('TEXTCOLOR', (0, 0), (-1, 0), COLOR_WHITE),
                ('FONTNAME', (0, 0), (-1, 0), self._get_font_name(True)),
                ('FONTSIZE', (0, 0), (-1, 0), 8),
                ('PADDING', (0, 0), (-1, 0), 6),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),

                # Corps
                ('BACKGROUND', (0, 1), (-1, -1), COLOR_WHITE),
                ('TEXTCOLOR', (0, 1), (-1, -1), COLOR_TEXT_PRIMARY),
                ('FONTNAME', (0, 1), (-1, -1), self._get_font_name()),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('PADDING', (0, 1), (-1, -1), 5),
                ('ALIGN', (5, 1), (5, -1), 'RIGHT'),

                # Bordures
                ('GRID', (0, 0), (-1, -1), 0.5, COLOR_BORDER),
                ('LINEABOVE', (0, 0), (-1, 0), 2, COLOR_ACCENT_GOLD),
                ('LINEBEFORE', (0, 0), (0, -1), 2, COLOR_ACCENT_GOLD),
                ('LINEAFTER', (-1, 0), (-1, -1), 2, COLOR_ACCENT_GOLD),

                # Alternance
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [COLOR_WHITE, COLOR_WARM_BEIGE])
            ]))

            # Grouper titre et tableau ensemble
            rotation_elements = [rotation_title, Spacer(1, 0.2*cm), vols_table, Spacer(1, 0.5*cm)]
            self.elements.append(KeepTogether(rotation_elements))

    def add_countries_prices_page(self, countries_prices):
        """
        Ajoute la page du tableau des pays et prix

        Args:
            countries_prices: Dictionnaire {pays: [liste de prix]}
        """
        self.elements.append(PageBreak())

        # Titre de la section
        title = Paragraph("Barèmes par Pays", self.styles['CustomTitle'])
        self.elements.append(title)
        self.elements.append(Spacer(1, 0.5*cm))

        intro = Paragraph(
            "Ce tableau présente les barèmes d'indemnités utilisés pour chaque pays identifié lors du traitement du journal de vol.",
            self.styles['CustomBody']
        )
        self.elements.append(intro)
        self.elements.append(Spacer(1, 0.5*cm))

        # Préparer les données du tableau
        table_data = [['Pays', 'Prix (€)', 'Périodes']]

        for pays, prix_list in sorted(countries_prices.items()):
            if not prix_list:
                continue

            # Si plusieurs prix (périodes différentes)
            if len(prix_list) == 1:
                prix_str = f"{prix_list[0]['price']:.2f} €"
                periode_str = prix_list[0].get('valid_from', 'Par défaut') or 'Par défaut'
            else:
                # Joindre plusieurs lignes
                prix_str = "\n".join([f"{p['price']:.2f} €" for p in prix_list])
                periode_str = "\n".join([
                    p.get('valid_from', 'Par défaut') or 'Par défaut'
                    for p in prix_list
                ])

            table_data.append([
                str(pays),
                prix_str,
                periode_str
            ])

        # Créer le tableau
        prices_table = Table(table_data, colWidths=[
            self.width * 0.40,
            self.width * 0.25,
            self.width * 0.35
        ])

        prices_table.setStyle(TableStyle([
            # En-tête
            ('BACKGROUND', (0, 0), (-1, 0), COLOR_PRIMARY_NAVY),
            ('TEXTCOLOR', (0, 0), (-1, 0), COLOR_WHITE),
            ('FONTNAME', (0, 0), (-1, 0), self._get_font_name(True)),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('PADDING', (0, 0), (-1, 0), 10),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),

            # Corps
            ('BACKGROUND', (0, 1), (-1, -1), COLOR_WHITE),
            ('TEXTCOLOR', (0, 1), (-1, -1), COLOR_TEXT_PRIMARY),
            ('FONTNAME', (0, 1), (-1, -1), self._get_font_name()),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('PADDING', (0, 1), (-1, -1), 8),
            ('ALIGN', (1, 1), (1, -1), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),

            # Bordures
            ('GRID', (0, 0), (-1, -1), 0.5, COLOR_BORDER),
            ('LINEABOVE', (0, 0), (-1, 0), 2, COLOR_ACCENT_GOLD),
            ('LINEBELOW', (0, -1), (-1, -1), 2, COLOR_ACCENT_GOLD),

            # Alternance
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [COLOR_WHITE, COLOR_WARM_BEIGE])
        ]))

        self.elements.append(prices_table)

    def build(self):
        """Génère le PDF final"""
        self.doc.build(
            self.elements,
            onFirstPage=self._add_header_footer,
            onLaterPages=self._add_header_footer
        )

    def _add_header_footer(self, canvas, doc):
        """Ajoute en-tête et pied de page"""
        self._add_header(canvas, doc)
        self._add_footer(canvas, doc)


def generate_pdf_report(filename, summary_data, rotations_data, countries_prices):
    """
    Génère un rapport PDF complet avec support UTF-8

    Args:
        filename: Nom du fichier PDF à créer
        summary_data: Données du résumé
        rotations_data: Données des rotations
        countries_prices: Prix par pays

    Returns:
        str: Chemin du fichier PDF généré
    """
    pdf = PDFGenerator(filename)

    # Page 1: Introduction et résumé
    pdf.add_title_page(summary_data)

    # Page 2: Détails des rotations
    pdf.add_rotations_page(rotations_data)

    # Page 3: Tableau des pays et prix
    pdf.add_countries_prices_page(countries_prices)

    # Générer le PDF
    pdf.build()

    return filename
