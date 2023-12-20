# %%
from googleapiclient.discovery import build
from google.oauth2 import service_account

# %%
# Set up credentials
credentials = service_account.Credentials.from_service_account_file(
    'token.json',
    scopes=['https://www.googleapis.com/auth/drive',
            'https://www.googleapis.com/auth/forms',
            "https://www.googleapis.com/auth/spreadsheets"]
)

# %%
# Create a service object
service = build('forms', 'v1', credentials=credentials)

# %%
# Request body for creating a form
NEW_FORM = {
    "info": {
        "title": "Quickstart form",
    }
}

# %%
# Request body to add a multiple-choice question
NEW_QUESTION = {
    "requests": [
        {
            "createItem": {
                "item": {
                    "title": (
                        "In what year did the United States land a mission on"
                        " the moon?"
                    ),
                    "questionItem": {
                        "question": {
                            "required": True,
                            "choiceQuestion": {
                                "type": "RADIO",
                                "options": [
                                    {"value": "1965"},
                                    {"value": "1967"},
                                    {"value": "1969"},
                                    {"value": "1971"},
                                ],
                                "shuffle": True,
                            },
                        }
                    },
                },
                "location": {"index": 0},
            }
        }
    ]
}

# # Define the form structure
# form_body = {
#     "title": "Your Form Title",
#     "description": "Your Form Description",
#     "items": [
#         {
#             "title": "Question 1",
#             "type": "TEXT",
#         },
#         {
#             "title": "Question 2",
#             "type": "MULTIPLE_CHOICE",
#             "multipleChoice": {
#                 "choices": [
#                     {"text": "Option 1"},
#                     {"text": "Option 2"},
#                     {"text": "Option 3"},
#                 ],
#             },
#         },
#         # Add more questions as needed
#     ],
# }

# %%
# Create the form
result = service.forms().create(body=NEW_FORM).execute()
# Adds the question to the form

# %%

question_setting = (
    service.forms()
    .batchUpdate(formId=result["formId"], body=NEW_QUESTION)
    .execute()
)

# %%
get_result = service.forms().get(formId=result["formId"]).execute()

print(get_result)


# print(f"Form created: {response['form']['formId']}")

# %%
# get the responses recorded by the form
response = (
    service.forms()
    .responses()
    .list(formId=result["formId"])
    .execute()
)
print(response)




# %%
