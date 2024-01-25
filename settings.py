from pathlib import Path
import os

if Path("local_settings.py").exists():
    from local_settings import push_local_settings_to_env

    push_local_settings_to_env()

current_folder_path = Path(__file__).parent


SPREADSHEET_ID = os.environ.get("SPREADSHEET_ID", default="example spreadsheetId")
RANGE = os.environ.get("RANGE", default="example range")
MAJOR_DIMENSION = os.environ.get("MAJOR_DIMENSION", default="ROWS")
DOCUMENT_ID = os.environ.get("DOCUMENT_ID", default="example documentId")
LOG_DIRECTORY_PATH = Path(
    os.environ.get("DATA_DIRECTORY_PATH", default=current_folder_path / "logs")
)
DEBUG = os.environ.get("DEBUG", default=False)
