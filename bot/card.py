from typing import List, Optional

import game

from enums import Color, Value


class Card:
    def __init__(self,
                 gameObj: 'game.Game',
                 playerObj: int,
                 deckPosition: int,
                 suit: Optional[Color],
                 rank: Optional[Value]) -> None:
        self.game: game.Game = gameObj
        self.player: int = playerObj
        self.deckPosition: int = deckPosition
        self.suit: Optional[Color] = suit
        self.rank: Optional[Value] = rank
        self.positiveClueColor: List[Color] = []
        self.negativeClueColor: List[Color] = []
        self.positiveClueValue: Optional[Value] = None
        self.negativeClueValue: List[Value] = []

    def __str__(self) -> str:
        if self.suit is None or self.rank is None:
            return "Unknown Card"
        return "{color} {number}".format(
            color=self.suit.full_name(self.game.variant),
            number=self.rank.value)

    def got_positive_color(self, color: Color) -> None:
        self.positiveClueColor.append(color)

    def got_negative_color(self, color: Color) -> None:
        self.negativeClueColor.append(color)

    def got_positive_value(self, value: Value) -> None:
        self.positiveClueValue = value

    def got_negative_value(self, value: Value) -> None:
        self.negativeClueValue.append(value)
