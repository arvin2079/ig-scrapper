import os 
import json
from urllib.request import url2pathname, pathname2url


JSON_FILES_DIR = os.path.join(os.path.curdir ,'files')

def dump_creds_as_json(colc: dict, name: str):
    filepath = os.path.join(JSON_FILES_DIR, name.strip() + '.json')
    if not os.path.exists(JSON_FILES_DIR):
        os.mkdir(JSON_FILES_DIR)
    with open(filepath, 'w') as f:
        json.dump(colc, f)
        return pathname2url(os.path.normpath(filepath))


def load_creds_from_json_uri(uri: str):
    path = os.path.normpath(url2pathname(uri))
    if not os.path.exists(path):
        raise FileNotFoundError('credential file does not exist!')
    with open(path, 'r') as f:
        return json.load(f)
