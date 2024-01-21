from abc import ABC, abstractmethod
from collections import defaultdict
from dataclasses import dataclass
from enum import Enum
from datetime import datetime
import pathlib
from typing import Optional

import pandas as pd
from googleapiclient.discovery import build

from cred import get_credentials
from settings import DOCUMENT_ID
from utils import (
    build_json_for_grid_question,
    build_json_for_select_question,
    build_json_for_text_question,
    build_requests_list,
    convert_form_type_enum_to_award_enum,
)


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


class service_template(ABC):
    def __init__(self) -> None:
        pass

    @abstractmethod
    def get(self, id: str) -> dict:
        pass


class document_service(service_template):
    def __init__(self, credentials: dict) -> None:
        self.service = build("docs", "v1", credentials=credentials)

    def get(self, id: str) -> dict:
        result = self.service.documents().get(documentId=id).execute()
        return result

    def get_award_info(
        self, document: dict, award: Enum = Award.INDIVIDUAL_APPLICATIONS
    ) -> dict:
        index_of_title = award.value[0]
        index_of_table = award.value[1]
        award_info = {}
        award_info[
            self.__get_award_title(document, index_of_title)
        ] = self.__get_first_column_of_table_text(document, index_of_table)
        return award_info

    def __get_award_title(self, document: dict, line: int) -> str:
        return document["body"]["content"][line]["paragraph"]["elements"][0]["textRun"][
            "content"
        ].strip()

    def __get_first_column_of_table_text(
        self, document: dict, index_of_table: int
    ) -> list:
        """
        Returns a list of strings from the first column of a Google Doc
        """
        table = document["body"]["content"][index_of_table]["table"]
        first_column = table["tableRows"]
        first_column_text = [
            element["tableCells"][0]["content"][0]["paragraph"]["elements"][0][
                "textRun"
            ]["content"].strip()
            for element in first_column
        ]
        return first_column_text[1:]


class form_service(service_template):
    def __init__(self, credentials: dict) -> None:
        self.service = build("forms", "v1", credentials=credentials)

    def get(self, formId: str) -> dict:
        result = self.service.forms().get(formId=formId).execute()
        return result

    def create_empty_form(
        self, form_title: str = "Empty Form", documentTitle: str = "Empty Form Document"
    ) -> dict:
        NEW_FORM = {
            "info": {
                "title": form_title,
                "documentTitle": documentTitle,
            }
        }
        form = self.service.forms().create(body=NEW_FORM).execute()
        return form


class drive_service(service_template):
    def __init__(self, credentials: dict) -> None:
        self.service = build("drive", "v3", credentials=credentials)

    def get(self, id: str) -> dict:
        result = self.service.files().get(fileId=id).execute()
        return result

    def list_forms(self) -> dict:
        result = (
            self.service.files()
            .list(q="mimeType='application/vnd.google-apps.form'")
            .execute()
        )
        return result

    def __delete_all_forms(self) -> dict:
        forms = self.list_forms()
        for form in forms["files"]:
            self.service.files().delete(fileId=form["id"]).execute()
        return forms


class sheet_service(service_template):
    def __init__(self, credentials: dict) -> None:
        self.service = build("sheets", "v4", credentials=credentials)

    def get_data_from_sheet(
        self, spreadsheetId: str, range: str, majorDimension: str = "ROWS"
    ) -> dict:
        result = (
            self.service.spreadsheets()
            .values()
            .get(
                spreadsheetId=spreadsheetId, range=range, majorDimension=majorDimension
            )
            .execute()
        )
        return result

    def get(self, id: str) -> dict:
        result = self.service.spreadsheets().get(spreadsheetId=id).execute()
        return result

    def list(self) -> dict:
        result = self.service.spreadsheets().list().execute()
        return result


