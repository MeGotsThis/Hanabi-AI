import math
import random

from enum import Enum

from enums import Action, Clue, Rank, Suit, Variant
from game import Game

names = ['Alice', 'Bob', 'Cathy', 'Donald', 'Emily']
numberWords = ['zero', 'one', 'two', 'three', 'four', 'five']


class CardStatus(Enum):
    Deck = 0
    Hand = 1
    Play = 2
    Discard = 3


class ServerGame:
    def __init__(self, variant, players, botCls, *, print_messages=False,
                 null_clues=False, seed=None, **kwargs):
        if variant not in Variant:
            raise ValueError('variant')
        if players < 2 or players > 5:
            raise ValueError('players')

        self.seed = seed
        self.rng = random.Random(self.seed)
        self.variant = variant
        self.players = players
        self.printMessages = convert_print(print_messages)
        self.allowNullClues = bool(null_clues)
        self.gameLog = []
        self.messages = []

        self.initialize_deck()
        self.hands = [[] for _ in range(players)]
        self.discards = {s: [] for s in self.variant.pile_suits}
        self.plays = {s: [] for s in self.variant.pile_suits}

        self.nextDraw = 0
        self.turnCount = 0
        self.endTurn = None
        self.maxScore = 25
        self.score = 0
        self.clues = 8
        self.strikes = 0
        self.loss = False
        self.lastAction = None

        self.connections = [ServerConnection(p, self)
                            for p in range(players)]
        self.players = [Game(self.connections[p], self.variant,
                             names[:players], p, botCls, **kwargs)
                        for p in range(players)]
        self.currentPlayer = self.rng.randrange(players)

    def isGameComplete(self):
        if self.strikes == 3 or self.score == 25:
            return True
        if self.turnCount > (self.endTurn or math.inf):
            return True
        if self.score >= self.maxScore:
            return True
        return False

    def updateMaxScore(self):
        maxScore = 0
        for s in self.variant.pile_suits:
            possible = 5
            copies = {r: 0 for r in Rank}
            for d in self.discards[s]:
                card = self.deck[d]
                copies[card.rank] += 1
            for r in reversed(Rank):
                totalCopies = r.num_copies
                if self.variant == Variant.OneOfEach and s == Suit.Extra:
                    totalCopies += 1
                if copies[r] == totalCopies:
                    possible = r.value - 1
            maxScore += possible
        self.maxScore = maxScore

    def print(self, message, final=False):
        self.messages.append(message)
        if self.printMessages or (final and self.printMessages is None):
            print(message)

    def run_game(self):
        self.log('game_start', {'replay': False})
        for p in self.players:
            self.log('init',
                     {'seat': p.botPosition,
                      'names': names[:len(self.players)],
                      'variant': self.variant.value,
                      'replay': False,
                      'spectating': False})

        handSize = 4 if len(self.players) > 3 else 5
        for p in self.players:
            for _ in range(handSize):
                self.draw_card(p.botPosition)

        self.print('{} goes first'.format(names[self.currentPlayer]))

        while not self.isGameComplete():
            self.send('notify', {'type': 'status', 'clues': self.clues,
                                 'score': self.score})
            self.send('notify', {'type': 'turn', 'who': self.currentPlayer,
                                 'num': self.turnCount})
            self.send('action',
                      {'can_clue': self.clues > 0,
                       'can_discard': self.clues < 8},
                      player=self.currentPlayer)
            self.turnCount += 1
            self.currentPlayer = (self.currentPlayer + 1) % len(self.players)
            self.updateMaxScore()

        self.loss = self.strikes == 3
        if not self.loss:
            self.print("Players score {} points".format(self.score), True)
        else:
            self.print("Players lost", True)

    def log(self, type, resp):
        pass

    def send(self, type, resp, *, player=None):
        if player is not None:
            p = self.players[player]
            p.received(type, resp)
        else:
            for p in self.players:
                p.received(type, resp)
            self.log(type, resp)

    def initialize_deck(self):
        self.deck = []
        index = 0
        for s in self.variant.pile_suits:
            for r in Rank:
                if not (s == Suit.Extra and self.variant == Variant.OneOfEach):
                    for i in range(r.num_copies):
                        self.deck.append(ServerCard(index, s, r, self.variant))
                        index += 1
                else:
                    self.deck.append(ServerCard(index, s, r, self.variant))
                    index += 1
        self.rng.shuffle(self.deck)
        for i, card in enumerate(self.deck):
            card.position = i
            card.status = CardStatus.Deck

    def draw_card(self, player):
        if self.nextDraw >= len(self.deck):
            return
        card = self.deck[self.nextDraw]
        if card.status != CardStatus.Deck:
            raise GameException('Bad Card Status', card.status)
        card.player = player
        card.status = CardStatus.Hand
        for p in self.players:
            info = {'type': 'draw',
                    'who': player,
                    'order': self.nextDraw}
            if p.botPosition != player:
                info['suit'] = card.suit.value
                info['rank'] = card.rank.value
            self.send('notify', info, player=p.botPosition)
        info = {'type': 'draw',
                'who': player,
                'order': self.nextDraw,
                'suit': card.suit.value,
                'rank': card.rank.value}
        self.log('notify', info)
        self.hands[player].append(self.nextDraw)
        self.nextDraw += 1
        if self.nextDraw >= len(self.deck):
            self.endTurn = self.turnCount + len(self.players)
        self.send('notify', {'type': 'draw_size',
                             'size': len(self.deck) - self.nextDraw})

    def clue_player(self, player, target, type, value):
        if self.isGameComplete():
            raise GameException('Game is complete')
        if self.lastAction == player:
            raise GameException('Player already made a move', player)
        if self.currentPlayer != player:
            raise GameException('Wrong Player Turn', player)
        if player == target:
            raise GameException('Cannot clue self')
        if self.clues == 0:
            raise GameException('Cannot Clue')
        if target >= len(self.players):
            raise GameException('Target does not exist', target)
        if type == Clue.Rank.value:
            rank = Rank(value)
            if not rank.valid():
                raise GameException('Invalid rank value', value)
            cards = []
            for h in self.hands[target]:
                card = self.deck[h]
                if card.rank == rank:
                    cards.append(h)
            if not cards and not self.allowNullClues:
                raise GameException('No Cards Clued')
            self.send('notify',
                      {'type': 'clue',
                       'giver': player,
                       'target': target,
                       'clue': {'type': type, 'value': value},
                       'list': cards})
            self.clues -= 1
            self.lastAction = player
            self.print("{} tells {} about {} {}'s".format(
                names[player], names[target], numberWords[len(cards)],
                rank.value))
        elif type == Clue.Suit.value:
            suit = Suit(value)
            if not suit.valid(self.variant):
                raise GameException('Invalid suit value', value)
            cards = []
            for h in self.hands[target]:
                card = self.deck[h]
                if card.suit == suit:
                    cards.append(h)
                if self.variant == Variant.Rainbow and card.suit == Suit.Extra:
                    cards.append(h)
            if not cards and not self.allowNullClues:
                raise GameException('No Cards Clued')
            self.send('notify',
                      {'type': 'clue',
                       'giver': player,
                       'target': target,
                       'clue': {'type': type, 'value': value},
                       'list': cards})
            self.clues -= 1
            self.lastAction = player
            self.print("{} tells {} about {} {}'s".format(
                names[player], names[target], numberWords[len(cards)],
                suit.full_name(self.variant)))
        else:
            raise GameException('Invalid clue type', type)

    def play_card(self, player, deckIdx):
        if self.isGameComplete():
            raise GameException('Game is complete')
        if self.lastAction == player:
            raise GameException('Player already made a move', player)
        if self.currentPlayer != player:
            raise GameException('Wrong Player Turn', player)
        card = self.deck[deckIdx]
        if card.status != CardStatus.Hand:
            raise GameException('Bad Card Status', card.status)
        if card.player != player:
            raise GameException('Card does not belong to player', card.player)
        nextRank = len(self.plays[card.suit]) + 1
        if card.rank.value == nextRank:
            self.plays[card.suit].append(card.position)
            self.send('notify',
                      {'type': 'played',
                       'which': {'suit': card.suit, 'rank': card.rank,
                                 'index': card.index, 'order': card.position}})
            self.score += 1
            card.status = CardStatus.Play
            self.hands[player].remove(deckIdx)
            self.print("{} plays {} {}".format(
                names[player], card.suit.full_name(self.variant),
                card.rank.value))
        else:
            self.discards[card.suit].append(card.position)
            self.strikes += 1
            self.send('notify',
                      {'type': 'discard',
                       'which': {'suit': card.suit, 'rank': card.rank,
                                 'index': card.index, 'order': card.position}})
            self.send('notify',
                      {'type': 'strike',
                       'num': self.strikes})
            card.status = CardStatus.Discard
            self.hands[player].remove(deckIdx)
            self.print("{} fails to play {} {}".format(
                names[player], card.suit.full_name(self.variant),
                card.rank.value))
        self.draw_card(player)
        self.lastAction = player

    def discard_card(self, player, deckIdx):
        if self.isGameComplete():
            raise GameException('Game is complete')
        if self.lastAction == player:
            raise GameException('Player already made a move', player)
        if self.currentPlayer != player:
            raise GameException('Wrong Player Turn', player)
        if self.clues == 8:
            raise GameException('Cannot Discard')
        card = self.deck[deckIdx]
        if card.status != CardStatus.Hand:
            raise GameException('Bad Card Status', card.status)
        if card.player != player:
            raise GameException('Card does not belong to player', card.player)
        self.discards[card.suit].append(card.position)
        self.send('notify',
                  {'type': 'discard',
                   'which': {'suit': card.suit, 'rank': card.rank,
                             'index': card.index, 'order': card.position}})
        card.status = CardStatus.Discard
        self.hands[player].remove(deckIdx)
        self.clues += 1
        self.print("{} discards {} {}".format(
            names[player], card.suit.full_name(self.variant), card.rank.value))
        self.draw_card(player)
        self.lastAction = player


