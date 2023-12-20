from googleapiclient.discovery import build
from google.oauth2 import service_account

# Set up credentials
credentials = service_account.Credentials.from_service_account_file(
    'token.json',
    scopes=['https://www.googleapis.com/auth/forms']
)

# Create a service object
service = build('forms', 'v1', credentials=credentials)

# Define the form structure
form_body = {
    "title": "Your Form Title",
    "description": "Your Form Description",
    "items": [
        {
            "title": "Question 1",
            "type": "TEXT",
        },
        {
            "title": "Question 2",
            "type": "MULTIPLE_CHOICE",
            "multipleChoice": {
                "choices": [
                    {"text": "Option 1"},
                    {"text": "Option 2"},
                    {"text": "Option 3"},
                ],
            },
        },
        # Add more questions as needed
    ],
}

# Create the form
response = service.forms().create(body=form_body).execute()

print(f"Form created: {response['form']['formId']}")