import json
import unittest

from game import Game
from enums import Action, Clue, Rank, Suit, Variant


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
            self.game = Game(self.connection, Variant(data['variant']),
                             data['names'], self.position, self.botcls,
                             **self.botkwargs)
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
        suit = color.suit(self.game.variant)
        assert emit[0] == 'message', 'Wrong Type'
        assert emit[1]['type'] == 'action', 'Wrong Type'
        assert emit[1]['resp']['type'] == Action.Clue.value, 'Not Cluing'
        assert emit[1]['resp']['target'] == who, 'Clued wrong person'
        assert emit[1]['resp']['clue']['type'] == Clue.Suit.value,\
            'Clued a Number, not color'
        assert emit[1]['resp']['clue']['value'] == suit.value,\
            'Clued {}, Not {}'.format(
                Suit(emit[1]['resp']['clue']['value']).name,
                color.full_name(self.game.variant))

    def assert_clue_value(self, who, value, *, when=-1):
        emit = self.emitlog[when]
        assert emit[0] == 'message', 'Wrong Type'
        assert emit[1]['type'] == 'action', 'Wrong Type'
        assert emit[1]['resp']['type'] == Action.Clue.value, 'Not Cluing'
        assert emit[1]['resp']['target'] == who, 'Clued wrong person'
        assert emit[1]['resp']['clue']['type'] == Clue.Rank.value,\
            'Clued a Color, not number'
        assert emit[1]['resp']['clue']['value'] == value.rank().value,\
            'Clued {}, Not {}'.format(emit[1]['resp']['clue']['value'],
                                      value.value)

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
        assert emit[1]['resp']['type'] == Action.Play.value, 'Not Playing'
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
        assert emit[1]['resp']['type'] == Action.Discard.value, 'Not Discarding'
        assert emit[1]['resp']['target'] == deckIdx,\
            'Discarded {}, Not {}, Position {}'.format(
                emit[1]['resp']['target'], deckIdx, position)

    def assert_not_clue_color(self, who, color, *, when=-1):
        emit = self.emitlog[when]
        suit = color.suit(self.game.variant)
        assert emit[0] == 'message', 'Wrong Type'
        assert emit[1]['type'] == 'action', 'Wrong Type'
        assert not (emit[1]['resp']['type'] == Action.Clue.value
                    and emit[1]['resp']['target'] == who
                    and emit[1]['resp']['clue']['type'] == Clue.Suit.value
                    and emit[1]['resp']['clue']['value'] == suit.value
                    ), 'Clued with {} to {}'.format(
                        color.full_name(self.game.variant), who)

    def assert_not_clue_value(self, who, value, *, when=-1):
        emit = self.emitlog[when]
        assert emit[0] == 'message', 'Wrong Type'
        assert emit[1]['type'] == 'action', 'Wrong Type'
        assert not (
            emit[1]['resp']['type'] == Action.Clue.value
            and emit[1]['resp']['target'] == who
            and emit[1]['resp']['clue']['type'] == Clue.Rank.value
            and emit[1]['resp']['clue']['value'] == value.rank().value
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
        assert not (emit[1]['resp']['type'] == Action.Play.value
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
        assert not (emit[1]['resp']['type'] == Action.Discard.value
                    and emit[1]['resp']['target'] == deckIdx
                    ), 'Discarded {}, Position {}'.format(
                        emit[1]['resp']['target'], position)

    def print_action(self, *, when=-1):
        emit = self.emitlog[when]
        assert emit[0] == 'message', 'Wrong Type'
        assert emit[1]['type'] == 'action', 'Wrong Type'
        if emit[1]['resp']['type'] == Action.Clue.value:
            who = emit[1]['resp']['target']
            if self.game is not None:
                who = self.game.players[emit[1]['resp']['target']].name
            if emit[1]['resp']['clue']['type'] == Clue.Suit.value:
                scolor = emit[1]['resp']['clue']['value']
                color = Suit(scolor)
                print('Clued color {} to {}'.format(color.name, who))
            elif emit[1]['resp']['clue']['type'] == Clue.Rank.value:
                value = emit[1]['resp']['clue']['value']
                print('Clued value {} to {}'.format(value, who))
            else:
                assert False
        elif emit[1]['resp']['type'] == Action.Play.value:
            position = 'Unknown'
            if (self.bot is not None
                    and emit[1]['resp']['target'] in self.bot.hand):
                position = self.bot.hand.index(emit[1]['resp']['target'])
            print('Played deckIdx {}, position {}'.format(
                emit[1]['resp']['target'], position))
        elif emit[1]['resp']['type'] == Action.Discard.value:
            position = 'Unknown'
            if (self.bot is not None
                    and emit[1]['resp']['target'] in self.bot.hand):
                position = self.bot.hand.index(emit[1]['resp']['target'])
            print('Discarded deckIdx {}, position {}'.format(
                emit[1]['resp']['target'], position))
        else:
            assert False
