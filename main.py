import traceback

import tautulli
import config
import time
from config import client_id
from pypresence import Presence
from datetime import datetime

RPC = Presence(client_id)


def main():
    RPC.connect()
    old_activity = {}
    playing_or_not = ""
    while True:
        try:
            now = datetime.now()
            time_str = now.strftime("%d/%m/%Y %Hh%Mm%Ss")
            current_activity = tautulli.get_my_activity()
            if current_activity is not None:
				# Shows
                if current_activity['media_type'] == "episode":
                    to_send = dict(state=current_activity['parent_title'].replace("Season", "Saison") + " - Épisode " +
                                         current_activity['media_index'])
                    to_send['large_image'] = "show"
                # Movies
                elif current_activity['media_type'] == "movie":
                    to_send = dict(details=current_activity['title'])
                    to_send['state'] = "(" + current_activity['year'] + ")"
                    to_send['large_image'] = "movie"
                # Musics
                elif current_activity['media_type'] == "track":
                    artists = current_activity['original_title'] if current_activity['original_title'] else current_activity['parent_title']
                    if len(current_activity['title']) > 25:
                        to_send = dict(
                            state=current_activity['title'][:25] + "... ー " + artists)
                    else:
                        to_send = dict(state= current_activity['title'] + " ー " + artists)
                    to_send['large_image'] = "music"
                    to_send['details'] = playing_or_not + current_activity['parent_title']
                # Others
                else:
                    to_send = dict(state=current_activity['title'] + " ー " + artists)
                    to_send['large_image'] = "plex"
                
                to_send['large_text'] = current_activity['title'][:50]

                

                if current_activity['state'] == "playing":
                    # playing_or_not = "▶ "
                    to_send['small_image'] = "play"
                    current_progress = (int(current_activity['duration']) * int(current_activity['progress_percent']) / 100) / 1000
                    to_send['small_text'] = "Playing"
                    to_send['end'] = time.time() + (int(current_activity['duration']) / 1000) - int(current_progress)
                elif current_activity['state'] == "paused":
                    # playing_or_not = "❚❚ "
                    to_send['small_image'] = "pause"
                    to_send['small_text'] = "Paused"

                if current_activity['grandparent_title'] != "" and not current_activity['media_type'] == "track":
                    to_send['details'] = playing_or_not + current_activity['grandparent_title']
                log_file = open("log.txt", "a")
                log_file.write(str(datetime.now()) + " : " + current_activity['state'] + " - " + current_activity['grandparent_title'] + " - " + current_activity['parent_title'] + " - " + current_activity['title'] + "\n")
                log_file.close() 
                print(to_send['end'])
                RPC.update(**to_send)
                print(time_str + " - Currently playing : " + current_activity['parent_title'] + " - " + current_activity['title'])
            else:
                RPC.clear()
        except Exception:
            print("Error here")
            error_file = open("error_log.txt", "a")
            error_file.write(time_str + " - ERROR\n")
            error_file.close()
            
        time.sleep(15)  # rich presence is limited to once per 15 seconds


if __name__ == "__main__":
    main()
