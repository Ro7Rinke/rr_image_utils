import secrets
import os
import shutil
from pathlib import Path
from debug_log import print_log

DATA_FOLDER_PATH = Path("data")
TEMP_DATA_FOLDER_PATH = DATA_FOLDER_PATH / "temp"
SESSIONS_DATA_FOLDER = TEMP_DATA_FOLDER_PATH / "sessions"

def new_uuid():
    return secrets.token_urlsafe(8)

def ensure_path(path):
    if not isinstance(path, Path):
        return Path(path.strip('"'))
    return path

def get_dirs(path = "."):
    path = ensure_path(path)
    return [d for d in os.listdir(path) if os.path.isdir(os.path.join(path, d))]

def new_dir(path, name):
    path = ensure_path(path)
    os.makedirs(path / name, exist_ok=True)

def get_files(path):
    path = ensure_path(path)
    return [f for f in path.iterdir() if f.is_file()]

def copy_file(source_path, destination_path):
    source_path = ensure_path(source_path)
    destination_path = ensure_path(destination_path)
    shutil.copyfile(source_path, destination_path)

def clear_temp():
    if TEMP_DATA_FOLDER_PATH.is_dir():
        shutil.rmtree(TEMP_DATA_FOLDER_PATH)
        print_log("Deleted temp folder", title="CLEAR TEMP")

def new_session():
    new_session_id = new_uuid()
    new_dir(DATA_FOLDER_PATH, 'temp')
    new_dir(SESSIONS_DATA_FOLDER, new_session_id)
    return new_session_id

def clear_sessions():
    if SESSIONS_DATA_FOLDER.is_dir():
        session_folders = get_dirs(SESSIONS_DATA_FOLDER)
        for folder in session_folders:
            print_log(SESSIONS_DATA_FOLDER / folder, title='Session folders DELETE')
            shutil.rmtree(SESSIONS_DATA_FOLDER / folder)

def get_session(session_id):
    if session_id:
        print_log(get_dirs(SESSIONS_DATA_FOLDER))
        files = get_files(SESSIONS_DATA_FOLDER / session_id / 'images')
        for file in files:
            print_log(file.stem)
        return session_id
    
    clear_sessions()
    return new_session()

def get_session_path(session_id):
    return SESSIONS_DATA_FOLDER / session_id
    
def get_session_images_path(session_id):
    session_path = get_session_path(session_id)
    new_dir(session_path, 'images')
    return session_path / 'images'
