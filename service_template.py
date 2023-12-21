from abc import ABC, abstractmethod
from googleapiclient.discovery import build

class service_template(ABC):
    def __init__(self):
        pass

    @abstractmethod
    def get(self, id):
        pass

class form_service(service_template):
    def __init__(self, credentials):
        self.service = build('forms', 'v1', credentials=credentials)

    def get(self, id):
        result = self.service.forms().get(formId=id).execute()
        return result

class drive_service(service_template):
    def __init__(self, credentials):
        self.service = build('drive', 'v3', credentials=credentials)

    def get(self, id):
        result = self.service.files().get(fileId=id).execute()
        return result

    def list_forms(self):
        result = self.service.files().list(q="mimeType='application/vnd.google-apps.form'").execute()
        return result
    
class sheet_service(service_template):
    def __init__(self, credentials):
        self.service = build('sheets', 'v4', credentials=credentials)

    def get(self, id):
        result = self.service.spreadsheets().get(spreadsheetId=id).execute()
        return result

    def list(self):
        result = self.service.spreadsheets().list().execute()
        return result

class form_handler():
    def __init__(self, service, form_title = "Empty Form"):
        self.service = service
        NEW_FORM = { "info": { "title": form_title,}}
        self.form = self.service.service.forms().create(body=NEW_FORM).execute()

    def create(self, body, service):
        self.form = service.service.forms().create(body=body).execute()
        return self.form

    def delete(self, id, service):
        result = service.service.forms().delete(formId=id).execute()
        return result
    
    def get(self, id, service):
        result = service.service.forms().get(formId=id).execute()
        return result
    
    def update_name(self, form_id, new_name):
        if not self.form:
            # If form is not already loaded, retrieve it
            self.form = self.service.get(form_id)
        
        # Update the title/name of the form
        UPDATE_FORM = {
    "requests": [
        {
            "updateFormInfo": {
                "info": {
                    "title": (
                        new_name
                    )
                },
                "updateMask": "title",
            }
        }
    ]
}
        # Use the update method to save changes
        updated_form = self.service.service.forms().batchUpdate(formId=form_id, body=UPDATE_FORM).execute()

        return updated_form
