from collections import defaultdict

# from dataclasses import dataclass
from enum import Enum
from datetime import datetime
import pathlib
from typing import Optional
from log import logger
import numpy as np

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


class Document_service:
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


class Form_service:
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


class Drive_service:
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

    def get_list_of_forms_ids(self) -> list:
        forms = self.list_forms()
        return [form["id"] for form in forms["files"]]

    def __delete_all_forms(self) -> dict:
        forms = self.list_forms()
        for form in forms["files"]:
            self.service.files().delete(fileId=form["id"]).execute()
        return forms


class Sheet_service:
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


# @dataclass()
class Form_handler:
    def __init__(
        self,
        form_title: str = "Empty Form",
        documentTitle: str = "document form",
        form_service_instance: Optional[Form_service] = None,
        formId: Optional[str] = None,
    ) -> None:
        if not form_service_instance:
            self.form_service = Form_service(get_credentials())
        else:
            self.form_service = form_service_instance

        if formId:
            self.formId = formId
            logger.info(f"form captured with id [{self.formId}]")
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
            logger.info(f"form created with id [{self.formId}]")

        self.__post_init__()

    def __post_init__(self) -> None:
        self.form = self.get()
        self.form_url = self.get_form_url()
        self.revisionId = self.get_revisionId()
        self.form_type = self.get()["info"]["title"]
        logger.info(f"form name captured/create [{self.form_type}]")

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
        document_service_instance: Document_service,
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

    def __build_default_dict_for_form(self) -> defaultdict:
        """
        pull the forms and create a defaultdict[list] with the structure of
        {attribute_name: [question01_id, question02_id, ...],...}, with the exception of
        the candidate name which is a list of names. The Judge name and affiliation are
        repeated lists of the same question id to match the length of the other columns

        input: self
        attributes used: self.formId
        methods used: self.form_service.get()
        output: defaultdict[list]
        """
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
            max_length = max(len(v) for v in condidates_questions_dict.values())
            for key, value in condidates_questions_dict.items():
                if len(value) < max_length:
                    condidates_questions_dict[key] *= max_length
        except KeyError:
            logger.info(
                f"No questions yet for form [{self.form_type}] with id [{self.formId}]"
            )
        return condidates_questions_dict

    def __map_answers_to_questions(
        self, condidates_questions_dict: dict, response_dict: dict
    ) -> defaultdict:
        """
        maps answers from a response dict to the questions in
        condidates_questions_dict and returns a defaultdict[list]
        with similar structure to condidates_questions_dict but with the answers
        instead of the question ids

        input: condidates_questions_dict, response_dict
        attributes used: none
        methods used: none
        output: defaultdict[list]
        """
        mapped_dict = defaultdict(list)
        for things in condidates_questions_dict.items():
            key = things[0]
            value = things[1]
            if key != "candidate":
                for value_item in value:
                    try:
                        mapped_dict[key].append(response_dict[value_item])
                    except KeyError:
                        mapped_dict[key].append(np.nan)
            else:
                mapped_dict[key] = value
        return mapped_dict

    def __build_responses_list_for_form(self) -> list:
        """
        build a list of responses for a form with the structure of
        [{question01_id: answer01, question02_id: answer02, ...}, ...]

        input: self
        attributes used: self.formId, self.form_type
        methods used: self.form_service.get()
        output: list
        """
        response = self.get_responses()
        if not response:
            logger.info(
                f"No responses yet for form [{self.form_type}] with id [{self.formId}]"
            )
            return []
        list_of_judge_names = []
        responses_list = []
        logger.info(f"got [{len(response['responses'])}] responses")
        for response in response["responses"]:
            answers = response["answers"]
            questions_answers_dict = {}
            for question_key in list(answers.keys()):
                answers_text = answers[question_key]["textAnswers"]["answers"][0][
                    "value"
                ]
                questions_answers_dict[question_key] = answers_text

            # get the list of judge names
            for _, value in questions_answers_dict.items():
                if value not in ["CAA", "FCDO", "Secretariat"] and not value.isdigit():
                    list_of_judge_names.append(value)
            responses_list.append(questions_answers_dict)
        logger.info(f"list_of_judge_names [{list_of_judge_names}]")
        return responses_list

    def __get_responses_df(self) -> pd.core.frame.DataFrame:
        """
        build a dataframe of responses for a form with the structure of

        Judge Name | Affiliation | candidate | Question 1 | Question 2 | ...
        ---------------------------------------------------------------------
        Judge 1     | CAA         | candidate1| answer1    | answer2    | ...
        Judge 1     | CAA         | candidate2| answer1    | answer2    | ...
        Judge 2     | CAA         | candidate1| answer1    | answer2    | ...
        Judge 2     | CAA         | candidate2| answer1    | answer2    | ...

        input: self
        attributes used: none
        methods used: self.__build_default_dict_for_form(),
                    self.__build_responses_list_for_form(),
                    self.__map_answers_to_questions()
        output: pd.core.frame.DataFrame
        """
        condidates_questions_dict = self.__build_default_dict_for_form()
        responses_list = self.__build_responses_list_for_form()
        list_of_dfs = []
        for response_dict in responses_list:
            mapped_dict = self.__map_answers_to_questions(
                condidates_questions_dict, response_dict
            )
            response_df = pd.DataFrame.from_dict(mapped_dict)
            list_of_dfs.append(response_df)
        responses_df = pd.concat(list_of_dfs, ignore_index=True)
        responses_df_numeric = responses_df.apply(pd.to_numeric, errors="ignore")
        # remove empty lines
        responses_df_numeric = self.__remove_empty_lines(responses_df_numeric)
        return responses_df_numeric

    def __remove_empty_lines(
        self, df: pd.core.frame.DataFrame
    ) -> pd.core.frame.DataFrame:
        """
        returns a dataframe without lines of empty scores
        """
        scores_columns = [
            column
            for column in df.columns
            if column not in ["candidate", "Judge Name", "Affiliation"]
        ]
        clean_df = df.dropna(subset=scores_columns, how="all")
        logger.info(
            f"removed [{len(df) - len(clean_df)}] empty lines from form [{self.form_type}]"
        )
        return clean_df

    def temp_call(self) -> None:
        self.__get_candidates_by_rank()

    def __get_candidates_by_rank(self) -> pd.core.frame.DataFrame:
        """ "
        returns a dataframe with the mean of the answers for each candidate
        and sorts the candidates based on the score

        input: self
        attributes used: none
        methods used: self.__get_responses_df()
        output: pd.core.frame.DataFrame
        """
        candidates_mean_makes_dict = {}
        responses_df = self.__get_responses_df()
        # group by candidate and calculate the mean of each candidate
        responses_df_group = responses_df.groupby("candidate")
        for candidate, df in responses_df_group:
            self.__report_missing_scores(df)
            df["mean_per_judge"] = df.mean(axis=1, skipna=True, numeric_only=True)
            candidates_mean_makes_dict[candidate] = df["mean_per_judge"].mean()
        candidates_mean_makes_df = pd.DataFrame.from_dict(
            candidates_mean_makes_dict, orient="index"
        )

        candidates_mean_makes_df.sort_values(by=0, ascending=False, inplace=True)
        return candidates_mean_makes_df

    def __report_missing_scores(self, df: pd.core.frame.DataFrame) -> None:
        if df.isnull().values.any():
            null_df = df[df.isnull().any(axis=1)]
            for _, row in null_df.iterrows():
                judge_name = row["Judge Name"]
                candidate_name = row["candidate"]
                columns_with_null = [
                    key for key, value in row.items() if value != value
                ]
                logger.info(
                    f"candidate [{candidate_name}] has missing answers [{columns_with_null}] for judge [{judge_name}] in form [{self.form_type}] with id [{self.formId}]"
                )

    def __save_dataframes_to_csv(
        self, df: pd.core.frame.DataFrame, df_type: str = "responses"
    ) -> None:
        """
        saves a dataframe to a csv file with the name
        [df_type]_[date]_[form_type].csv

        input: df, df_type
        attributes used: self.form_type
        methods used: none
        output: none
        """
        current_file_path = pathlib.Path(__file__).parent.absolute()
        file_name = (
            df_type
            + "_"
            + str(datetime.now().isoformat()).replace(":", "_")
            + "_"
            + str(self.form_type)
            + ".csv"
        )
        df.to_csv(current_file_path / "data" / file_name)

    def export_all_responses_to_csv(self) -> None:
        responses_df = self.__get_responses_df()
        if responses_df is not None:
            self.__save_dataframes_to_csv(responses_df, "responses")

    def export_candidates_ranking_to_csv(self) -> None:
        candidates_mean_makes_df = self.__get_candidates_by_rank()
        if candidates_mean_makes_df is not None:
            self.__save_dataframes_to_csv(candidates_mean_makes_df, "rank")
