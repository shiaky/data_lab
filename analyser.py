import pandas as pd
import numpy as np
from typing import List


# Constants
DATA_BASE_PATH = "./Quelldaten_Case_2019_07/"


# helper functions

def load_df(file_name: str, header: List[str], parse_dates: List[str] = None):
    def dateparse(x): return pd.datetime.strptime(x, '%d.%m.%Y')
    return pd.read_csv(DATA_BASE_PATH+file_name, sep=";",
                       names=header, parse_dates=parse_dates, date_parser=dateparse)


def get_full_dataset():
    df_gp = load_df("gp.dat", header=["GP_ID", "Rating_ID", "gp_Typ"])
    df_rating = load_df("rating.dat", header=["Rating_ID", "Rating"])
    df_zusage = load_df("zusage.dat", header=[
                        "Zusage_ID", "zu_Typ", "zu_Ursprungsbetrag", "zu_Offener_Betrag", "STUFF0", "zu_Laufzeitbeginn", "zu_Laufzeitende", "GP_ID"], parse_dates=["zu_Laufzeitbeginn", "zu_Laufzeitende"])
    df_kreditgeschaeft = load_df("kreditgeschaeft.dat", header=[
        "Kreditgeschaeft_ID", "kred_Laufzeitbeginn", "kred_Laufzeitende", "kred_Nominal", "kred_Aktueller_Saldo", "kred_Zinssatz", "kred_Tilgungsfrequenz", "kred_Tilgungsrate", "STUFF1", "STUFF2", "STUFF3", "GP_ID", "Zusage_ID"], parse_dates=["kred_Laufzeitbeginn", "kred_Laufzeitende"])

    df_gp_rating = pd.merge(df_gp, df_rating, how='left', left_on=[
        'Rating_ID'], right_on=['Rating_ID'])
    df_gp_rating_zusagen = pd.merge(df_zusage, df_gp_rating, how='left', left_on=[
        'GP_ID'], right_on=['GP_ID'])
    df_all = pd.merge(df_kreditgeschaeft, df_gp_rating_zusagen, how='left', left_on=[
        'GP_ID', 'Zusage_ID'], right_on=['GP_ID', 'Zusage_ID'])

    return df_all


# procedures
if __name__ == '__main__':

    df_all = get_full_dataset()

    print(df_all.head())
    print(df_all.info())
