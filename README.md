## Intro

This project makes a RPC in discord of your current activity on plex via Tautulli

## Setup

Install required packages

```bash
pip install -r requirements.txt
```

Copy the config example and update the value

```bash
cp config.example.json config.json
```

```json
{
    "apikey": "changeme", <- This is your Tautulli api key (found in Settings -> Web Interface)
    "host" : "127.0.0.1:8181", <- This the IP / domain to access Tautulli, leave it as is if Tautulli run on the same computer as the script
    "username" : "", <- Plex user to track by the script, if you leave it blank it will apply to any user
    "client_id" : "changeme", <- ID of the discord application (create one on https://discord.com/developers/applications/)
    "libraries": [], <- Plex library to track by the script, if you leave it blank it will apply to every library of the plex server
    "excluded_devices": [] <- List of devices to be ignored by the script, you can leave it blank if not needed
}
```

## Discord application settings

TODO
