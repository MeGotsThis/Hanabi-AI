import json
import unittest

from game import Game, SUIT, RANK
from color import card_color, clue_color, str_color


class GameSimulatorTesting(unittest.TestCase):
    def load_game(self, file, position, turn, botcls, **kwargs):
        self.connection = MockConnection()
        self.botcls = botcls
        self.botkwargs = kwargs
        self.position = position

        with open(file) as fp:
            self.messages = json.load(fp)

        for msg in self.messages:
            self.send_message(msg)
            if (msg['type'] == 'notify' and msg['resp']['type'] == 'turn'
                    and msg['resp']['num'] == turn):
                break

    def send_action(self):
        data = {'can_clue': self.game.clueCount > 0,
                'can_discard': self.game.clueCount < 8}
        self.message_sent('action', data)

    def send_message(self, message):
        self.message_sent(message['type'], message['resp'])

    def message_sent(self, mtype, data):
        if mtype == 'game_start':
            pass
        elif mtype == 'init':
            self.game = Game(self.connection, data['variant'], data['names'],
                             self.position, self.botcls, **self.botkwargs)
            self.bot = self.game.bot
            self.connection.game = self.game
            self.connection.bot = self.bot
        elif self.game is not None:
            self.game.received(mtype, data)
        elif mtype == 'notify' and data['type'] == 'reveal':
            pass
        elif mtype == 'action':
            pass
        else:
            print(mtype, data)
            raise Exception()


