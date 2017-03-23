import math
import random

from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Type

from bot import bot
from enums import Action, Clue, Rank, Suit, Variant
from game import Game

names: List[str] = ['Alice', 'Bob', 'Cathy', 'Donald', 'Emily']
numberWords: List[str] = ['zero', 'one', 'two', 'three', 'four', 'five']


class CardStatus(Enum):
    Deck = 0
    Hand = 1
    Play = 2
    Discard = 3


class ServerGame:
    def __init__(self,
                 variant: Variant,
                 players: int,
                 botCls: Type[bot.Bot], *,
                 print_messages: Any=False,
                 print_verbose: Any=False,
                 null_clues: Any=False,
                 seed: Any=None, **kwargs) -> None:
        if variant not in Variant:  # type: ignore
            raise ValueError('variant')
        if players < 2 or players > 5:
            raise ValueError('players')

        self.seed: Any = seed
        self.rng: random.Random = random.Random(self.seed)
        self.variant: Variant = variant
        self.printVerbose: Optional[bool] = convert_print(print_verbose)
        self.printMessages: Optional[bool]= convert_print(print_messages)
        self.allowNullClues: bool = bool(null_clues)
        self.gameLog: List[Tuple[str, dict]] = []
        self.messages: List[str] = []
        self.verbose: List[str] = []

        self.deck: List[ServerCard]
        self.initialize_deck()
        self.hands: List[List[int]] = [[] for _ in range(players)]
        self.discards: Dict[Suit, List[int]]
        self.discards = {s: [] for s in self.variant.pile_suits}
        self.plays: Dict[Suit, List[int]]
        self.plays = {s: [] for s in self.variant.pile_suits}

        self.nextDraw: int = 0
        self.turnCount: int = 0
        self.endTurn: Optional[int] = None
        self.maxScore: int = 25
        self.score: int = 0
        self.clues: int = 8
        self.strikes: int = 0
        self.loss: bool = False

        self.connections: List[ServerConnection]
        self.connections = [ServerConnection(p, self)
                            for p in range(players)]
        self.players: List[Game]
        self.players = [Game(self.connections[p], self.variant,
                             names[:players], p, botCls, **kwargs)
                        for p in range(players)]
        self.currentPlayer: int = self.rng.randrange(players)
        self.lastAction: int = (self.currentPlayer - 1) % players

    def isGameComplete(self) -> bool:
        if self.strikes == 3 or self.score >= self.maxScore:
            return True
        if self.turnCount > (self.endTurn or math.inf):
            return True
        return False

    def updateMaxScore(self) -> None:
        maxScore: int = 0
        s: Suit
        for s in self.variant.pile_suits:
            possible: int = 5
            copies: Dict[Rank, int] = {r: 0 for r in Rank}  # type: ignore
            d: int
            for d in self.discards[s]:
                card: ServerCard = self.deck[d]
                copies[card.rank] += 1
            r: Rank
            for r in reversed(Rank):  # type: ignore
                totalCopies: int = r.num_copies
                if self.variant == Variant.OneOfEach and s == Suit.Extra:
                    totalCopies += 1
                if copies[r] == totalCopies:
                    possible = r.value - 1
            maxScore += possible
        self.maxScore = maxScore

    def print(self,
              message: Optional[str]=None,
              verbose: Optional[str]=None,
              final: bool=False) -> None:
        verbose = verbose if verbose is not None else message
        if verbose is not None:
            self.verbose.append(verbose)
            if self.printVerbose:
                print(verbose)
        if message is not None:
            self.messages.append(message)
            if not self.printVerbose and self.printMessages:
                print(message)
            if final and self.printMessages is None:
                print(message)

    def run_game(self) -> None:
        self.log('game_start', {'replay': False})
        p: Game
        for p in self.players:
            self.log('init',
                     {'seat': p.botPosition,
                      'names': names[:len(self.players)],
                      'variant': self.variant.value,
                      'replay': False,
                      'spectating': False})

        handSize: int = 4 if len(self.players) > 3 else 5
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

        self.send('notify', {'type': 'game_over'})

        self.loss = self.strikes == 3
        if not self.loss:
            self.print("Players score {} points".format(self.score),
                       final=True)
        else:
            self.print("Players lost", final=True)
        self.print(verbose='')
        self.print(verbose='Number of Players: {}'.format(len(self.players)))
        self.print(verbose='Variant: {}'.format(self.variant.full_name))
        self.print(verbose='Deck Size: {}'.format(len(self.deck)))
        self.recordGameState()

    def recordGameState(self) -> None:
        deckSize: int = len(self.deck) - self.nextDraw
        lastPlayer: int = (self.currentPlayer - 1) % len(self.players)
        self.print(verbose='Deck Count: {}'.format(deckSize))
        self.print(verbose='Clue Count: {}'.format(self.clues))
        self.print(verbose='Score: {}'.format(self.score))
        self.print(verbose='Strikes: {}'.format(self.strikes))
        self.print(verbose='Max Possible Score: {}'.format(self.maxScore))
        self.print(verbose='Turn Count: {}'.format(self.turnCount))
        self.print(verbose='End Turn: {}'.format(self.endTurn))
        self.print(verbose='Next Draw Index: {}'.format(self.nextDraw))
        self.print(verbose='Last Player: {}'.format(names[lastPlayer]))
        self.print(verbose='')
        self.print(verbose='Player Hands (Newest To Oldest)')
        p: int
        hand: List[int]
        for p, hand in enumerate(self.hands):
            cards = []
            for deckIdx in reversed(hand):
                card = self.deck[deckIdx]
                cards.append('{} {}'.format(card.suit.full_name(self.variant),
                                            card.rank.value))
            self.print(verbose='{}: {}'.format(names[p], ', '.join(cards)))
        self.print(verbose='')
        self.print(verbose='Played Cards')
        s: Suit
        for s in self.variant.pile_suits:
            self.print(verbose='{}: {}'.format(s.full_name(self.variant),
                                               len(self.plays[s])))
        self.print(verbose='')
        self.print(verbose='Discarded Cards')
        for s in self.variant.pile_suits:
            discards: List[int] = []
            for deckIdx in self.discards[s]:
                card = self.deck[deckIdx]
                discards.append(card.rank.value)
            discards.sort()
            self.print(verbose='{}: {}'.format(
                s.full_name(self.variant),
                ', '.join(str(d) for d in discards)))
        self.print(verbose='')

    def log(self, type: str, resp: dict) -> None:
        self.gameLog.append((type, resp))

    def send(self,
             type: str,
             resp: dict, *,
             player: Optional[int]=None) -> None:
        if player is not None:
            p = self.players[player]
            p.received(type, resp)
        else:
            for p in self.players:
                p.received(type, resp)
            self.log(type, resp)

    def initialize_deck(self) -> None:
        self.deck = []
        index: int = 0
        s: Suit
        r: Rank
        i: int
        for s in self.variant.pile_suits:
            for r in Rank:  # type: ignore
                if not (s == Suit.Extra and self.variant == Variant.OneOfEach):
                    for i in range(r.num_copies):
                        self.deck.append(ServerCard(index, s, r, self.variant))
                        index += 1
                else:
                    self.deck.append(ServerCard(index, s, r, self.variant))
                    index += 1
        self.rng.shuffle(self.deck)
        card: ServerCard
        for i, card in enumerate(self.deck):
            card.position = i
            card.status = CardStatus.Deck

    def draw_card(self, player: int) -> None:
        if self.nextDraw >= len(self.deck):
            return
        card: ServerCard = self.deck[self.nextDraw]
        if card.status != CardStatus.Deck:
            raise GameException('Bad Card Status', card.status)
        card.player = player
        card.status = CardStatus.Hand
        p: Game
        info: dict
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
        self.print(verbose="{} draws {} {}".format(
            names[player], card.suit.full_name(self.variant), card.rank.value))

    def clue_player(self,
                    player: int,
                    target: int,
                    type: int,
                    value: int) -> None:
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
        rank: Rank
        suit: Suit
        positions: List[int]
        cards: List[int]
        card: ServerCard
        i: int
        h: int
        if type == Clue.Rank.value:
            rank = Rank(value)
            if not rank.valid():
                raise GameException('Invalid rank value', value)
            positions = []
            cards = []
            for i, h in enumerate(self.hands[target]):
                card = self.deck[h]
                if card.rank == rank:
                    positions.insert(0, len(self.hands[target]) - i)
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
            self.print(
                "{} tells {} about {} {}'s".format(
                    names[player], names[target], numberWords[len(cards)],
                    rank.value),
                "{} tells {} about {} {}'s in slots {}".format(
                    names[player], names[target], numberWords[len(cards)],
                    rank.value, ', '.join(str(p) for p in positions)))
        elif type == Clue.Suit.value:
            suit = Suit(value)
            if not suit.valid(self.variant):
                raise GameException('Invalid suit value', value)
            positions = []
            cards = []
            for i, h in enumerate(self.hands[target]):
                card = self.deck[h]
                if card.suit == suit:
                    positions.insert(0, len(self.hands[target]) - i)
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
            self.print(
                "{} tells {} about {} {}'s".format(
                    names[player], names[target], numberWords[len(cards)],
                    suit.full_name(self.variant)),
                "{} tells {} about {} {}'s in slots {}".format(
                    names[player], names[target], numberWords[len(cards)],
                    suit.full_name(self.variant),
                    ', '.join(str(p) for p in positions)))
        else:
            raise GameException('Invalid clue type', type)

    def play_card(self, player: int, deckIdx: int) -> None:
        if self.isGameComplete():
            raise GameException('Game is complete')
        if self.lastAction == player:
            raise GameException('Player already made a move', player)
        if self.currentPlayer != player:
            raise GameException('Wrong Player Turn', player)
        card: ServerCard = self.deck[deckIdx]
        if card.status != CardStatus.Hand:
            raise GameException('Bad Card Status', card.status)
        if card.player != player:
            raise GameException('Card does not belong to player', card.player)
        nextRank: int = len(self.plays[card.suit]) + 1
        position: int
        position = len(self.hands[player]) - self.hands[player].index(deckIdx)
        if card.rank.value == nextRank:
            self.plays[card.suit].append(card.position)
            self.send('notify',
                      {'type': 'played',
                       'which': {'suit': card.suit, 'rank': card.rank,
                                 'index': card.index, 'order': card.position}})
            self.score += 1
            card.status = CardStatus.Play
            self.hands[player].remove(deckIdx)
            self.print(
                "{} plays {} {}".format(
                    names[player], card.suit.full_name(self.variant),
                    card.rank.value),
                "{} plays {} {} from slot {}".format(
                    names[player], card.suit.full_name(self.variant),
                    card.rank.value, position))
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
            self.print(
                "{} fails to play {} {}".format(
                    names[player], card.suit.full_name(self.variant),
                    card.rank.value),
                "{} fails to play {} {} from slot {}".format(
                    names[player], card.suit.full_name(self.variant),
                    card.rank.value, position))
        self.draw_card(player)
        self.lastAction = player

    def discard_card(self, player: int, deckIdx: int) -> None:
        if self.isGameComplete():
            raise GameException('Game is complete')
        if self.lastAction == player:
            raise GameException('Player already made a move', player)
        if self.currentPlayer != player:
            raise GameException('Wrong Player Turn', player)
        if self.clues == 8:
            raise GameException('Cannot Discard')
        card: ServerCard = self.deck[deckIdx]
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
        position: int
        position = len(self.hands[player]) - self.hands[player].index(deckIdx)
        self.hands[player].remove(deckIdx)
        self.clues += 1
        self.print(
            "{} discards {} {}".format(
                names[player], card.suit.full_name(self.variant),
                card.rank.value),
            "{} discards {} {} from slot {}".format(
                names[player], card.suit.full_name(self.variant),
                card.rank.value, position))
        self.draw_card(player)
        self.lastAction = player


class ServerCard:
    def __init__(self,
                 index: int,
                 suit: Suit,
                 rank: Rank,
                 variant: Variant) -> None:
        self.variant:Variant = variant
        self.index: int = index
        self.position: int
        self.suit: Suit = suit
        self.rank: Rank = rank
        self.status: CardStatus
        self.player: int = None

    def __str__(self) -> str:
        return "{color} {number}".format(
            color=self.suit.full_name(self.variant),
            number=self.rank.value)


class ServerConnection:
    def __init__(self, position: int, game: ServerGame) -> None:
        self.position: int = position
        self.game: ServerGame = game

    def emit(self, *args) -> None:
        if len(args) == 2:
            type: str
            data: dict
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


def convert_print(arg: Any) -> Optional[bool]:
    if isinstance(arg, str):
        if arg.lower() in ['false', '0', '']:
            return False
        if arg.lower() in ['none']:
            return None
    return bool(arg)