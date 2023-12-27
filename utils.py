import pandas as pd


def convert_sheet_data_to_df(sheet_data: dict) -> pd.DataFrame:
    values = sheet_data.get("values", [])
    df = pd.DataFrame(values[1:], columns=values[0])
    return df
