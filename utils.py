import pandas as pd
from settings import SPREADSHEET_ID, RANGE, MAJOR_DIMENSION, DOCUMENT_ID
from enum import Enum


class Award(Enum):
    INDIVIDUAL_APPLICATIONS = (3, 4, "Individual")
    COLLABORATIVE_PROJECTS = (6, 7, "Project")
    ALLUMNI_ASSOCIATIONS = (19, 20, "Alumni Association")


class Form_Type(Enum):
    ALLUMNI_ASSOCIATIONS = "Alumni Association"
    HUMAN_RIGHTS = "Achievement in Human Rights"
    INNOVATIONS = "Achievement in Innovations and Entrepreneurship"
    POLITICS = "Achievement in Politics"
    SCIENCE = "Achievement in Science"
    SOCIAL_ENVIRONMENTAL = "Achievement in Social & Environmental Impact"
    INDUSTRY = "Achievement in the industry of expertise (professional)"
    OTHER = "Other Area"
    PUBLICATIONS = "Outstanding Publications"
    PROJECT = "Project"


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


# def select_enum(form_title):
#     return [award_enum.value for award_enum in  enumerate(Award) if award_enum.value[2] == award_type][0]


def make_form(form_title: Enum):
    if form_title == Form_Type.PROJECT:
        pass
    elif form_title == Form_Type.ALLUMNI_ASSOCIATIONS:
        pass
    else:
        pass


def build_json_for_grid_question(selection_criteria, name_of_candidate, INDEX=0):
    answer_values = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"]
    options = [{"value": value} for value in answer_values]
    cleaned_name_of_candidate = name_of_candidate.replace("\n", " ")
    questions = [
        {"rowQuestion": {"title": question}} for question in selection_criteria
    ]
    NEW_GRID_QUESTION = {
        "createItem": {
            "item": {
                "title": cleaned_name_of_candidate,
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


def convert_form_type_enum_to_award_enum(form_title: Enum):
    if form_title == Form_Type.PROJECT:
        return Award.COLLABORATIVE_PROJECTS
    elif form_title == Form_Type.ALLUMNI_ASSOCIATIONS:
        return Award.ALLUMNI_ASSOCIATIONS
    else:
        return Award.INDIVIDUAL_APPLICATIONS
