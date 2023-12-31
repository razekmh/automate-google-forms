# %%
from cred import get_credentials
from service_template import (
    document_service,
    drive_service,
    form_handler,
    form_service,
    sheet_service,
)
from settings import MAJOR_DIMENSION, RANGE, SPREADSHEET_ID
from utils import Form_Type, convert_sheet_data_to_df, process_df

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
# # Create a form
# form = form_handler(form_service_instance=form_service_instance, form_title="Test Form")
# # %%
# # make award form
# form.create_award_form(
#     group_dataframes_of_applicatants, Form_Type.PROJECT, document_service_instance
# )
# %%
# create all forms
for form_type in Form_Type:
    form = form_handler(
        form_service_instance=form_service_instance,
        form_title=form_type.value,
        documentTitle=str(form_type.value) + " document",
    )
    form.create_award_form(
        group_dataframes_of_applicatants, form_type, document_service_instance
    )
    print("Created form for: ", form_type.value, " form url", form.get_form_url())
# %%
