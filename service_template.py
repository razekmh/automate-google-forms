from abc import ABC, abstractmethod
from googleapiclient.discovery import build
from dataclasses import dataclass


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

    def get_first_column_text(self, document: dict, index_of_table: int = 0) -> list:
        """
        Returns a list of strings from the first column of a Google Doc
        """
        table = document["body"]["content"][index_of_table]["table"]
        rows = table["tableRows"]
        first_column_text = []
        for row in rows:
            first_column_text.append(
                row["tableCells"][0]["content"][0]["paragraph"]["elements"][0][
                    "textRun"
                ]["content"]
            )
        return first_column_text


class form_service(service_template):
    def __init__(self, credentials: dict) -> None:
        self.service = build("forms", "v1", credentials=credentials)

    def get(self, id: str) -> dict:
        result = self.service.forms().get(formId=id).execute()
        return result


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
