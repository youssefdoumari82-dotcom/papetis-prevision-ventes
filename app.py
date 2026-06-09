
import io
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st

MOIS_FR = {
    1: "janvier", 2: "février", 3: "mars", 4: "avril",
    5: "mai", 6: "juin", 7: "juillet", 8: "août",
    9: "septembre", 10: "octobre", 11: "novembre", 12: "décembre"
}

st.set_page_config(page_title="PAPETIS - Prévision des ventes", layout="wide")

st.title("PAPETIS DISTRIBUTION - Outil de prévision des ventes")
st.caption("Prototype réalisé par Abdellah BEN HAYOUNE - Développeur principal")

def charger_donnees(uploaded_file):
    xls = pd.ExcelFile(uploaded_file)
    df = pd.read_excel(xls, sheet_name="Ventes globales", skiprows=3)
    df = df.dropna(how="all")
    df.columns = [str(c).strip() for c in df.columns]
    df = df.rename(columns={"Ventes (kMAD)": "Ventes"})
    df["Date"] = pd.to_datetime(df["Année"].astype(int).astype(str) + "-" + df["Mois"].astype(int).astype(str) + "-01")
    df = df.sort_values("Date").reset_index(drop=True)
    return df

def calculer_previsions(df, horizon=12):
    df = df.copy()
    x = df["t"].astype(float).values
    y = df["Ventes"].astype(float).values

    # Méthode 1 : moindres carrés ordinaires
    pente, intercept = np.polyfit(x, y, 1)
    df["Tendance_MCO"] = intercept + pente * df["t"]

    # Méthode 2 : moyennes mobiles centrées 12 mois
    df["Moyenne_mobile_12"] = df["Ventes"].rolling(window=12, center=True).mean()

    # Coefficients saisonniers multiplicatifs
    df["Ratio_saisonnier"] = df["Ventes"] / df["Tendance_MCO"]
    coefs = df.groupby("Mois")["Ratio_saisonnier"].mean()
    coefs = coefs / coefs.mean()
    df["Coef_saisonnier"] = df["Mois"].map(coefs)

    # Détection observations atypiques
    df["Ventes_desaisonnalisees"] = df["Ventes"] / df["Coef_saisonnier"]
    df["Residu"] = df["Ventes_desaisonnalisees"] - df["Tendance_MCO"]
    ecart_type = df["Residu"].std(ddof=1)
    df["Z_score"] = df["Residu"] / ecart_type
    atypiques = df.loc[df["Z_score"].abs() >= 2, ["Année", "Nom du mois", "Ventes", "Z_score"]]
    top2 = df.reindex(df["Z_score"].abs().sort_values(ascending=False).index).head(2)

    # Prévisions
    dernier_t = int(df["t"].max())
    dates = pd.date_range(df["Date"].max() + pd.offsets.MonthBegin(1), periods=horizon, freq="MS")
    prev = pd.DataFrame({
        "Date": dates,
        "Année": dates.year,
        "Mois": dates.month,
        "Nom du mois": [MOIS_FR[m] for m in dates.month],
        "t": range(dernier_t + 1, dernier_t + horizon + 1)
    })
    prev["Tendance_MCO"] = intercept + pente * prev["t"]
    prev["Coef_saisonnier"] = prev["Mois"].map(coefs)
    prev["Prévision"] = prev["Tendance_MCO"] * prev["Coef_saisonnier"]

    return df, prev, coefs, pente, intercept, atypiques, top2

def exporter_excel(df, prev, coefs):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="Calculs historiques")
        prev.to_excel(writer, index=False, sheet_name="Prévisions 2026")
        pd.DataFrame({"Mois": [MOIS_FR[i] for i in range(1,13)], "Coefficient": [coefs.loc[i] for i in range(1,13)]}).to_excel(writer, index=False, sheet_name="Saisonnalité")
    output.seek(0)
    return output

uploaded_file = st.file_uploader("Importer le fichier Excel PAPETIS", type=["xlsx", "xls", "csv"])

if uploaded_file is None:
    st.info("Veuillez importer le fichier papetis_ventes_historiques.xlsx pour lancer les calculs.")
else:
    df = charger_donnees(uploaded_file)
    df_calc, prev, coefs, pente, intercept, atypiques, top2 = calculer_previsions(df)

    col1, col2, col3 = st.columns(3)
    col1.metric("Dernière année historique", int(df_calc["Année"].max()))
    col2.metric("Pente mensuelle", f"{pente:.2f} kMAD/mois")
    col3.metric("Prévision annuelle 2026", f"{prev['Prévision'].sum():,.0f} kMAD".replace(",", " "))

    st.subheader("1. Équation de tendance")
    st.latex(rf"Y_t = {intercept:.2f} + {pente:.2f} \times t")

    st.subheader("2. Coefficients saisonniers multiplicatifs")
    saison = pd.DataFrame({"Mois": [MOIS_FR[i] for i in range(1, 13)], "Coefficient": [coefs.loc[i] for i in range(1, 13)]})
    st.dataframe(saison, use_container_width=True)

    st.subheader("3. Prévisions mensuelles")
    st.dataframe(prev[["Année", "Nom du mois", "t", "Tendance_MCO", "Coef_saisonnier", "Prévision"]].round(2), use_container_width=True)

    st.subheader("4. Graphique historique vs prévisions")
    fig, ax = plt.subplots(figsize=(11, 5))
    ax.plot(df_calc["Date"], df_calc["Ventes"], label="Historique observé")
    ax.plot(prev["Date"], prev["Prévision"], linestyle="--", marker="o", label="Prévision")
    ax.axvline(df_calc["Date"].max(), linestyle=":", label="Fin historique")
    ax.set_xlabel("Date")
    ax.set_ylabel("Ventes en kMAD")
    ax.set_title("Ventes historiques et prévisions 2026")
    ax.legend()
    ax.grid(True, alpha=0.3)
    st.pyplot(fig)

    st.subheader("5. Observations atypiques")
    st.write("Méthode utilisée : désaisonnalisation, résidu par rapport à la tendance, puis score standardisé.")
    st.write("Observations avec |Z-score| >= 2 :")
    st.dataframe(atypiques.round(2), use_container_width=True)
    st.write("Top 2 des observations les plus atypiques :")
    st.dataframe(top2[["Année", "Nom du mois", "Ventes", "Z_score"]].round(2), use_container_width=True)

    st.subheader("6. Export")
    excel_bytes = exporter_excel(df_calc, prev, coefs)
    st.download_button(
        label="Télécharger les résultats Excel",
        data=excel_bytes,
        file_name="papetis_resultats_previsions.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
