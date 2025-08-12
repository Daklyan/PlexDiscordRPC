import json

with open("config.json") as f:
    config = json.loads(f.read())

username = config["username"]  # if blank, any user will be reported on your profile
client_id = config["client_id"]
libraries = config["libraries"]  # set this to [] if you want to use any library
fanarttv_apikey = config["fanarttv_apikey"]
tvdb_apikey = config["tvdb_apikey"]
x_plex_token = config["x_plex_token"]
plex_address = config.get("plex_address", "localhost")
plex_port = config.get("plex_port", "32400")
