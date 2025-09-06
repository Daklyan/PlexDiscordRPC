import requests
import json
import urllib3

from config import (
    plex_address,
    plex_port,
    x_plex_token,
    username,
    libraries,
)


def get_activity(
    plex_address=plex_address, plex_port=plex_port, x_plex_token=x_plex_token
):
    headers = {"accept": "application/json"}
    with urllib3.warnings.catch_warnings():
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        r = requests.get(
            f"https://{plex_address}:{plex_port}/status/sessions?X-Plex-Token={x_plex_token}",
            headers=headers,
            verify=False,
        )
    return dict(data=json.loads(r.text), code=r.status_code)


def get_my_activity(username=username, libraries=libraries):
    data = get_activity()["data"]
    for stream in data["MediaContainer"].get("Metadata", {}):
        if (len(libraries) == 0 or stream["librarySectionTitle"] in libraries) and (
            username == "" or stream["User"]["title"] == username
        ):
            # print(json.dumps(stream, indent=4))
            return stream
    return None


def get_metadata(plex_item_id=None) -> dict:
    if plex_item_id:
        headers = {"accept": "application/json"}
        with urllib3.warnings.catch_warnings():
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            r = requests.get(
                f"https://{plex_address}:{plex_port}/library/metadata/{plex_item_id}?X-Plex-Token={x_plex_token}",
                headers=headers,
                verify=False,
            )
            return json.loads(r.text)
    return {}


def get_imdb_id(plex_item_id=None) -> str:
    metadata = get_metadata(plex_item_id)
    return metadata["MediaContainer"]["Metadata"][0]["Guid"][0]["id"].split("/")[-1]
