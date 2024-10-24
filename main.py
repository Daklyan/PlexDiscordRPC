import time
import logging
import subprocess
import tautulli

from config import client_id

# from pypresence import Presence
# from pypresence import PyPresenceException
from patchedPypresence.presence import Presence
from patchedPypresence.exceptions import PyPresenceException


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
    except PyPresenceException as error:
        LOGGER.error(f"Encountered a discord error : {error}")
        LOGGER.info("Launching discord")
        subprocess.Popen("discord")
        time.sleep(30)
        RPC.connect()
    precedent_activity = {}
    to_send = {}
    while True:
        try:
            current_activity = tautulli.get_my_activity()
            if current_activity is not None:
                if (
                    precedent_activity
                    and precedent_activity["file"] == current_activity["file"]
                    and precedent_activity["state"] == current_activity["state"]
                ):
                    # This works but need to improve in case the user scrubs through media
                    pass
                else:
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
                    time.sleep(15)  # rich presence is limited to once per 15 seconds
            else:
                RPC.clear()
        except Exception as error:
            LOGGER.error(f"Encountered an error : {error}")

        precedent_activity = current_activity


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
        to_send["activity_type"] = 3
    # Movies
    elif current_activity["media_type"] == "movie":
        to_send = dict(details=current_activity["title"])
        to_send["state"] = f"({current_activity['year']})"
        to_send["large_image"] = "movie"
        to_send["activity_type"] = 3
    # Musics
    elif current_activity["media_type"] == "track":
        artists = (
            current_activity["original_title"]
            if current_activity["original_title"]
            else current_activity["grandparent_title"]
        )
        to_send = dict(state=artists)
        to_send["large_image"] = "music"
        to_send["details"] = "{:<2}".format(current_activity["parent_title"])
        to_send["activity_type"] = 2
    # Others
    else:
        to_send = dict(state=current_activity["title"])
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
        duration = int(current_activity["duration"]) / 1000
        current_time = int(time.time())
        current_progress = duration * (
            float(current_activity["progress_percent"]) / 100
        )
        to_send["start"] = current_time - current_progress
        to_send["end"] = current_time + (duration - current_progress)
        to_send["small_image"] = "play"
        to_send["small_text"] = "Playing"
    elif current_activity["state"] == "paused":
        to_send["small_image"] = "pause"
        to_send["small_text"] = "Paused"
    return to_send


if __name__ == "__main__":
    main()
