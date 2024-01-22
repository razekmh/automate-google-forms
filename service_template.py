from abc import ABC, abstractmethod
from collections import defaultdict

# from dataclasses import dataclass
from enum import Enum
from datetime import datetime
import pathlib
from typing import Optional
import itertools
from log import logger

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


class Service_template(ABC):
    def __init__(self) -> None:
        pass

    @abstractmethod
    def get(self, id: str) -> dict:
        pass


class Document_service(Service_template):
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


class Form_service(Service_template):
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


class Drive_service(Service_template):
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


class Sheet_service(Service_template):
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
            logger.info(f"form captured with id {self.formId}")
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
            logger.info(f"form created with id {self.formId}")

        self.__post_init__()

    def __post_init__(self) -> None:
        self.form = self.get()
        self.form_url = self.get_form_url()
        self.revisionId = self.get_revisionId()
        self.form_type = self.get()["info"]["title"]
        # print(self.form_type)

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

    def __extract_questions_id_and_name_for_text_and_select_questions(
        self, item: dict
    ) -> dict:
        if "questionGroupItem" in item.keys():
            logger.info(f"questionGroupItem in item.keys() {item['itemId']}")
            raise KeyError
        question_id = item["questionItem"]["question"]["questionId"]
        question_name = item["title"]
        return {question_id: question_name}

    def __extract_questions_id_and_name_for_a_grid_question(self, item: dict) -> dict:
        questions_id_and_name_for_grid_questions_dict = {}
        if "questionGroupItem" not in item.keys():
            logger.info(f"questionGroupItem not in item.keys() {item['itemId']}")
            raise KeyError
        candidate_name = item["title"]
        for question in item["questionGroupItem"]["questions"]:
            question_id = question["questionId"]
            question_name = question["rowQuestion"]["title"]
            questions_id_and_name_for_grid_questions_dict[question_id] = question_name
        return {candidate_name: questions_id_and_name_for_grid_questions_dict}

    def __build_default_dict_for_form(self) -> defaultdict:
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
            # print(condidates_questions_dict)
            max_length = max(len(v) for v in condidates_questions_dict.values())
            for key, value in condidates_questions_dict.items():
                if len(value) < max_length:
                    condidates_questions_dict[key] *= max_length
        except KeyError:
            logger.info(
                f"No questions yet for form [{self.form_type}] with id [{self.formId}]"
            )
        return condidates_questions_dict

    def __build_responses_list_for_form(self) -> list:
        response = self.get_responses()
        if not response:
            logger.info(
                f"No responses yet for form [{self.form_type}] with id [{self.formId}]"
            )
            return []
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
            responses_list.append(questions_answers_dict)
        return responses_list

    def __map_answers_to_questions(
        self, condidates_questions_dict: dict, response_dict: dict
    ) -> defaultdict:
        mapped_dict = defaultdict(list)
        for things in condidates_questions_dict.items():
            key = things[0]
            value = things[1]
            if key != "candidate":
                for value_item in value:
                    try:
                        mapped_dict[key].append(response_dict[value_item])
                    except KeyError:
                        mapped_dict[key].append("")
            else:
                mapped_dict[key] = value

        # expand the affliation and judge name columns to match the length of
        max_length = max(len(v) for v in mapped_dict.values())
        for key, value in mapped_dict.items():
            if len(value) < max_length:
                mapped_dict[key] *= max_length
        return mapped_dict

    def __get_responses_df(self) -> pd.core.frame.DataFrame:
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
        return responses_df

    def __extract_quetions_ids_and_responses_given_questions_ids(
        self, quetions_id_dict: dict
    ) -> list:
        # TODO: fix this to accomdate for the change in the dict structure

        """Takes a dict of {'questions id': 'questions title'}
        returns a list of the response to the form as
        a list of dicts {'questions title': 'response'}
        if a question was not answered the response will be empty string"""
        response = self.get_responses()
        if not response:
            logger.info(
                f"No responses yet for form [{self.form_type}] with id [{self.formId}]"
            )
            return []
        responses_list = []
        logger.info(f"got [{len(response['responses'])}] responses")
        for response in response["responses"]:
            answers = response["answers"]

            questions_answers_dict = {}
            for question_key in list(quetions_id_dict.keys()):
                if quetions_id_dict[question_key] in ["Judge Name", "Affiliation"]:
                    questions_answers_dict[quetions_id_dict[question_key]] = answers[
                        question_key
                    ]["textAnswers"]["answers"][0]["value"]
                else:
                    candidate_name = question_key
                    questions_answers_candidate_dict = {}
                    for candidate_question_key in list(
                        quetions_id_dict[question_key].keys()
                    ):
                        try:
                            questions_answers_candidate_dict[
                                quetions_id_dict[question_key][candidate_question_key]
                            ] = answers[candidate_question_key]["textAnswers"][
                                "answers"
                            ][0]["value"]
                        except KeyError:
                            logger.info(
                                f"question [{quetions_id_dict[question_key][candidate_question_key]}] for candidate [{candidate_name}] was not answered"
                            )
                            questions_answers_candidate_dict[
                                quetions_id_dict[question_key][candidate_question_key]
                            ] = ""
                    questions_answers_dict[
                        candidate_name
                    ] = questions_answers_candidate_dict
            responses_list.append(questions_answers_dict)
            # print(responses_list)
        return responses_list

    def __get_full_questions_id_and_name(self) -> dict:
        form_content = self.form_service.get(formId=self.formId)
        questions_id_and_name_dict = {}

        try:
            logger.info(f"got [{len(form_content['items'])}] questions")
            for item in form_content["items"]:
                if "questionGroupItem" not in item.keys():
                    questions_id_and_name_dict.update(
                        self.__extract_questions_id_and_name_for_text_and_select_questions(
                            item
                        )
                    )
                else:
                    questions_id_and_name_dict.update(
                        self.__extract_questions_id_and_name_for_a_grid_question(item)
                    )
            return questions_id_and_name_dict
        except KeyError:
            logger.info(f"No questions yet for form [{self.formId}]")
            raise KeyError

    def __build_list_of_responses_with_questions_names(self) -> list:
        questions_id_and_name_dict = self.__get_full_questions_id_and_name()
        responses_list = self.__extract_quetions_ids_and_responses_given_questions_ids(
            questions_id_and_name_dict
        )
        if len(responses_list) == 0:
            logger.info(
                f"No responses yet for form [{self.form_type}] with id [{self.formId}]"
            )
        return responses_list

    def temp_call(self) -> None:
        print(self.__get_responses_df())

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
            # print(condidates_questions_dict)
            max_length = max(len(v) for v in condidates_questions_dict.values())
            for key, value in condidates_questions_dict.items():
                if len(value) < max_length:
                    condidates_questions_dict[key] *= max_length
            condidates_questions_df = pd.DataFrame.from_dict(condidates_questions_dict)
            return condidates_questions_df
        except KeyError:
            logger.info(f"No questions yet for form [{self.formId}]")
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
            # print(f"responses_with_question_ids after { responses_with_question_ids}")
            # print(f"answers_with_question_ids { answers_with_question_ids}")
            ## convert all missing values to None
            return responses_with_question_ids
        except KeyError:
            logger.info(
                f"No responses yet for form [{self.form_type}] with id [{self.formId}]"
            )
            return {}

    def __fill_skipped_questions_answered(
        self,
        responses_with_question_ids: dict,
        condidates_questions_df: pd.core.frame.DataFrame,
        fillna: bool = True,
    ) -> dict:
        list_of_all_questions_ids = list(
            itertools.chain.from_iterable(
                [
                    condidates_questions_df[question].to_list()
                    for question in condidates_questions_df.columns
                    if question != "candidate"
                ]
            )
        )
        for question_id in list_of_all_questions_ids:
            if question_id not in responses_with_question_ids.keys():
                responses_with_question_ids[question_id] = ""
        return responses_with_question_ids

    def __build_list_of_response_dfs(self) -> pd.core.frame.DataFrame:
        responses_with_question_ids = self.get_responses_with_question_ids()
        condidates_questions_df = self.get_questions_with_question_ids()
        # check if all the questions are in the responses
        responses_with_question_ids = self.__fill_skipped_questions_answered(
            responses_with_question_ids, condidates_questions_df
        )
        # print(f"esponses_with_question_ids {responses_with_question_ids}")
        # print(f"condidates_questions_df {condidates_questions_df}")
        list_of_response_dfs = []
        if (
            responses_with_question_ids
            and type(condidates_questions_df) == pd.core.frame.DataFrame
        ):
            for _, response in responses_with_question_ids.items():
                temp_response_df = None
                # print(condidates_questions_df)
                # print(response)
                temp_response_df = condidates_questions_df.replace(
                    to_replace=response, inplace=False
                )
                list_of_response_dfs.append(temp_response_df)
            responses_df = pd.concat(list_of_response_dfs)
            # convert the responses to numeric values
            responses_df_numeric = responses_df.apply(
                pd.to_numeric, errors="coerce"
            ).fillna(responses_df)
            return responses_df_numeric

    def __get_candidates_by_rank(self) -> pd.core.frame.DataFrame:
        candidates_mean_makes_dict = {}
        responses_df = self.__build_list_of_response_dfs()

        # group by candidate and calculate the mean of each candidate
        if responses_df is not None:  # if the dataframe is not empty
            responses_df_group = responses_df.groupby("candidate")
            for candidate, df in responses_df_group:
                df["mean_per_judge"] = df.select_dtypes("number").mean(axis=1)
                candidates_mean_makes_dict[candidate] = df["mean_per_judge"].mean()
            candidates_mean_makes_df = pd.DataFrame.from_dict(
                candidates_mean_makes_dict, orient="index"
            )

            candidates_mean_makes_df.sort_values(by=0, ascending=False, inplace=True)
            return candidates_mean_makes_df

    def __save_dataframes_to_csv(
        self, df: pd.core.frame.DataFrame, df_type: str = "responses"
    ) -> None:
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
        responses_df = self.__build_list_of_response_dfs()
        if responses_df is not None:
            self.__save_dataframes_to_csv(responses_df, "responses")

    def export_candidates_ranking_to_csv(self) -> None:
        candidates_mean_makes_df = self.__get_candidates_by_rank()
        if candidates_mean_makes_df is not None:
            self.__save_dataframes_to_csv(candidates_mean_makes_df, "rank")
