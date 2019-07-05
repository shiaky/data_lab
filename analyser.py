import pandas as pd
import numpy as np
import datetime
from typing import List, Dict

# utils


def add_years(d, years):
    try:
        return d.replace(year=d.year + years)
    except ValueError:
        return d + (datetime.date(d.year + years, 1, 1) -
                    datetime.date(d.year, 1, 1))


# Constants
DATA_BASE_PATH = "./Quelldaten_Case_2019_07/"
CUT_OFF_DATE = pd.Timestamp(datetime.date(2019, 3, 29))
CUT_OFF_DATE_PLUS_ONE = pd.Timestamp(add_years(CUT_OFF_DATE, 1))


# helper functions

def load_df(file_name: str, header: List[str], parse_dates: List[str] = None):
    def dateparse(x): return pd.datetime.strptime(x, '%d.%m.%Y')
    return pd.read_csv(DATA_BASE_PATH+file_name, sep=";",
                       names=header, parse_dates=parse_dates, date_parser=dateparse)


def get_full_dataset():
    df_gp_rating = pd.merge(df_gp, df_rating, how='left', left_on=[
        'Rating_ID'], right_on=['Rating_ID'])
    df_gp_rating_zusagen = pd.merge(df_zusage, df_gp_rating, how='left', left_on=[
        'GP_ID'], right_on=['GP_ID'])
    df_all = pd.merge(df_kreditgeschaeft, df_gp_rating_zusagen, how='left', left_on=[
        'GP_ID', 'Zusage_ID'], right_on=['GP_ID', 'Zusage_ID'])

    return df_all


# run always
df_gp = load_df("gp.dat", header=["GP_ID", "Rating_ID", "gp_Typ"])
df_rating = load_df("rating.dat", header=["Rating_ID", "Rating"])
df_zusage = load_df("zusage.dat", header=[
                    "Zusage_ID", "zu_Typ", "zu_Ursprungsbetrag", "zu_Offener_Betrag", "zu_Ziehungswahrscheinlichkeit", "zu_Laufzeitbeginn", "zu_Laufzeitende", "GP_ID"], parse_dates=["zu_Laufzeitbeginn", "zu_Laufzeitende"])
df_kreditgeschaeft = load_df("kreditgeschaeft.dat", header=[
    "Kreditgeschaeft_ID", "kred_Laufzeitbeginn", "kred_Laufzeitende", "kred_Nominal", "kred_Aktueller_Saldo", "kred_Zinssatz", "kred_Tilgungsfrequenz", "kred_Tilgungsrate", "STUFF1", "STUFF2", "kred_Marktfaehigkeit", "GP_ID", "Zusage_ID"], parse_dates=["kred_Laufzeitbeginn", "kred_Laufzeitende"])


def calc_nsfr():
        ## Net Stable Founding Ratio ##
    # zu_Laufzeitbeginn << stichtag
    # zu_laufzeitende >> stichtag
    # zu_laufzeitende << stichtag + 1a = 50%
    # zu_laufzeitende >> stichtag + 1a = 100%

    df_zusage_kredit = df_zusage.merge(
        df_kreditgeschaeft, how="left", on="Zusage_ID")

    df_zusage_kredit_filtered = df_zusage_kredit[(df_zusage_kredit["kred_Laufzeitbeginn"] < CUT_OFF_DATE_PLUS_ONE) & (
        df_zusage_kredit["kred_Laufzeitende"] > CUT_OFF_DATE)]

    df_zusage_kredit_filtered['nsfr'] = df_zusage_kredit_filtered.apply(
        lambda row: row["kred_Aktueller_Saldo"] if row['kred_Laufzeitende'] > CUT_OFF_DATE_PLUS_ONE else (row["kred_Aktueller_Saldo"]) * 0.5, axis=1)

    # ??? Verfügbare Liq??
    # zu_typ == einlage
    # sum(OFFENER bETRAG)
    nsfr_vl = df_zusage_kredit_filtered[df_zusage_kredit_filtered["zu_Typ"]
                                        == "Einlage"]['nsfr'].sum()

    # ??? Benötigte Liq ???
    # zu_typ == darlehn
    # sum(OFFENER bETRAG)
    nsfr_bl = df_zusage_kredit_filtered[df_zusage_kredit_filtered["zu_Typ"]
                                        == "Darlehen"]['nsfr'].sum()

    nsfr = nsfr_vl / nsfr_bl

    print("###Net Stable Founding Ratio###")

    print("Verfügbare Liquidität: %.0f" % nsfr_vl)
    print("Benötigte Liquidität: %.0f" % nsfr_bl)

    print("NSFR: %.4f" % nsfr)


def calc_lcr():
    ## Liquidity Coverage Ratio ##
    df_all = get_full_dataset()

    # ??? kurzfristig liquiditierbare aktiva??
    # zu_Typ = Darlehen
    # Laufzeitende nach Stichtag
    # Sum der aktuellen Salden

    lcr_kla = df_all[(df_all["zu_Typ"] == "Darlehen") & (
        df_all["kred_Laufzeitende"] > CUT_OFF_DATE)]["kred_Aktueller_Saldo"].sum()

    # ??? Erwartete Nettoabflüsse ???

    ea = df_all[(df_all["zu_Typ"] == "Einlage") & (df_all["kred_Laufzeitende"] > CUT_OFF_DATE) & (
        df_all["kred_Laufzeitende"] < CUT_OFF_DATE + pd.DateOffset(30))]["kred_Nominal"].sum()

    db = df_all[(df_all["zu_Typ"] == "Einlage") & (df_all["kred_Laufzeitbeginn"] > CUT_OFF_DATE) & (
        df_all["kred_Laufzeitbeginn"] < CUT_OFF_DATE + pd.DateOffset(30))]["kred_Aktueller_Saldo"].sum()

    abg = ea + db

    es = df_all[(df_all["zu_Typ"] == "Einlage") & (df_all["kred_Laufzeitbeginn"] > CUT_OFF_DATE) & (
        df_all["kred_Laufzeitbeginn"] < CUT_OFF_DATE + pd.DateOffset(30))]["kred_Aktueller_Saldo"].sum()

    td = 42  # TODO: calc real value
    # USE: df_all["Rating"].str.startswith("A")

    eng = es + td

    lcr_ena = abg - eng

    lcr = lcr_kla / lcr_ena

    print("###Liquidity Coverage Ratio###")

    print("Kurzfristig Liquiditierbare Aktiva: %.0f" % lcr_kla)
    print("Erwartete Nettoabflüsse: %.0f" % lcr_ena)

    print("LCR: %.4f" % lcr)


# procedures
if __name__ == '__main__':
    print("\n\n")
    calc_nsfr()
    print("\n\n--------------------\n\n")
    calc_lcr()
