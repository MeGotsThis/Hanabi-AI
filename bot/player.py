class Player:
    def __init__(self, game, position, name):
        self.game = game
        self.position = position
        self.hand = []
        self.name = name

    def drew_card(self, deckIdx):
        self.hand.append(deckIdx)

    def played_card(self, deckIdx):
        self.hand.remove(deckIdx)

    def discarded_card(self, deckIdx):
        self.hand.remove(deckIdx)
