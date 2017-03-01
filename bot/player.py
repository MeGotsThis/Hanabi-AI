from typing import List

import game


class Player:
    def __init__(self, gameObj: 'game.Game', position: int, name: str) -> None:
        self.game: game.Game = gameObj
        self.position: int = position
        self.hand: List[int] = []
        self.name: int = name

    def drew_card(self, deckIdx: int) -> None:
        self.hand.append(deckIdx)

    def played_card(self, deckIdx: int) -> None:
        self.hand.remove(deckIdx)

    def discarded_card(self, deckIdx: int) -> None:
        self.hand.remove(deckIdx)
