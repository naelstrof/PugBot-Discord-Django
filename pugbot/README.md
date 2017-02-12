# Discord PUG Bot

This is currently in early development and may contain bugs. Use at your
own risk.

PUG Bot for https://discordapp.com

# Requirements

* Python 3.5
* git

# Installing

```
$ pip install -r requirements.txt
```

# Hosting

Visit [Discord](https://discordapp.com/developers/applications/me) and create
new application for the bot.

Go to this [link](https://discordapp.com/developers/docs/topics/oauth2#bots)
for instructions on adding the bot to your server.

Create a `credentials.json` file with the following contents:

```json
{
  "token": "your bot token here"
}
```

# Running

```
$ python3.5 bot.py
```
