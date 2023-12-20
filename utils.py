
def create_form(form_service, form_body):
    result = form_service.forms().create(body=form_body).execute()
    return result

def delete_form(form_service, form_id):
    result = form_service.forms().delete(formId=form_id).execute()
    return result

def get_form(form_service, form_id):
    result = form_service.forms().get(formId=form_id).execute()
    return result

def get_form_responder_uri(form_service, form_id):
    result = form_service.forms().getPublish(formId=form_id).execute()
    return result

def list_forms(form_service):
    result = form_service.forms().list().execute()
    return result

def update_form(form_service, form_id, form_body):
    result = form_service.forms().update(formId=form_id, body=form_body).execute()
    return result

def create_question(form_service, form_id, question_body):
    result = form_service.forms().batchUpdate(formId=form_id, body=question_body).execute()
    return result

def delete_question(form_service, form_id, question_id):
    result = form_service.forms().pages().delete(formId=form_id, pageId=question_id).execute()
    return result

def get_question(form_service, form_id, question_id):
    result = form_service.forms().pages().get(formId=form_id, pageId=question_id).execute()
    return result

def list_questions(form_service, form_id):
    result = form_service.forms().pages().list(formId=form_id).execute()
    return result

def update_question(form_service, form_id, question_id, question_body):
    result = form_service.forms().pages().update(formId=form_id, pageId=question_id, body=question_body).execute()
    return result

def create_response(form_service, form_id, response_body):
    result = form_service.forms().responses().create(formId=form_id, body=response_body).execute()
    return result

def delete_response(form_service, form_id, response_id):
    result = form_service.forms().responses().delete(formId=form_id, responseId=response_id).execute()
    return result

def get_response(form_service, form_id, response_id):
    result = form_service.forms().responses().get(formId=form_id, responseId=response_id).execute()
    return result

def list_responses(form_service, form_id):
    result = form_service.forms().responses().list(formId=form_id).execute()
    return result

def update_response(form_service, form_id, response_id, response_body):
    result = form_service.forms().responses().update(formId=form_id, responseId=response_id, body=response_body).execute()
    return result

def create_sheet(sheet_service, sheet_body):
    result = sheet_service.spreadsheets().create(body=sheet_body).execute()
    return result

def delete_sheet(sheet_service, sheet_id):
    result = sheet_service.spreadsheets().delete(spreadsheetId=sheet_id).execute()
    return result

def get_sheet(sheet_service, sheet_id):
    result = sheet_service.spreadsheets().get(spreadsheetId=sheet_id).execute()
    return result
    