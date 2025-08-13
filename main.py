import time
import subprocess
import plex

from config import client_id
from utils import LOGGER, get_item_cover, get_artist_picture

# from pypresence import Presence
# from pypresence import PyPresenceException
from patchedPypresence.presence import Presence, Activity, StatusDisplay
from patchedPypresence.exceptions import PyPresenceException


RPC = Presence(client_id)


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
    precedent_start = 0
    to_send = {}
    while True:
        try:
            current_activity = plex.get_my_activity()
            # print(json.dumps(current_activity, indent=2))
            if current_activity is not None:
                if precedent_activity:
                    # Checking if user is scrubbing through media
                    progress_diff = abs(
                        int(current_activity["viewOffset"] / 1000) - precedent_start
                    )
                if (
                    precedent_activity
                    and precedent_activity["title"] == precedent_activity["title"]
                    and precedent_activity["Player"]["state"]
                    == current_activity["Player"]["state"]
                    and progress_diff < 10
                ):
                    # Not updating if same media or no scrubbing detected
                    pass
                else:
                    to_send = get_corresponding_infos(current_activity=current_activity)
                    if (
                        current_activity.get("grandparentTitle", "") != ""
                        and not current_activity["type"] == "track"
                    ):
                        to_send["details"] = current_activity["grandparentTitle"]

                    LOGGER.info(
                        current_activity["Player"]["state"].capitalize()
                        + " - "
                        + current_activity.get("grandparentTitle", "")
                        + " - "
                        + current_activity.get("parentTitle", "")
                        + " - "
                        + current_activity["title"]
                    )
                    RPC.update(**to_send)

                time.sleep(5)

                precedent_activity = current_activity
                precedent_start = int(current_activity["viewOffset"] / 1000)
            else:
                RPC.clear()
        except Exception as error:
            LOGGER.error(f"Encountered an error : {error}")


def get_corresponding_infos(current_activity: dict) -> dict:
    """Returns informations corresponding to the media if it's a show/movie/song or others

    Args:
        current_activity (dict): Current activity provided by tautulli

    Returns:
        dict: Dict with the informations to send to discord RPC
    """
    # Shows
    if current_activity["type"] == "episode":
        to_send = dict(
            state="S"
            + str(current_activity["parentIndex"])
            + "・E"
            + str(current_activity["index"])
            + " - "
            + current_activity["title"]
        )
        artwork = get_item_cover(
            media_name=current_activity["grandparentTitle"],
            media_type="tv",
        )
        to_send["large_image"] = artwork if artwork else "show"
        to_send["large_text"] = current_activity["grandparentTitle"][:50]
        to_send["activity_type"] = Activity.WATCHING.value
        to_send["status_display_type"] = StatusDisplay.DETAILS.value
    # Movies
    elif current_activity["type"] == "movie":
        artwork = get_item_cover(
            media_name=current_activity["title"],
            media_type="movies",
        )
        to_send = dict(details=current_activity["title"])
        to_send["state"] = f"({current_activity['year']})"
        to_send["large_image"] = artwork if artwork else "movie"
        to_send["large_text"] = current_activity["title"][:50]
        to_send["activity_type"] = Activity.WATCHING.value
        to_send["status_display_type"] = StatusDisplay.DETAILS.value
    # Musics
    elif current_activity["type"] == "track":
        artists = (
            current_activity["title"]
            if current_activity["title"]
            else current_activity["grandparentTitle"]
        )
        to_send = dict(state=artists)
        artwork = get_item_cover(
            media_name=current_activity["parentTitle"],
            media_type="music",
            media_artist=current_activity["grandparentTitle"],
        )
        to_send["large_image"] = artwork if artwork else "music"
        artist_pic_url = get_artist_picture(current_activity["grandparentTitle"])
        if artist_pic_url:
            to_send["small_image"] = artist_pic_url
            to_send["small_text"] = current_activity["grandparentTitle"]
        else:
            to_send["small_image"] = "play"
            to_send["small_text"] = "Playing"
        to_send["details"] = current_activity["title"][:50]
        to_send["large_text"] = "{:<2}".format(current_activity["parentTitle"])
        to_send["activity_type"] = Activity.LISTENING.value
        to_send["status_display_type"] = StatusDisplay.STATE.value
    # Others
    else:
        to_send = dict(state=current_activity["title"])
        to_send["large_image"] = "plex"
        to_send["activity_type"] = Activity.PLAYING.value
        to_send["status_display_type"] = StatusDisplay.NAME.value

    to_send = set_progress(current_activity=current_activity, to_send=to_send)

    return to_send


def set_progress(current_activity: dict, to_send: dict) -> dict:
    """Set the duration of the media as a timestamp if playing or paused if not

    Args:
        current_activity (dict): Current activity provided by tautulli
        to_send (dict): Informations that'll be sent to discord RPC to set progression

    Returns:
        dict: Updated to_send dict with the media progression
    """
    if current_activity["Player"]["state"] == "playing":
        duration = int(current_activity["duration"]) / 1000
        current_time = int(time.time())
        current_progress = int(current_activity["viewOffset"]) / 1000
        to_send["start"] = current_time - current_progress
        to_send["end"] = current_time + (duration - current_progress)
        # to_send["small_image"] = "play"
        # to_send["small_text"] = "Playing"
    elif current_activity["Player"]["state"] == "paused":
        to_send["small_image"] = "pause"
        to_send["small_text"] = "Paused"
    return to_send


if __name__ == "__main__":
    main()
