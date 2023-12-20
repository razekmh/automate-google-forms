from abc import ABC, abstractmethod
from googleapiclient.discovery import build

class service_template(ABC):
    def __init__(self, service):
        self.service = service

    @abstractmethod
    def create(self, body):
        pass

    @abstractmethod
    def delete(self, id):
        pass

    @abstractmethod
    def get(self, id):
        pass

    @abstractmethod
    def list(self):
        pass

    @abstractmethod
    def update(self, id, body):
        pass

class form_service(service_template):
    def __init__(self, service, credentials):
        super().__init__(service)
        self.service = build('forms', 'v1', credentials=credentials)

    def create(self, body):
        result = self.service.forms().create(body=body).execute()
        return result

    def delete(self, id):
        result = self.service.forms().delete(formId=id).execute()
        return result

    def get(self, id):
        result = self.service.forms().get(formId=id).execute()
        return result

    def list(self):
        result = self.service.forms().list().execute()
        return result

    def update(self, id, body):
        result = self.service.forms().update(formId=id, body=body).execute()
        return result


class drive_service(service_template):
    def __init__(self, service, credentials):
        super().__init__(service)
        self.service = build('drive', 'v3', credentials=credentials)


    def create(self, body):
        result = self.service.files().create(body=body).execute()
        return result

    def delete(self, id):
        result = self.service.files().delete(fileId=id).execute()
        return result

    def get(self, id):
        result = self.service.files().get(fileId=id).execute()
        return result

    def list(self):
        result = self.service.files().list().execute()
        return result

    def update(self, id, body):
        result = self.service.files().update(fileId=id, body=body).execute()
        return result
    
class sheet_service(service_template):
    def __init__(self, service, credentials):
        super().__init__(service)
        self.service = build('sheets', 'v4', credentials=credentials)


    def create(self, body):
        result = self.service.spreadsheets().create(body=body).execute()
        return result

    def delete(self, id):
        result = self.service.spreadsheets().delete(spreadsheetId=id).execute()
        return result

    def get(self, id):
        result = self.service.spreadsheets().get(spreadsheetId=id).execute()
        return result

    def list(self):
        result = self.service.spreadsheets().list().execute()
        return result

    def update(self, id, body):
        result = self.service.spreadsheets().update(spreadsheetId=id, body=body).execute()
        return result
    

class form_handler():
    def __init__(self, service, body=None):
        if body:
            self.form = service.forms().create(body=body).execute()
        else:
            self.form = service.forms().create().execute()

    def create(self, body, service):
        self.form = service.forms().create(body=body).execute()
        return self.form

    def delete(self, id, service):
        result = service.forms().delete(formId=id).execute()
        return result
    
