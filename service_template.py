from abc import ABC, abstractmethod
from googleapiclient.discovery import build
from dataclasses import dataclass
from enum import Enum
from utils import (
    build_json_for_grid_question,
    build_requests_list,
    convert_form_type_enum_to_award_enum,
    Award,
)
import pandas as pd
from settings import DOCUMENT_ID


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
    def __init__(self):
        pass

    @abstractmethod
    def get(self, id):
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
        self, form_title="Empty Form", documentTitle="Empty Form Document"
    ):
        NEW_FORM = {
            "info": {
                "title": form_title,
                "documentTitle": documentTitle,
            }
        }
        form = self.service.service.forms().create(body=NEW_FORM).execute()
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

    def delete_all_forms(self) -> dict:
        forms = self.list_forms()
        for form in forms["files"]:
            self.service.files().delete(fileId=form["id"]).execute()
        return forms


class sheet_service(service_template):
    def __init__(self, credentials):
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

    def get(self, id):
        result = self.service.spreadsheets().get(spreadsheetId=id).execute()
        return result

    def list(self):
        result = self.service.spreadsheets().list().execute()
        return result


class form_handler:
    def __init__(
        self, form_service, form_title="Empty Form", documentTitle="document form"
    ):
        self.form_service = form_service
        NEW_FORM = {
            "info": {
                "title": form_title,
                "documentTitle": documentTitle,
            }
        }
        self.form = self.form_service.service.forms().create(body=NEW_FORM).execute()
        self.form_id = self.form["formId"]
        print(f"Form created: {self.form_id}")

    def __repr__(self) -> str:
        return f"Form Object: {str(self.form)}"

    def __post_init__(self):
        pass

    def delete(self):
        result = self.form_service.service.forms().delete(formId=self.form_id).execute()
        return result

    def get(self):
        result = self.form_service.service.forms().get(formId=self.form_id).execute()
        return result

    def update_form_title(self, new_form_title):
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
            .batchUpdate(formId=self.form_id, body=UPDATE_FORM)
            .execute()
        )

        return updated_form

    def add_question(self, question):
        question_setting = (
            self.form_service.service.forms()
            .batchUpdate(formId=self.form_id, body=question)
            .execute()
        )
        return question_setting

    def update_question(self, question):
        question_setting = (
            self.form_service.service.forms()
            .batchUpdate(formId=self.form_id, body=question)
            .execute()
        )
        return question_setting

    def get_form_url(self):
        form_info = self.get()
        return form_info["responderUri"]

    def get_responses(self):
        responses = (
            self.form_service.service.forms()
            .responses()
            .list(formId=self.form_id)
            .execute()
        )
        return responses

    def create_award_form(
        self,
        group_dataframes_of_applicatants: pd.core.groupby.DataFrameGroupBy,
        form_title: Enum,
        document_service_instance: document_service,
    ):
        self.update_form_title(form_title.value)
        document_content = document_service_instance.get(DOCUMENT_ID)
        award_enum = convert_form_type_enum_to_award_enum(form_title)
        critria = document_service_instance.get_award_info(document_content, award_enum)
        question_json_list = []
        dataframe = group_dataframes_of_applicatants.get_group(
            (award_enum.value[2], form_title.value)
        )
        for name in dataframe["Name"]:
            question_json = build_json_for_grid_question(
                list(critria.values())[0], name
            )
            question_json_list.append(question_json)
        request_body = build_requests_list(question_json_list)
        self.add_question(request_body)
        return self.form