@dataclass()
class form_handler:
    def __init__(
        self,
        form_title: str = "Empty Form",
        documentTitle: str = "document form",
        form_service_instance: Optional[form_service] = None,
        formId: Optional[str] = None,
    ) -> None:
        if not form_service_instance:
            self.form_service = form_service(get_credentials())
        else:
            self.form_service = form_service_instance

        if formId:
            self.formId = formId
            print(f"form captured with id {self.formId}")

        else:
            NEW_FORM = {
                "info": {
                    "title": form_title,
                    "documentTitle": documentTitle,
                }
            }
            form_object = (
                self.form_service.service.forms().create(body=NEW_FORM).execute()
            )
            self.formId = form_object["formId"]
            print(f"form created with id {self.formId}")

        self.__post_init__()

    def __post_init__(self) -> None:
        self.form = self.get()
        self.form_url = self.get_form_url()
        self.revisionId = self.get_revisionId()
        self.form_type = self.get()["info"]["title"]
        print(self.form_type)

    def __repr__(self) -> str:
        return f"Form Object: {str(self.formId)}"

    def delete(self) -> dict:
        result = self.form_service.service.forms().delete(formId=self.formId).execute()
        return result

    def get(self) -> dict:
        result = self.form_service.service.forms().get(formId=self.formId).execute()
        return result

    def update_form_title(self, new_form_title: str) -> dict:
        UPDATE_FORM = {
            "requests": [
                {
                    "updateFormInfo": {
                        "info": {"title": (new_form_title)},
                        "updateMask": "title",
                    }
                }
            ]
        }
        updated_form = (
            self.form_service.service.forms()
            .batchUpdate(formId=self.formId, body=UPDATE_FORM)
            .execute()
        )

        return updated_form

    def add_question(self, question: dict) -> dict:
        question_setting = (
            self.form_service.service.forms()
            .batchUpdate(formId=self.formId, body=question)
            .execute()
        )
        return question_setting

    def update_question(self, question: dict) -> dict:
        question_setting = (
            self.form_service.service.forms()
            .batchUpdate(formId=self.formId, body=question)
            .execute()
        )
        return question_setting

    def get_form_url(self) -> str:
        form_info = self.get()
        return form_info["responderUri"]

    def get_revisionId(self) -> str:
        form_info = self.get()
        return form_info["revisionId"]

    def get_responses(self) -> dict:
        responses = (
            self.form_service.service.forms()
            .responses()
            .list(formId=self.formId)
            .execute()
        )
        return responses

    def create_award_form(
        self,
        group_dataframes_of_applicatants: pd.core.groupby.DataFrameGroupBy,
        form_title: Enum,
        document_service_instance: document_service,
    ) -> dict:
        # build base objects for the form
        document_content = document_service_instance.get(DOCUMENT_ID)
        award_enum = convert_form_type_enum_to_award_enum(form_title)
        critria = document_service_instance.get_award_info(document_content, award_enum)

        # update the form title
        self.update_form_title(form_title.value)

        # build questions list for the form
        question_json_list = []
        dataframe = group_dataframes_of_applicatants.get_group(
            (award_enum.value[2], form_title.value)
        )
        for name in dataframe["Name"]:
            question_json = build_json_for_grid_question(
                list(critria.values())[0], name
            )
            question_json_list.append(question_json)

        question_json_list.append(build_json_for_select_question())
        question_json_list.append(build_json_for_text_question())

        self.add_question(build_requests_list(question_json_list))

        return self.form

    def get_questions_with_question_ids(self) -> pd.core.frame.DataFrame:
        form_content = self.form_service.get(formId=self.formId)
        condidates_questions_dict = defaultdict(list)
        try:
            for item in form_content["items"]:
                if "questionGroupItem" not in item.keys():
                    condidates_questions_dict[item["title"]].append(
                        item["questionItem"]["question"]["questionId"]
                    )
                else:
                    name_of_candidate = item["title"]
                    condidates_questions_dict["candidate"].append(name_of_candidate)
                    for question in item["questionGroupItem"]["questions"]:
                        condidates_questions_dict[
                            question["rowQuestion"]["title"]
                        ].append(question["questionId"])
            # expand the affliation and judge name columns to match the length of
            # the other columns
            max_length = max(len(v) for v in condidates_questions_dict.values())
            for key, value in condidates_questions_dict.items():
                if len(value) < max_length:
                    condidates_questions_dict[key] *= max_length
            condidates_questions_df = pd.DataFrame.from_dict(condidates_questions_dict)
            return condidates_questions_df
        except KeyError:
            print(f"No questions yet for form [{self.formId}]")
            return {}

    def get_responses_with_question_ids(self) -> dict:
        responses = self.get_responses()
        try:
            responses_with_question_ids = {}
            for response in responses["responses"]:
                answers_with_question_ids = {}
                for question_key in list(response["answers"].keys()):
                    answers_with_question_ids[question_key] = response["answers"][
                        question_key
                    ]["textAnswers"]["answers"][0]["value"]

                responses_with_question_ids[
                    response["responseId"]
                ] = answers_with_question_ids
            print(f"responses_with_question_ids after { responses_with_question_ids}")
            print(f"answers_with_question_ids { answers_with_question_ids}")
            ## convert all missing values to None
            return responses_with_question_ids
        except KeyError:
            print(f"No responses yet for form [{self.formId}]")
            return {}

    def map_responses_to_questions(self) -> pd.core.frame.DataFrame:
        responses_with_question_ids = self.get_responses_with_question_ids()
        condidates_questions_df = self.get_questions_with_question_ids()
        list_of_response_dfs = []
        if (
            responses_with_question_ids
            and type(condidates_questions_df) == pd.core.frame.DataFrame
        ):
            for _, response in responses_with_question_ids.items():
                temp_response_df = None
                print(condidates_questions_df)
                print(response)
                temp_response_df = condidates_questions_df.replace(
                    to_replace=response, inplace=False
                )
                list_of_response_dfs.append(temp_response_df)
            responses_df = pd.concat(list_of_response_dfs)
            current_file_path = pathlib.Path(__file__).parent.absolute()
            file_name = (
                "responses_"
                + str(datetime.now().isoformat()).replace(":", "_")
                + "_"
                + str(self.form_type)
                + ".csv"
            )
            responses_df.to_csv(current_file_path / "data" / file_name)
            return responses_df

    def get_candidates_by_rank(self) -> pd.core.frame.DataFrame:
        candidates_mean_makes_dict = {}
        responses_df = self.map_responses_to_questions()
        # convert the responses to numeric values
        responses_df_numeric = responses_df.apply(
            pd.to_numeric, errors="coerce"
        ).fillna(responses_df)

        # group by candidate and calculate the mean of each candidate
        responses_df_numeric_group = responses_df_numeric.groupby("candidate")
        for candidate, df in responses_df_numeric_group:
            df["mean_per_judge"] = df.select_dtypes("number").mean(axis=1)
            candidates_mean_makes_dict[candidate] = df["mean_per_judge"].mean()
        candidates_mean_makes_df = pd.DataFrame.from_dict(
            candidates_mean_makes_dict, orient="index"
        )

        candidates_mean_makes_df.sort_values(by=0, ascending=False, inplace=True)
        return candidates_mean_makes_df
