import game

from bot import player


class Player(player.Player):
    def __init__(self, gameObj: 'game.Game', position: int, name: str) -> None:
        super().__init__(gameObj, position, name)
