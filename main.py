# %%
from cred import get_credentials
from service_template import form_service, drive_service, sheet_service, form_handler
# %%
# Create service instances with credentials
form_service_instance = form_service(get_credentials())
drive_service_instance = drive_service(get_credentials())
sheet_service_instance = sheet_service(get_credentials())
# %%
# Create a form
form = form_handler(form_service_instance, form_title = "Test Form")

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
