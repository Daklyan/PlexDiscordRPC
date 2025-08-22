# Plex activity as Discord RPC

## Intro

This project makes a RPC in discord of your current activity on Plex

## Setup

To get Plex activity will need your X-Plex-Token, look at [here](https://support.plex.tv/articles/204059436-finding-an-authentication-token-x-plex-token/) if you don't know how

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
    "username" : "", <- Plex user to track by the script, if you leave it blank it will apply to any user
    "client_id" : "changeme", <- ID of the discord application
    "libraries": [], <- Plex library to track by the script, if you leave it blank it will apply to every library of the plex server
    "fanarttv_apikey": "changeme", <- API Key to get Artist illustration on fanart.tv
    "tvdb_apikey": "changeme", <- API Key to get Show/Movie illustration from tvdb
    "x_plex_token": "changeme", <- X-Plex-Token to get Plex activity
    "plex_address": "127.0.0.1",
    "plex_port": "32400"
}
```

## Discord application setup

### App creation

For discord to display your RPC you need to create an application on the dev portal (<https://discord.com/developers/applications/>)

The process is very straight forward

Just click on "New Application"
![New Application](./img/doc/create_app.png)

Add an app name, accept the ToS and click create

![Creation](./img/doc/app_name.png)

After that you'll be on your newly created app page

### Setting up the discord app

On your app page you'll find your discord app ID that you need to put in your config file for the script to work
![App id](./img/doc/app_id.png)

That's all you need for your app to be functionnal

But to make our RPC a bit prettier we're gonna add a few images on our app
![App assets](./img/doc/app_assets.png)

You can use your own images or the ones in img/plex on this repo

The important part is the naming as the code lookup by name the images

Here are the categories :

- plex (default picture)
- movie
- show
- music
- play
- pause

Here's how the assets page looks with the repo images

![Assets page filled](./img/doc/assets_page.png)

And how the RPC looks (here while listening to music for the example)

![RPC example](./img/doc/rpc_example.png)

## Launching the script manually

Just launch the main.py

```bash
python3 main.py
```

You may experience errors if you have medias with UTF-8 characters in the name for the logging

To avoid that you can run

```bash
python3 -X utf8 main.py
```

## Using docker

### Building the Docker Image

To build the Docker image, run the following command:

```bash
docker build -t plex-discord-rpc .
```

### Running Docker Compose

To run the Docker Compose setup, use the following command:

```bash
docker-compose up
```
