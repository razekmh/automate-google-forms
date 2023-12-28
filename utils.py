import pandas as pd
from service_template import Award
from settings import SPREADSHEET_ID, RANGE, MAJOR_DIMENSION, DOCUMENT_ID


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


def make_form(groupdf: pd.core.groupby.DataFrameGroupBy, document_service_instance):
    types_pf_award = [index[0] for index, _ in groupdf]
    titles_of_forms = [index[1] for index, _ in groupdf]
    document_content = document_service_instance.get(DOCUMENT_ID)

    for form_title in titles_of_forms:
        question_json_list = []
        if form_title == "Project":
            award_type = "Project"
            critria = document_service_instance.get_award_info(
                document_content, Award.COLLABORATIVE_PROJECTS
            )
            dataframe = groupdf.get_group(("Project", "Project"))
            for name in dataframe["Name"]:
                question_json = build_json_for_grid_question(
                    list(critria.values())[0], name
                )
                question_json_list.append(question_json)
            request_body = build_requests_list(question_json_list)
            return request_body

        elif form_title == "Alumni Association":
            award_type = "Alumni Association"
            critria = document_service_instance.get_award_info(
                document_content, Award.ALLUMNI_ASSOCIATIONS
            )
            dataframe = groupdf.get_group(("Alumni Association", "Alumni Association"))
            pass

        else:
            award_type = "Individual"
            critria = document_service_instance.get_award_info(
                document_content, Award.INDIVIDUAL_APPLICATIONS
            )
            dataframe = groupdf.get_group(("Individual", form_title))


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
