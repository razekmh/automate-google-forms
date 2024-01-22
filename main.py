# %%
from cred import get_credentials
from service_template import (
    # Document_service,
    Drive_service,
    Form_handler,
    # Form_service,
    # Sheet_service,
)
from log import logger

# from settings import MAJOR_DIMENSION, RANGE, SPREADSHEET_ID
# from utils import Form_Type, convert_sheet_data_to_df, process_df
from argparse import ArgumentParser


# %%
def export_all_forms_to_csv(drive_service_instance: Drive_service) -> None:
    forms_ids = [form["id"] for form in drive_service_instance.list_forms()["files"]]
    for form_id in forms_ids:
        form_instance = Form_handler(formId=form_id)
        form_instance.export_all_responses_to_csv()


def export_ranking_to_csv(drive_service_instance: Drive_service) -> None:
    forms_ids = [form["id"] for form in drive_service_instance.list_forms()["files"]]
    for form_id in forms_ids:
        form_instance = Form_handler(formId=form_id)
        form_instance.export_candidates_ranking_to_csv()


def temp_arg() -> None:
    drive = Drive_service(credentials=get_credentials())
    list_of_forms = drive.get_list_of_forms_ids()
    for formId in list_of_forms:
        form_instance = Form_handler(formId=formId)
        form_instance.temp_call()


def main() -> None:
    logger.info("Starting CAA forms process")
    Parser = ArgumentParser(description="")
    Parser.add_argument(
        "-a",
        "--action",
        choices=["export_all_candidates", "create_all", "export_ranking", "temp"],
        required=True,
    )
    args = Parser.parse_args()

    # Create service instances with credentials
    # form_service_instance = Form_service(get_credentials())
    drive_service_instance = Drive_service(get_credentials())
    # sheet_service_instance = Sheet_service(get_credentials())
    # document_service_instance = Document_service(get_credentials())

    if args.action == "export_all_candidates":
        export_all_forms_to_csv(drive_service_instance)
    elif args.action == "create_all":
        pass
    elif args.action == "export_ranking":
        export_ranking_to_csv(drive_service_instance)
    elif args.action == "temp":
        temp_arg()
    else:
        print("Invalid action")


if __name__ == "__main__":
    main()


# %%
# read the applicatants data from the google sheet
# group_dataframes_of_applicatants = process_df(
#     convert_sheet_data_to_df(
#         sheet_service_instance.get_data_from_sheet(
#             SPREADSHEET_ID, RANGE, MAJOR_DIMENSION
#         )
#     )
# )

# # %%
# # export all forms to local csv files
# forms_ids = [form["id"] for form in drive_service_instance.list_forms()["files"]]
# for form_id in forms_ids:
#     form_instance = Form_handler(formId=form_id)
#     form_instance.map_responses_to_questions()


# # %%
# # Create a form
# form = form_handler(form_service_instance=form_service_instance, form_title="Test Form")
# # %%
# # make award form
# form.create_award_form(
#     group_dataframes_of_applicatants, Form_Type.PROJECT, document_service_instance
# )
# # %%
# # create all forms
# for form_type in Form_Type:
#     form = Form_handler(
#         form_service_instance=form_service_instance,
#         form_title=form_type.value,
#         documentTitle=str(form_type.value) + " document",
#     )
#     form.create_award_form(
#         group_dataframes_of_applicatants, form_type, document_service_instance
#     )
#     print("Created form for: ", form_type.value, " form url", form.get_form_url())
# # %%


# def get_forms_names_and_links() -> list:
#     drive = Drive_service(get_credentials())
#     forms = drive.list_forms()["files"]
#     forms_names_and_links = []
#     for form in forms:
#         form_object = Form_handler(formId=form["id"])
#         forms_names_and_links.append(
#             {"name": form_object.form_type, "link": form_object.get_form_url()}
#         )
#     return forms_names_and_links


# print(get_forms_names_and_links())
# %%
