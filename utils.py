import logging
import json
import os
import requests

from config import tvdb_apikey, fanarttv_apikey
from datetime import datetime

TVDB_URL = "https://api4.thetvdb.com/v4"
FANARTTV_URL = "https://webservice.fanart.tv/v3"
MBID_URL = "https://musicbrainz.org/ws/2"

LOGGER = logging.getLogger(__name__)
logging.basicConfig(
    format="[%(levelname)s] - %(asctime)s %(message)s",
    datefmt="%d/%m/%Y %H:%M:%S",
    handlers=[logging.FileHandler("plex_rpc.log"), logging.StreamHandler()],
    encoding="utf-8",
    level=logging.INFO,
)


def get_artist_picture(artist_name: str) -> str:
    """Fetches the picture of a given artist using their name.

    Args:
        artist_name (str): Name of the artist to get picture

    Returns:
        str: URL of the picture
    """
    LOGGER.debug(f"Fetching {artist_name} picture")
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
    except Exception as error:
        LOGGER.error(f"Error while fetching {artist_name} picture: {error}")
        return None

    return pic_url


def get_item_cover(media_name: str, media_type: str, media_artist=None) -> str:
    """Gets an URL of a cover for a movie/show/album

    Args:
        media_name (str): Name of the media (e.g.: Vampire Hunter D: Bloodlust)
        media_type (str): The type of the media (tv, movie, music)
        media_artist (str, optional): The artist in the case of an album. Defaults to None.

    Returns:
        str: URL of the cover
    """
    res_url = ""

    if media_type not in ["tv", "movies", "music"]:
        LOGGER.error(f"{media_type} is not a supported media type")
        return None

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
    except Exception as error:
        LOGGER.error(f"Error while fetching {media_name} artwork: {error}")
        return None

    data = request.json()

    if media_type == "tv":
        res_url = data["tvposter"][0]["url"]
    elif media_type == "movies":
        res_url = data["movieposter"][0]["url"]
    elif media_type == "music":
        _, album = data["albums"].popitem()
        res_url = album["albumcover"][0]["url"]

    return res_url


def get_media_id(media_name: str, media_type: str, media_artist=None) -> str:
    """Get an id recognizable by fanart.tv for a media.
    IMDB id for movies
    TVDB id for shows
    MBID id for musics

    Args:
        media_name (str): Name of the media (e.g.: Vampire Hunter D: Bloodlust)
        media_type (str): The type of the media (tv, movie, music)
        media_artist (str, optional): The artist in the case of an album. Defaults to None.

    Returns:
        str: id of the media
    """
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
    except Exception as error:
        LOGGER.error(f"Error while getting {media_name} id: {error}")
        media_id = None
    return media_id


def tvdb_login() -> str:
    """Gets TVDB token stored locally or calls to generate a new one

    Returns:
        str: TVDB token
    """
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
    """Calls TVDB API to get a token from API key

    Returns:
        dict: TVDB API response
    """
    headers = {"Content-type": "application/json", "accept": "application/json"}

    request = requests.post(
        url=f"{TVDB_URL}/login", headers=headers, json={"apikey": tvdb_apikey}
    )

    return request.json()


def write_token(token_bearer: str):
    """Writes TVDB token to local file called token_bearer.json

    Args:
        token_bearer (str): The TVDB token to write
    """
    token = {"token": token_bearer, "date": datetime.today().strftime("%d-%m-%Y")}
    with open("./token_bearer.json", "w") as file:
        json.dump(token, file)
