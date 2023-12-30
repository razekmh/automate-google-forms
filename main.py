# %%
from cred import get_credentials
from service_template import (
    form_service,
    drive_service,
    sheet_service,
    form_handler,
    document_service,
)
from utils import (
    convert_sheet_data_to_df,
    process_df,
    get_questions_with_question_ids,
    Award,
    Form_Type,
)
from settings import SPREADSHEET_ID, RANGE, MAJOR_DIMENSION, DOCUMENT_ID
import pandas as pd

# %%
# Create service instances with credentials
form_service_instance = form_service(get_credentials())
drive_service_instance = drive_service(get_credentials())
sheet_service_instance = sheet_service(get_credentials())
document_service_instance = document_service(get_credentials())
# %%
# read the applicatants data from the google sheet
group_dataframes_of_applicatants = process_df(
    convert_sheet_data_to_df(
        sheet_service_instance.get_data_from_sheet(
            SPREADSHEET_ID, RANGE, MAJOR_DIMENSION
        )
    )
)
# %%
# Create a form
form = form_handler(form_service_instance, form_title="Test Form")
# %%
# make award form
form.create_award_form(
    group_dataframes_of_applicatants, Form_Type.PROJECT, document_service_instance
)
