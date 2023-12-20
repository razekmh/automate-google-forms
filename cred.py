from google.oauth2 import service_account

def get_credentials() -> service_account.Credentials:
    '''
    Returns credentials for Google API
    '''


    credentials = service_account.Credentials.from_service_account_file(
        'token.json',
        scopes=['https://www.googleapis.com/auth/drive',
                'https://www.googleapis.com/auth/forms',
                "https://www.googleapis.com/auth/spreadsheets"]
    )
    return credentials