import pandas as pd
from typing import DataFrame


def convert_sheet_data_to_df(sheet_data: dict) -> pd.DataFrame:
    values = sheet_data.get("values", [])
    values = [
        [inner_item.strip() for inner_item in outer_item] for outer_item in values
    ]
    df = pd.DataFrame(values[1:], columns=values[0])
    return df


def process_df(df: pd.DataFrame) -> pd.core.groupby.DataFrameGroupBy:
    project_alumni_filter = df["Individual/Project/Alumni"].isin(
        ["Alumni Association", "Project"]
    )
    df.loc[project_alumni_filter, "For Individual Nominations only"] = df[
        "Individual/Project/Alumni"
    ]
    groupdf = df.groupby(
        ["Individual/Project/Alumni", "For Individual Nominations only"]
    )
    return groupdf


def build_json_for_grid_question(selection_criteria, name_of_candidate, INDEX=0):
    answer_values = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"]
    options = [{"value": value} for value in answer_values]
    questions = [
        {"rowQuestion": {"title": question}} for question in selection_criteria
    ]
    NEW_GRID_QUESTION = {
        "createItem": {
            "item": {
                "title": name_of_candidate,
                "questionGroupItem": {
                    "grid": {
                        "columns": {
                            "type": "RADIO",
                            "options": options,
                        }
                    },
                    "questions": questions,
                },
            },
            "location": {"index": INDEX},
        }
    }

    return NEW_GRID_QUESTION


def build_requests_list(list_of_requests):
    requests_list = {"requests": list_of_requests}
    return requests_list
