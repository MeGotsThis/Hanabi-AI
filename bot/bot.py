from typing import ClassVar, List, Optional

from abc import abstractmethod

import game

from enums import Action, Clue, Color, Value
from .card import Card
from .player import Player


class Bot(Player):
    BOT_NAME: ClassVar[str] = 'Base Bot'

    def __init__(self,
                 gameObj: 'game.Game',
                 position: int,
                 name: str, *,
                 debug: bool=False, **kwargs) -> None:
        super().__init__(gameObj, position, name)
        self.debug: bool = bool(debug)

    '''
    Some helper methods to create some objects
    '''
    def create_player(self, position: int, name: str) -> Player:
        if position == self.position:
            return self
        return Player(self.game, position, name)

    def create_player_card(self,
                           player: int,
                           deckPosition: int,
                           color: Optional[Color],
                           value: Optional[Value]) -> Card:
        return Card(self.game, player, deckPosition, color, value)

    def create_own_card(self, deckPosition) -> Card:
        return self.create_player_card(self.position, deckPosition, None, None)

    '''
    The server will make it so that decide_move is called after
    next_turn for the bot
    '''
    @abstractmethod
    def decide_move(self, can_clue: bool, can_discard: bool) -> None: ...

    '''
    This will be called for all players
    '''
    def next_turn(self, player: int) -> None: ...
    def striked(self, player: int) -> None: ...
    def game_ended(self) -> None: ...

    '''
    These will be called for all players except the bot
    '''
    def someone_drew(self, player: int, deckIdx: int) -> None: ...
    def someone_played(self,
                       player: int,
                       deckIdx: int,
                       position: int) -> None: ...
    def someone_discard(self,
                        player: int,
                        deckIdx: int,
                        position: int) -> None: ...
    def someone_did_played(self,
                           player: int,
                           deckIdx: int,
                           position: int,
                           striked: bool) -> None: ...
    def someone_did_discard(self,
                            player: int,
                            deckIdx: int,
                            position: int) -> None: ...
    def someone_got_color(self,
                          from_: int,
                          to: int,
                          color: Color,
                          positions: List[int]) -> None: ...
    def someone_got_value(self,
                          from_: int,
                          to: int,
                          value: Value,
                          positions: List[int]) -> None: ...

    '''
    These will be called for only the bot
    '''
    def got_color_clue(self,
                       player: int,
                       color: Color,
                       positions: List[int]) -> None: ...
    def got_value_clue(self,
                       player: int,
                       value: Value,
                       positions: List[int]) -> None: ...

    '''
    These will be called for only the bot.
    Both card_played and card_discarded are called before played_card and
    discarded_card
    '''
    def card_played(self, deckIdx: int, position: int) -> None: ...
    def card_discarded(self, deckIdx: int, position: int) -> None: ...
    def card_did_played(self,
                        deckIdx: int,
                        position: int,
                        striked: bool) -> None: ...
    def card_did_discarded(self,
                           deckIdx: int,
                           position: int) -> None: ...
    def card_revealed(self, deckIdx: int) -> None: ...

    '''
    These are actions for the bot to take on decide_move
    Should not be overriden
    '''
    def can_color_clue(self, who: int, color: Color) -> bool:
        if who == self.position:
            return False
        for deckIdx in self.game.players[who].hand:
            card = self.game.deck[deckIdx]
            if card.suit & color:
                return True
        return False

    def can_value_clue(self, who: int, value: Value) -> bool:
        if who == self.position:
            return False
        for deckIdx in self.game.players[who].hand:
            card = self.game.deck[deckIdx]
            if card.rank == value:
                return True
        return False

    def give_color_clue(self, who: int, color: Color) -> None:
        if self.debug:
            print('Sending Color Clue {color} to {who}'.format(
                color=color.full_name(self.game.variant),
                who=self.game.players[who].name))
        suit = color.suit(self.game.variant)
        self.game.send('action', {'type': Action.Clue.value, 'target': who,
                                  'clue': {'type': Clue.Suit.value,
                                           'value': suit.value}})

    def give_value_clue(self, who: int, value: Value) -> None:
        if self.debug:
            print('Sending Value Clue {value} to {who}'.format(
                value=value, who=self.game.players[who].name))
        rank = value.rank()
        self.game.send('action', {'type': Action.Clue.value, 'target': who,
                                  'clue': {'type': Clue.Rank.value,
                                           'value': rank.value}})

    def play_card(self, position: int) -> None:
        if self.debug:
            print(
                'Sending Playing Card from slot {position}, deck index '
                '{deckIndex}'.format(
                    position=position, deckIndex=self.hand[position]))
        self.game.send('action', {'type': Action.Play.value,
                                  'target': self.hand[position]})

    def discard_card(self, position: int) -> None:
        if self.debug:
            print(
                'Sending Discarding Card from slot {position}, deck index '
                '{deckIndex}'.format(
                    position=position, deckIndex=self.hand[position]))
        self.game.send('action', {'type': Action.Discard.value,
                                  'target': self.hand[position]})
