# LongSphinx, aka Tim the Diviner

For a list of available commands, hit !readme on a running instance.

# Installation instructions: (WIP)

## Prereqs
1. Tim runs on python 3 (Tested with Python 3.5). The following instructions all assume that running "python" on your machine runs python 3. If this is not the case, replace `python` in these instructions with whatever command will run python 3.
2. Install all dependencies. From the LongSphinx root directory (the one containing 'requirements.txt'), run `python -m pip install -r requirements.txt`.

## Create a bot token
3. Go to https://discordapp.com/developers/applications/. Sign in.
4. Click "Create an application"
5. Give your application a name. To the best of my knowledge, this name does nothing. You can also upload your bot's profile picture on this page.
6. Click "Bot" in the left sidebar.
7. Click "Add Bot".
8. Give you bot a username.
9. Under "Token" click "copy". Keep this window open; you'll need another field later.

## Run your bot
10. Create a token.txt file in the LongSphinx root directory. Paste the token you just copied into it; other than that it should have nothing but a single newline at the end.
11. From the LongSphinx root directory, run `python corebot.py`.

## Add your bot to a server
12. Go back to the web browser you left open. Click "General Information".
13. Find the "Client ID" and copy it.
14. Put the client ID in the appropriate place in the following link, then put it in your address bar and hit enter:  https://discordapp.com/oauth2/authorize?client_id=INSERT_CLIENT_ID_HERE&scope=bot
15. Follow the on-screen prompts.

## Permissions
16. In the discord app, set Tim's permissions as appropriate.
    * Remember that he'll need the "manage roles" permission if you want him to manage any roles.
    * Remember also that his role will need to be higher in the list than any roles you want him to manage.
