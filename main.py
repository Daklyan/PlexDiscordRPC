import time
import logging
import subprocess
import tautulli

from config import client_id
from pypresence import Presence
from pypresence.exceptions import PyPresenceException


RPC = Presence(client_id)


LOGGER = logging.getLogger(__name__)
logging.basicConfig(
    format="[%(levelname)s] - %(asctime)s %(message)s",
    datefmt="%d/%m/%Y %H:%M:%S",
    handlers=[logging.FileHandler("plex_rpc.log"), logging.StreamHandler()],
    encoding="utf-8",
    level=logging.INFO,
)


def main():
    try:
        RPC.connect()
    except Exception:
        LOGGER.info("Launching discord")
        subprocess.Popen("discord")
        time.sleep(30)
        RPC.connect()
    while True:
        try:
            current_activity = tautulli.get_my_activity()
            if current_activity is not None:
                to_send = get_corresponding_infos(current_activity=current_activity)
                if (
                    current_activity["grandparent_title"] != ""
                    and not current_activity["media_type"] == "track"
                ):
                    to_send["details"] = current_activity["grandparent_title"]

                LOGGER.info(
                    current_activity["state"].capitalize()
                    + " - "
                    + current_activity["grandparent_title"]
                    + " - "
                    + current_activity["parent_title"]
                    + " - "
                    + current_activity["title"]
                )
                RPC.update(**to_send)
            else:
                RPC.clear()
        except PyPresenceException as error:
            LOGGER.error(f"Encountered a discord error : {error}")
            LOGGER.info("Launching discord")
            subprocess.Popen("discord")
            time.sleep(30)
            RPC.connect()
        except Exception as error:
            LOGGER.error(f"Encountered an error : {error}")

        time.sleep(15)  # rich presence is limited to once per 15 seconds


def get_corresponding_infos(current_activity: dict) -> dict:
    """Returns informations corresponding to the media if it's a show/movie/song or others

    Args:
        current_activity (dict): Current activity provided by tautulli

    Returns:
        dict: Dict with the informations to send to discord RPC
    """
    # Shows
    if current_activity["media_type"] == "episode":
        to_send = dict(
            state=current_activity["parent_title"].replace("Season", "Saison")
            + " - Épisode "
            + current_activity["media_index"]
        )
        to_send["large_image"] = "show"
    # Movies
    elif current_activity["media_type"] == "movie":
        to_send = dict(details=current_activity["title"])
        to_send["state"] = "(" + current_activity["year"] + ")"
        to_send["large_image"] = "movie"
    # Musics
    elif current_activity["media_type"] == "track":
        artists = (
            current_activity["original_title"]
            if current_activity["original_title"]
            else current_activity["grandparent_title"]
        )
        if len(current_activity["title"]) > 25:
            to_send = dict(state=current_activity["title"][:25] + "... ー " + artists)
        else:
            to_send = dict(state=current_activity["title"] + " ー " + artists)
        to_send["large_image"] = "music"
        to_send["details"] = current_activity["parent_title"]
    # Others
    else:
        to_send = dict(state=current_activity["title"] + " ー " + artists)
        to_send["large_image"] = "plex"

    to_send["large_text"] = current_activity["title"][:50]
    to_send = set_progression(current_activity=current_activity, to_send=to_send)

    return to_send


def set_progression(current_activity: dict, to_send: dict) -> dict:
    """Set the duration of the media as a timestamp if playing or paused if not

    Args:
        current_activity (dict): Current activity provided by tautulli
        to_send (dict): Informations that'll be sent to discord RPC to set progression

    Returns:
        dict: Updated to_send dict with the media progression
    """
    if current_activity["state"] == "playing":
        to_send["small_image"] = "play"
        current_progress = (
            (
                int(current_activity["duration"])
                * int(current_activity["progress_percent"])
            )
            / 100
        ) / 1000
        to_send["small_text"] = "Playing"
        to_send["end"] = (
            time.time()
            + (int(current_activity["duration"]) / 1000)
            - int(current_progress)
        )
    elif current_activity["state"] == "paused":
        to_send["small_image"] = "pause"
        to_send["small_text"] = "Paused"
    return to_send


if __name__ == "__main__":
    main()
