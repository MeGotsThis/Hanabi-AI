import configparser
import json

from enums import Clue

colors = ['Color.Blue', 'Color.Green', 'Color.Yellow', 'Color.Red',
          'Color.Purple', 'Color.Black']

config = configparser.ConfigParser()
config.read('bot.ini')

bot = config['BOT']['bot']

script = '''\
from enums import Color
from testing.game_testing import GameSimulatorTesting
from ''' + bot + '''.bot import Bot


class Game(GameSimulatorTesting):
'''

print('Which game file?')
gameFile = input('--> ')

with open(gameFile) as fp:
    messages = json.load(fp)

print('Which position?')
p = input('--> ')
position = int(p) if p else None

names = []
currentTurn = None
currentPosition = None
deckSize = None
clues = 8
score = 0
hand = []
for msg in messages:
    data = msg['resp']
    if msg['type'] == 'init':
        if position is None:
            position = data['seat']
        if position >= len(data['names']):
            raise Exception('Not enough players')
        names = data['names']
    elif msg['type'] == 'notify':
        if data['type'] == 'turn':
            currentTurn = data['num']
            currentPosition = data['who']
        elif data['type'] == 'draw_size':
            deckSize = data['size']
        elif data['type'] == 'status':
            clues = data['clues']
            score = data['score']
        elif data['type'] == 'draw':
            if data['who'] == position:
                hand.append(data['order'])

        if currentPosition == position:
            if data['type'] == 'clue':
                if data['clue']['type'] == Clue.Suit.value:
                    script += '''\
    def test_turn_''' + str(currentTurn) + '''(self):
        # Deck size ''' + str(deckSize) + ''', ''' + names[position] + ''', \
Clues ''' + str(clues) + ''', Score ''' + str(score) + """
        self.load_game(r'""" + gameFile + """', position=""" + str(position)\
+ ''', turn=''' + str(currentTurn) + ''', botcls=Bot)
        self.send_action()
        self.connection.assert_clue_color\
(''' + str(data['target']) + ''', ''' + colors[data['clue']['value']] + ''')

'''
                elif data['clue']['type'] == Clue.Rank.value:
                    script += '''\
    def test_turn_''' + str(currentTurn) + '''(self):
        # Deck size ''' + str(deckSize) + ''', ''' + names[position] + ''', \
Clues ''' + str(clues) + ''', Score ''' + str(score) + """
        self.load_game(r'""" + gameFile + """', position=""" + str(position)\
+ ''', turn=''' + str(currentTurn) + ''', botcls=Bot)
        self.send_action()
        self.connection.assert_clue_value\
(''' + str(data['target']) + ''', ''' + str(data['clue']['value']) + ''')

'''
            elif data['type'] == 'played':
                idx = hand.index(data['which']['order'])
                hand.remove(data['which']['order'])
                script += '''\
    def test_turn_''' + str(currentTurn) + '''(self):
        # Deck size ''' + str(deckSize) + ''', ''' + names[position] + ''', \
Clues ''' + str(clues) + ''', Score ''' + str(score) + """
        self.load_game(r'""" + gameFile + """', position=""" + str(position)\
+ ''', turn=''' + str(currentTurn) + ''', botcls=Bot)
        self.send_action()
        self.connection.assert_card_played_hand(''' + str(idx) + ''')

'''
            elif data['type'] == 'discard':
                idx = hand.index(data['which']['order'])
                hand.remove(data['which']['order'])
                script += '''\
    def test_turn_''' + str(currentTurn) + '''(self):
        # Deck size ''' + str(deckSize) + ''', ''' + names[position] + ''', \
Clues ''' + str(clues) + ''', Score ''' + str(score) + """
        self.load_game(r'""" + gameFile + """', position=""" + str(position)\
+ ''', turn=''' + str(currentTurn) + ''', botcls=Bot)
        self.send_action()
        self.connection.assert_card_discarded_hand(''' + str(idx) + ''')

'''

with open('game_test.py', 'w') as fp:
    fp.write(script)