class ServerCard:
    def __init__(self, index, suit, rank, variant):
        self.variant = variant
        self.index = index
        self.position = None
        self.suit = suit
        self.rank = rank
        self.status = None
        self.player = None

    def __str__(self):
        return "{color} {number}".format(
            color=self.suit.full_name(self.variant),
            number=self.rank.value)


class ServerConnection:
    def __init__(self, position, game):
        self.position = position
        self.game = game

    def emit(self, *args):
        if len(args) == 2:
            type, data = args
            if type != 'message':
                raise GameException('emit type')
            if data['type'] != 'action':
                raise GameException('data type')
            if data['resp']['type'] == Action.Clue.value:
                self.game.clue_player(
                    self.position, data['resp']['target'],
                    data['resp']['clue']['type'],
                    data['resp']['clue']['value'])
            elif data['resp']['type'] == Action.Play.value:
                self.game.play_card(self.position, data['resp']['target'])
            elif data['resp']['type'] == Action.Discard.value:
                self.game.discard_card(self.position, data['resp']['target'])
            else:
                raise GameException('emit action type')


class GameException(Exception):
    pass


def convert_print(arg):
    if isinstance(arg, str):
        if arg.lower() in ['false', '0', '']:
            return False
        if arg.lower() in ['none']:
            return None
    return bool(arg)