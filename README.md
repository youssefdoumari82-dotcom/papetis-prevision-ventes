# Prototype PAPETIS - Prévision des ventes

Développeur principal : Abdellah BEN HAYOUNE

## Objectif
Ce prototype Streamlit permet d'importer le fichier `papetis_ventes_historiques.xlsx`, de calculer la tendance, les coefficients saisonniers multiplicatifs, les prévisions mensuelles 2026, de détecter les observations atypiques et d'exporter les résultats.

## Fonctionnalités réalisées
- Import automatique de la feuille `Ventes globales`.
- Calcul de tendance par moindres carrés ordinaires.
- Calcul d'une moyenne mobile centrée sur 12 mois.
- Calcul des coefficients saisonniers selon un modèle multiplicatif.
- Prévision des 12 mois suivant la dernière observation.
- Graphique historique observé vs prévisions.
- Détection des observations atypiques par Z-score.
- Export des résultats au format Excel.

## Installation
```bash
pip install -r requirements.txt
```

## Lancement
```bash
streamlit run app.py
```

## Résultats obtenus avec le jeu fourni
Équation de tendance :

`Y(t) = 1795.92 + 28.10 x t`

La pente indique une croissance moyenne d'environ `28.10` kMAD par mois.
