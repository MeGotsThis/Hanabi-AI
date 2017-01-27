from abc import abstractmethod

from enums import Action, Clue
from .card import Card
from .player import Player


class Bot(Player):
    BOT_NAME = 'Base Bot'

    def __init__(self, game, position, name, *, debug=False, **kwargs):
        super().__init__(game, position, name)
        self.debug = bool(debug)

    '''
    Some helper methods to create some objects
    '''
    def create_player(self, position, name):
        if position == self.position:
            return self
        return Player(self.game, position, name)

    def create_player_card(self, player, deckPosition, color, value):
        return Card(self.game, player, deckPosition, color, value)

    def create_own_card(self, deckPosition):
        return self.create_player_card(self.position, deckPosition, None, None)

    '''
    The server will make it so that decide_move is called after
    next_turn for the bot
    '''
    @abstractmethod
    def decide_move(self, can_clue, can_discard): ...

    '''
    This will be called for all players
    '''
    def next_turn(self, player): ...
    def striked(self, player): ...

    '''
    These will be called for all players except the bot
    '''
    def someone_drew(self, player, deckIdx): ...
    def someone_played(self, player, deckIdx, position): ...
    def someone_discard(self, player, deckIdx, position): ...
    def someone_got_color(self, from_, to, color, positions): ...
    def someone_got_value(self, from_, to, value, positions): ...

    '''
    These will be called for only the bot
    '''
    def got_color_clue(self, player, color, positions): ...
    def got_value_clue(self, player, value, positions): ...

    '''
    These will be called for only the bot.
    Both card_played and card_discarded are called before played_card and
    discarded_card
    '''
    def card_played(self, deckIdx, position): ...
    def card_discarded(self, deckIdx, position): ...
    def card_revealed(self, deckIdx): ...

    '''
    These are actions for the bot to take on decide_move
    Should not be overriden
    '''
    def can_color_clue(self, who, color):
        if who == self.position:
            return False
        for deckIdx in self.game.players[who].hand:
            card = self.game.deck[deckIdx]
            if card.suit & color:
                return True
        return False

    def can_value_clue(self, who, value):
        if who == self.position:
            return False
        for deckIdx in self.game.players[who].hand:
            card = self.game.deck[deckIdx]
            if card.rank == value:
                return True
        return False

    def give_color_clue(self, who, color):
        if self.debug:
            print('Sending Color Clue {color} to {who}'.format(
                color=color.full_name(self.game.variant),
                who=self.game.players[who].name))
        suit = color.suit(self.game.variant)
        self.game.send('action', {'type': Action.Clue.value, 'target': who,
                                  'clue': {'type': Clue.Suit.value,
                                           'value': suit.value}})

    def give_value_clue(self, who, value):
        if self.debug:
            print('Sending Value Clue {value} to {who}'.format(
                value=value, who=self.game.players[who].name))
        rank = value.rank()
        self.game.send('action', {'type': Action.Clue.value, 'target': who,
                                  'clue': {'type': Clue.Rank.value,
                                           'value': rank.value}})

    def play_card(self, position):
        if self.debug:
            print(
                'Sending Playing Card from slot {position}, deck index '
                '{deckIndex}'.format(
                    position=position, deckIndex=self.hand[position]))
        self.game.send('action', {'type': Action.Play.value,
                                  'target': self.hand[position]})

    def discard_card(self, position):
        if self.debug:
            print(
                'Sending Discarding Card from slot {position}, deck index '
                '{deckIndex}'.format(
                    position=position, deckIndex=self.hand[position]))
        self.game.send('action', {'type': Action.Discard.value,
                                  'target': self.hand[position]})