class MockConnection:
    def __init__(self):
        self.emitlog = []
        self.game = None
        self.bot = None

    def emit(self, *args):
        self.emitlog.append(args)

    def assert_clue_color(self, who, color, *, when=-1):
        emit = self.emitlog[when]
        assert emit[0] == 'message', 'Wrong Type'
        assert emit[1]['type'] == 'action', 'Wrong Type'
        assert emit[1]['resp']['type'] == 0, 'Not Cluing'
        assert emit[1]['resp']['target'] == who, 'Clued wrong person'
        assert emit[1]['resp']['clue']['type'] == SUIT,\
            'Clued a Number, not color'
        assert emit[1]['resp']['clue']['value'] == clue_color(color),\
            'Clued {}, Not {}'.format(
                str_color(card_color(emit[1]['resp']['clue']['value'],
                                     self.game.variant)), color)

    def assert_clue_value(self, who, value, *, when=-1):
        emit = self.emitlog[when]
        assert emit[0] == 'message', 'Wrong Type'
        assert emit[1]['type'] == 'action', 'Wrong Type'
        assert emit[1]['resp']['type'] == 0, 'Not Cluing'
        assert emit[1]['resp']['target'] == who, 'Clued wrong person'
        assert emit[1]['resp']['clue']['type'] == RANK,\
            'Clued a Color, not number'
        assert emit[1]['resp']['clue']['value'] == value,\
            'Clued {}, Not {}'.format(emit[1]['resp']['clue']['value'], value)

    def assert_card_played_hand(self, position, *, when=-1):
        self.assert_card_played(self.bot.hand[position], when=when)

    def assert_card_played(self, deckIdx, *, when=-1):
        emit = self.emitlog[when]
        position = 'Unknown'
        if (self.bot is not None
            and emit[1]['resp']['target'] in self.bot.hand):
            position = self.bot.hand.index(emit[1]['resp']['target'])
        assert emit[0] == 'message', 'Wrong Type'
        assert emit[1]['type'] == 'action', 'Wrong Type'
        assert emit[1]['resp']['type'] == 1, 'Not Playing'
        assert emit[1]['resp']['target'] == deckIdx,\
            'Played {}, Not {}, Position {}'.format(
                emit[1]['resp']['target'], deckIdx, position)

    def assert_card_discarded_hand(self, position, *, when=-1):
        self.assert_card_discarded(self.bot.hand[position], when=when)

    def assert_card_discarded(self, deckIdx, *, when=-1):
        emit = self.emitlog[when]
        position = 'Unknown'
        if (self.bot is not None
            and emit[1]['resp']['target'] in self.bot.hand):
            position = self.bot.hand.index(emit[1]['resp']['target'])
        assert emit[0] == 'message', 'Wrong Type'
        assert emit[1]['type'] == 'action', 'Wrong Type'
        assert emit[1]['resp']['type'] == 2, 'Not Discarding'
        assert emit[1]['resp']['target'] == deckIdx,\
            'Discarded {}, Not {}, Position {}'.format(
                emit[1]['resp']['target'], deckIdx, position)

    def assert_not_clue_color(self, who, color, *, when=-1):
        emit = self.emitlog[when]
        assert emit[0] == 'message', 'Wrong Type'
        assert emit[1]['type'] == 'action', 'Wrong Type'
        assert not (emit[1]['resp']['type'] == 0
                    and emit[1]['resp']['target'] == who
                    and emit[1]['resp']['clue']['type'] == SUIT
                    and emit[1]['resp']['clue']['value'] == clue_color(color)
                    ), 'Clued with {} to {}'.format(str_color(color), who)

    def assert_not_clue_value(self, who, value, *, when=-1):
        emit = self.emitlog[when]
        assert emit[0] == 'message', 'Wrong Type'
        assert emit[1]['type'] == 'action', 'Wrong Type'
        assert not (
            emit[1]['resp']['type'] == 0
            and emit[1]['resp']['target'] == who
            and emit[1]['resp']['clue']['type'] == RANK
            and emit[1]['resp']['clue']['value'] == value
            ), 'Clued with {} to {}'.format(emit[1]['resp']['clue']['value'],
                                            who)

    def assert_not_card_played_hand(self, position, *, when=-1):
        self.assert_card_played(self.bot.hand[position], when=when)

    def assert_not_card_played(self, deckIdx, *, when=-1):
        emit = self.emitlog[when]
        position = 'Unknown'
        if (self.bot is not None
            and emit[1]['resp']['target'] in self.bot.hand):
            position = self.bot.hand.index(emit[1]['resp']['target'])
        assert emit[0] == 'message', 'Wrong Type'
        assert emit[1]['type'] == 'action', 'Wrong Type'
        assert not (emit[1]['resp']['type'] == 1
                    and emit[1]['resp']['target'] == deckIdx
                    ), 'Played {}, Position {}'.format(
                        emit[1]['resp']['target'], position)

    def assert_not_card_discarded_hand(self, position, *, when=-1):
        self.assert_not_card_discarded(self.bot.hand[position], when=when)

    def assert_not_card_discarded(self, deckIdx, *, when=-1):
        emit = self.emitlog[when]
        position = 'Unknown'
        if (self.bot is not None
            and emit[1]['resp']['target'] in self.bot.hand):
            position = self.bot.hand.index(emit[1]['resp']['target'])
        assert emit[0] == 'message', 'Wrong Type'
        assert emit[1]['type'] == 'action', 'Wrong Type'
        assert not (emit[1]['resp']['type'] == 2
                    and emit[1]['resp']['target'] == deckIdx
                    ), 'Discarded {}, Position {}'.format(
                        emit[1]['resp']['target'], position)

    def print_action(self, *, when=-1):
        emit = self.emitlog[when]
        assert emit[0] == 'message', 'Wrong Type'
        assert emit[1]['type'] == 'action', 'Wrong Type'
        if emit[1]['resp']['type'] == 0:
            who = emit[1]['resp']['target']
            if self.game is not None:
                who = self.game.players[emit[1]['resp']['target']].name
            if emit[1]['resp']['clue']['type'] == SUIT:
                scolor = emit[1]['resp']['clue']['value']
                color = str_color(card_color(scolor, self.game.variant))
                print('Clued color {} to {}'.format(color, who))
            elif emit[1]['resp']['clue']['type'] == RANK:
                value = emit[1]['resp']['clue']['value']
                print('Clued value {} to {}'.format(value, who))
            else:
                assert False
        elif emit[1]['resp']['type'] == 1:
            position = 'Unknown'
            if (self.bot is not None
                    and emit[1]['resp']['target'] in self.bot.hand):
                position = self.bot.hand.index(emit[1]['resp']['target'])
            print('Played deckIdx {}, position {}'.format(
                emit[1]['resp']['target'], position))
        elif emit[1]['resp']['type'] == 2:
            position = 'Unknown'
            if (self.bot is not None
                    and emit[1]['resp']['target'] in self.bot.hand):
                position = self.bot.hand.index(emit[1]['resp']['target'])
            print('Discarded deckIdx {}, position {}'.format(
                emit[1]['resp']['target'], position))
        else:
            assert False
