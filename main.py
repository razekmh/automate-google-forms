# %%
from cred import get_credentials
from service_template import (
    form_service,
    drive_service,
    sheet_service,
    form_handler,
    document_service,
    Award,
)
from utils import convert_sheet_data_to_df
from settings import SPREADSHEET_ID, RANGE, MAJOR_DIMENSION

# %%
# Create service instances with credentials
form_service_instance = form_service(get_credentials())
drive_service_instance = drive_service(get_credentials())
sheet_service_instance = sheet_service(get_credentials())
document_service_instance = document_service(get_credentials())
# %%
# Create a form
form = form_handler(form_service_instance, form_title="Test Form")

# %%
update_name = form.update_form_title("New Form Name")
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
                                "type": "CHECKBOX",
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
# %%
first_question = form.add_question(NEW_QUESTION)
print(first_question)
# %%
UPDATE_QUESTION = {
    "requests": [
        {
            "updateItem": {
                "item": {
                    "itemId": "09979f83",
                    "questionItem": {
                        "question": {
                            "questionId": "00d3ea29",
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
                "updateMask": "questionItem",
            }
        }
    ]
}

# %%
updated_questions = form.update_question(UPDATE_QUESTION)

# %%
print(
    convert_sheet_data_to_df(
        sheet_service_instance.get_data_from_sheet(
            SPREADSHEET_ID, RANGE, MAJOR_DIMENSION
        )
    )
)
# %%
