import json
import os
import requests

from config import tvdb_apikey, fanarttv_apikey
from datetime import datetime

TVDB_URL = "https://api4.thetvdb.com/v4"
FANARTTV_URL = "https://webservice.fanart.tv/v3"
MBID_URL = "https://musicbrainz.org/ws/2"


def get_artist_picture(artist_name: str) -> str:
    try:
        id_url = f"{MBID_URL}/artist?query={artist_name}"
        headers = {"accept": "application/json"}
        request = requests.get(url=id_url, headers=headers)
        data = request.json()
        artist_id = data["artists"][0]["id"]

        pic_url = f"{FANARTTV_URL}/music/{artist_id}?api_key={fanarttv_apikey}"
        request = requests.get(url=pic_url, headers=headers)
        data = request.json()
        pic_url = data["artistthumb"][0]["url"]
    except Exception:
        return None

    return pic_url


def get_item_cover(media_name: str, media_type: str, media_artist=None) -> str:
    res_url = ""

    media_id = get_media_id(media_name, media_type, media_artist)

    if not media_id:
        return None

    if media_type == "music":
        media_route = "music/albums"
    else:
        media_route = media_type
    url = f"{FANARTTV_URL}/{media_route}/{media_id}?api_key={fanarttv_apikey}"
    try:
        request = requests.get(url=url)
    except Exception:
        return None

    data = request.json()

    if media_type == "tv":
        res_url = data["tvposter"][0]["url"]
    elif media_type == "movies":
        res_url = data["movieposter"][0]["url"]
    else:
        _, album = data["albums"].popitem()
        res_url = album["albumcover"][0]["url"]

    return res_url


def get_media_id(media_name: str, media_type: str, media_artist=None) -> str:
    media_id = ""

    if media_type == "tv":
        url = f"{TVDB_URL}/search?q={media_name}&type=series"
    elif media_type == "movies":
        url = f"{TVDB_URL}/search?q={media_name}&type=movie"
    elif media_type == "music":
        if media_artist:
            url = f"{MBID_URL}/release?query=artist:{media_artist}%20AND%20release:{media_name}"
        else:
            url = f"{MBID_URL}/release?query=release:{media_name}"
    tvdb_token = tvdb_login()
    headers = {"accept": "application/json", "Authorization": f"Bearer {tvdb_token}"}
    try:
        encoded_url = requests.utils.requote_uri(url)
        request = requests.get(url=encoded_url, headers=headers)
        data = request.json()
        if media_type == "tv":
            media_id = data["data"][0]["tvdb_id"]
        elif media_type == "movies":
            for remote_id in data["data"][0]["remote_ids"]:
                if remote_id["sourceName"] == "IMDB":
                    media_id = remote_id["id"]
                    break
        elif media_type == "music":
            media_id = data["releases"][0]["release-group"]["id"]
    except Exception:
        media_id = None
    return media_id


def tvdb_login() -> str:
    if not os.path.isfile("./token_bearer.json"):
        write_token(token_bearer=get_bearer()["data"]["token"])

    with open("./token_bearer.json", "r") as file:
        file_data = json.load(file)

    today = datetime.today()
    token_date = datetime.strptime(file_data["date"], "%d-%m-%Y")
    time_diff = (today.year - token_date.year) * 12 + (today.month - token_date.month)
    if time_diff >= 1:
        token = get_bearer()["data"]["token"]
        write_token(token_bearer=token)
        return token

    return file_data["token"]


def get_bearer() -> dict:
    headers = {"Content-type": "application/json", "accept": "application/json"}

    request = requests.post(
        url=f"{TVDB_URL}/login", headers=headers, json={"apikey": tvdb_apikey}
    )

    return request.json()


def write_token(token_bearer: str):
    token = {"token": token_bearer, "date": datetime.today().strftime("%d-%m-%Y")}
    with open("./token_bearer.json", "w") as file:
        json.dump(token, file)
