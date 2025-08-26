import time
import subprocess

from config import client_id
from socket import error as SocketError

from utils.logger import setup_logger
from utils.art import get_item_cover, get_artist_picture
from utils import plex

# from pypresence import Presence
# from pypresence import PyPresenceException
from patchedPypresence.presence import Presence, Activity, StatusDisplay
from patchedPypresence.exceptions import PyPresenceException

RPC = Presence(client_id)
LOGGER = setup_logger(__name__)


def main():
    try:
        RPC.connect()
    except PyPresenceException as error:
        LOGGER.error(f"❌ Failed to connect to Discord: {error}")
        reconnect_to_discord()
    except SocketError as error:
        if error.errno == 104:
            LOGGER.error(f"❌ Connection reset by peer: {error}")
            reconnect_to_discord()
        else:
            LOGGER.error(f"❌ Failed to connect to Discord: {error}")
            reconnect_to_discord()
    except Exception as error:
        LOGGER.error(f"❌ Got an unexpected error: {error}")
        exit(1)

    precedent_activity = {}
    precedent_start = 0
    to_send = {}

    LOGGER.info("🚀 Discord Plex RPC launched, waiting for Plex Activity...")

    while True:
        try:
            current_activity = plex.get_my_activity()
            # print(json.dumps(current_activity, indent=2))
            if current_activity:
                # Only update if there's a significant change in activity
                should_update = (
                    not precedent_activity
                    or precedent_activity["title"] != current_activity["title"]
                    or precedent_activity["Player"]["state"] != current_activity["Player"]["state"]
                    or (
                        precedent_activity
                        and abs(int(current_activity["viewOffset"] / 1000) - precedent_start) >= 15
                    )
                )

                if should_update:
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

                    # Update precedent activity
                    precedent_activity = current_activity
                    precedent_start = int(current_activity["viewOffset"] / 1000)
            else:
                RPC.clear()
                precedent_activity = {}
                precedent_start = 0

            time.sleep(5 if current_activity else 10)
        except Exception as error:
            LOGGER.error(f"Encountered an error : {error}")
        except PyPresenceException:
            reconnect_to_discord()


def reconnect_to_discord():
    """Infinite loop until connected to Discord client"""
    LOGGER.warning("⚠️ Attempting to reconnect to Discord")
    while True:
        try:
            RPC.connect()
            break
        except PyPresenceException as reconnect_error:
            LOGGER.error(f"❌ Failed to reconnect to Discord: {reconnect_error}")
        except SocketError as socker_error:
            if socker_error.errno == 104:
                LOGGER.error(f"❌ Connection reset by peer: {socker_error}")
            else:
                LOGGER.error(
                    f"❌ Got a socket error while connecting to Discord client: {socker_error}"
                )
            LOGGER.warning("⚠️ Retrying in 30 seconds")
            time.sleep(30)
        except Exception as error:
            LOGGER.error(f"❌ Unexpected error while reconnecting to Discord: {error}")
            LOGGER.warning("⚠️ Retrying in 30 seconds")
            time.sleep(30)


def get_corresponding_infos(current_activity: dict) -> dict:
    """Returns informations corresponding to the media if it's a show/movie/song or others

    Args:
        current_activity (dict): Current activity provided by Plex

    Returns:
        dict: Dict with the informations to send to discord RPC
    """
    match current_activity["type"]:
        case "episode":
            to_send = parse_episode(current_activity)
        case "movie":
            to_send = parse_movie(current_activity)
        case "track":
            to_send = parse_track(current_activity)
        case _:
            to_send = dict(state=current_activity["title"])
            to_send["large_image"] = "plex"
            to_send["activity_type"] = Activity.PLAYING.value
            to_send["status_display_type"] = StatusDisplay.NAME.value

    to_send = set_progress(current_activity=current_activity, to_send=to_send)

    return to_send


def parse_episode(current_activity: dict) -> dict:
    """Parse infos for an episode

    Args:
        current_activity (dict): Current activity provided by Plex
        to_send (dict): informations that'll be sent to discord RPC to set progression

    Returns:
        dict: Updated to_send dict with the parsed episode's info
    """
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

    return to_send


def parse_movie(current_activity: dict) -> dict:
    """Parse infos for a movie

    Args:
        current_activity (dict): Current activity provided by Plex
        to_send (dict): informations that'll be sent to discord RPC to set progression

    Returns:
        dict: Updated to_send dict with the parsed movie's info
    """
    artwork = get_item_cover(
        media_name=current_activity["title"],
        media_type="movies",
        year=current_activity["year"],
    )

    to_send = dict(details=current_activity["title"])
    to_send["state"] = current_activity["year"]
    to_send["large_image"] = artwork if artwork else "movie"
    to_send["large_text"] = current_activity["title"][:50]
    to_send["activity_type"] = Activity.WATCHING.value
    to_send["status_display_type"] = StatusDisplay.DETAILS.value

    return to_send


def parse_track(current_activity: dict) -> dict:
    """Parse infos for a track
    Args:
        current_activity (dict): Current activity provided by Plex
        to_send (dict): informations that'll be sent to discord RPC to set progression

    Returns:
        dict: Updated to_send dict with the parsed track's info
    """
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

    return to_send


def set_progress(current_activity: dict, to_send: dict) -> dict:
    """Set the duration of the media as a timestamp if playing or paused if not

    Args:
        current_activity (dict): Current activity provided by Plex
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
