from abc import ABC, abstractmethod
from googleapiclient.discovery import build

class service_template(ABC):
    def __init__(self):
        pass

    @abstractmethod
    def get(self, id):
        pass

    @abstractmethod
    def list(self):
        pass

class form_service(service_template):
    def __init__(self, credentials):
        self.service = build('forms', 'v1', credentials=credentials)

    def get(self, id):
        result = self.service.forms().get(formId=id).execute()
        return result

    def list(self):
        result = self.service.forms().list().execute()
        return result

class drive_service(service_template):
    def __init__(self, credentials):
        self.service = build('drive', 'v3', credentials=credentials)

    def get(self, id):
        result = self.service.files().get(fileId=id).execute()
        return result

    def list(self):
        result = self.service.files().list().execute()
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
    
