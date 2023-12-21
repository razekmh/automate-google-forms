from abc import ABC, abstractmethod
from googleapiclient.discovery import build
from dataclasses import dataclass


class service_template(ABC):
    def __init__(self):
        pass

    @abstractmethod
    def get(self, id):
        pass


class form_service(service_template):
    def __init__(self, credentials):
        self.service = build("forms", "v1", credentials=credentials)

    def get(self, id):
        result = self.service.forms().get(formId=id).execute()
        return result


class drive_service(service_template):
    def __init__(self, credentials):
        self.service = build("drive", "v3", credentials=credentials)

    def get(self, id):
        result = self.service.files().get(fileId=id).execute()
        return result

    def list_forms(self):
        result = (
            self.service.files()
            .list(q="mimeType='application/vnd.google-apps.form'")
            .execute()
        )
        return result


class sheet_service(service_template):
    def __init__(self, credentials):
        self.service = build("sheets", "v4", credentials=credentials)

    def get(self, id):
        result = self.service.spreadsheets().get(spreadsheetId=id).execute()
        return result

    def list(self):
        result = self.service.spreadsheets().list().execute()
        return result


class form_handler:
    def __init__(self, form_service, form_title="Empty Form"):
        self.form_service = form_service
        NEW_FORM = {
            "info": {
                "title": form_title,
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

    def update_name(self, new_name):
        # Update the title/name of the form
        UPDATE_FORM = {
            "requests": [
                {
                    "updateFormInfo": {
                        "info": {"title": (new_name)},
                        "updateMask": "title",
                    }
                }
            ]
        }
        # Use the update method to save changes
        updated_form = (
            self.form_service.service.forms()
            .batchUpdate(formId=self.form_id, body=UPDATE_FORM)
            .execute()
        )

        return updated_form
