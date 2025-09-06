import json
import os
import requests

from config import tvdb_apikey, fanarttv_apikey
from utils.plex import get_imdb_id
from datetime import datetime

from utils.logger import setup_logger
from utils.cache import get_cached_data, set_cached_data

TVDB_URL = "https://api4.thetvdb.com/v4"
FANARTTV_URL = "https://webservice.fanart.tv/v3"
MBID_URL = "https://musicbrainz.org/ws/2"
COVERART_URL = "https://coverartarchive.org"
WILDCARDS = ["?", "*"]
APP_HEADER = "DiscordRPC/v0.0.1"
LOGGER = setup_logger(__name__)


def get_artist_picture(artist_name: str) -> str | None:
    """Fetches the picture of a given artist using their name.

    Args:
        artist_name (str): Name of the artist to get picture

    Returns:
        str: URL of the picture
    """
    cache_key = f"artist_picture_{artist_name}"
    cached_data = get_cached_data(cache_key)
    if cached_data:
        return cached_data

    LOGGER.debug(f"Fetching {artist_name} picture")
    try:
        id_url = f"{MBID_URL}/artist?query={artist_name}"
        headers = {"accept": "application/json", "User-Agent": APP_HEADER}
        request = requests.get(url=id_url, headers=headers)
        data = request.json()
        artist_id = data["artists"][0]["id"]

        pic_url = f"{FANARTTV_URL}/music/{artist_id}?api_key={fanarttv_apikey}"
        request = requests.get(url=pic_url, headers=headers)
        data = request.json()
        if data.get("artistthumb"):
            pic_url = data["artistthumb"][0]["url"]
        else:
            pic_url = data["artistbackground"][0]["url"]

        set_cached_data(cache_key, pic_url)
    except requests.exceptions.RequestException as error:
        LOGGER.error(f"❌ Error while fetching {artist_name} picture: {error}")
        return None

    return pic_url


def get_item_cover(
    media_type: str, media_name=None, plex_item_id=None, media_artist=None
) -> str | None:
    """Gets an URL of a cover for a movie/show/album

    Args:
        media_name (str): Name of the media (e.g.: Vampire Hunter D: Bloodlust)
        media_type (str): The type of the media (tv, movie, music)
        media_artist (str, optional): The artist in the case of an album. Defaults to None.

    Returns:
        str: URL of the cover
    """
    if media_type not in ["tv", "movies", "music"]:
        LOGGER.error(f"❌ {media_type} is not a supported media type")
        return None

    cache_key = f"cover_{media_type}_{media_name}_{plex_item_id}_{media_artist}"
    cached_data = get_cached_data(cache_key)
    if cached_data:
        return cached_data

    res_url = get_media_art(media_name, media_type, plex_item_id, media_artist)

    if res_url:
        set_cached_data(cache_key, res_url)

    return res_url if res_url else None


def get_album_cover(mbid_id: str) -> str | None:
    """Gets album cover from MBID

    Args:
        mbid_id (str): MBID album id

    Returns:
        str: URL of the album cover
    """
    url = f"{COVERART_URL}/release/{mbid_id}/front"
    request = requests.get(url=url, allow_redirects=False)
    return request.headers.get("Location", None)


def get_media_art(
    media_name: str, media_type: str, plex_item_id=None, media_artist=None
) -> str | None:
    """Get the cover/poster for a media.

    Args:
        media_name (str): Name of the media (e.g.: Vampire Hunter D: Bloodlust)
        media_type (str): The type of the media (tv, movie, music)
        media_artist (str, optional): The artist in the case of an album. Defaults to None.

    Returns:
        str: id of the media
    """
    media_id = ""
    url = None
    res_url = None
    headers = {
            "accept": "application/json",
            "Authorization": f"Bearer {tvdb_login()}",
            "User-Agent": APP_HEADER,
        }

    if media_name:
        media_name = wildcard_security(media_name)

    if media_type == "tv":
        imdb_id = get_imdb_id(plex_item_id)
        res = requests.get(url=f"{TVDB_URL}/search/remoteid/{imdb_id}", headers=headers)
        tvdb_id = res.json()["data"][0]["series"]["id"]
        url = f"{TVDB_URL}/series/{tvdb_id}"
    elif media_type == "movies":
        imdb_id = get_imdb_id(plex_item_id)
        res = requests.get(url=f"{TVDB_URL}/search/remoteid/{imdb_id}", headers=headers)
        tvdb_id = res.json()["data"][0]["series"]["id"]
        url = f"{TVDB_URL}/movies/{tvdb_id}"
    elif media_type == "music":
        if media_artist:
            url = f"{MBID_URL}/release?query=artist:{media_artist}%20AND%20release:{media_name}"
        else:
            url = f"{MBID_URL}/release?query=release:{media_name}"
    try:
        encoded_url = requests.utils.requote_uri(url)
        request = requests.get(url=encoded_url, headers=headers)
        data = request.json()

        if media_type in ["tv", "movies"]:
            res_url = data["data"]["image"]
        elif media_type == "music":
            for release in data["releases"]:
                if wildcard_security(
                    release["title"]
                ).lower() == media_name.lower() and release.get("packaging") in [
                    "None",
                    "Jewel Case",
                ]:
                    media_id = release["id"]
                    break
            media_id = data["releases"][0]["id"]
            res_url = get_album_cover(media_id)
    except requests.exceptions.RequestException as error:
        LOGGER.error(f"❌ Error while getting {media_name} id: {error}")
        res_url = None
    return res_url


def wildcard_security(string: str) -> str:
    """Puts backslash in case of wildcard (for example: ? by XXXTENTACION)

    Args:
        string (str): String to check

    Returns:
        str: String with backslash before wildcards if found
    """
    res = ""
    for char in string:
        if char in WILDCARDS:
            res += f"\\{char}"
        else:
            res += char
    return res


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
