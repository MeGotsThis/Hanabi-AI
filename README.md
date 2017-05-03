# Hanabi

Hanabi is a cooperative card team game in which you can see everyone's hands but not your own. You can read more about the rules [here](http://pastebin.com/6brGz2J4) provided by [ExtraTricky](https://www.twitch.tv/extratricky)

# Keldon

http://keldon.net/hanabi/ is a site where groups of people meet up to play games of Hanabi. You can host your own games with friends or guests. Also spectating other games is available when the host of the game allows it. You can also see replays of your own games and other games that share the same deal. It all runs in your web browser.  
The site provide 3 other variations from the standard 5 suited decks. The possible variations are:

- No Variant: 5 suits
- Black Suit: 6 suits, the last suit is Black
- Rainbow: 6 suits, the last suit is Rainbow which can be clued with any color
- Black Suit (one of each): Same as Black Suit except the black suit has one copy of each rank

'Null' clues are not allowed on this site.

Screenshots:
![3 Player Game](https://cdn.discordapp.com/attachments/225437979085242369/270132982487056384/Screen_Shot_2017-01-15_at_1.54.40_AM.png "3 Player Rainbow Game using a Chrome extension")
![5 Player Replay](https://cdn.discordapp.com/attachments/90621118829842432/274972552646885376/unknown.png "5 Player No Variant Replay")

Actively, there are two groups who hold different conventions. You can find their discords [here](https://discord.gg/5CCr7FX) and [here](https://discord.gg/FADvkJp) and learn about their conventions. The first discord has a channel dedicated to talking about hanabi AI bots.

# AI

Unlike games such as Tic-Tac-Toe, Chess, and Go, Hanabi is a game of imperfect information. Every player is trying to achieve the same goal, get the best score (either 25 or 30 depending on the number of suits).  
Bots offered:

- Human Bot by MeGotsThis - Plays using the console interface
- Random Bot by MeGotsThis - Plays completely randomly
- AwwBot by [SliceOfBread](https://github.com/SliceOfBread/Hanabi) - Port only
- Full Tag Bot by MeGotsThis - Only No Variant
  - v1.0 - Only Plays Cards that are fully known
  - v1.5 - v1.0 but also plays all minimum playable value and single tagged cards
- Multi Tag Bot by MeGotsThis - Only No Variant
  - v1.0 - Make and consider clues of multiple color to be in order
  - v2.0 - Make critical saving clues
  - v2.1 - Make critical 2 saving clues

# Setup & Running

Requirements: 3.6, socketIO_client

There are 4 executable files and 3 configuration files

## Configuration
### bot.ini
Used wth /main.py and /create_test.py. Used to specify options for the bot as well as what bot to run on Keldon and create tests for.

### user.ini
Used with /main.py and /save_game.py. Used to tell what user to log into Keldon.

### simulator.ini
Used with /simulator.py. Used to tell what bot to run and how many game simulations to run.

## Running
### /main.py
The main executable to run on http://keldon.net/hanabi/. Can be used to create, join, rejoin games.

### /save_game.py
Save games from keldon into a json file in games folder. This will remove all names from the game to keep it anonymous. Note: the user must have played the deal (by it or others) to download the game.

### /create_test.py
Create a test suite from a game saved from /save_game.py. This is saved to game_test.py

### /simulator.py
Runs simulations of games as many as one wants. Good to run thousand games without the need of network latency or use keldon resources.
