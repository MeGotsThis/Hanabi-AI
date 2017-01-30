from bot import player


class Player(player.Player):
    def __init__(self, game, position, name):
        super().__init__(game, position, name)
