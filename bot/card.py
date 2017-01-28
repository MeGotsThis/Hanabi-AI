class Card:
    def __init__(self, game, player, deckPosition, suit, rank):
        self.game = game
        self.player = player
        self.deckPosition = deckPosition
        self.suit = suit
        self.rank = rank
        self.positiveClueColor = []
        self.negativeClueColor = []
        self.positiveClueValue = None
        self.negativeClueValue = []

    def __str__(self):
        if self.suit is None or self.rank is None:
            return "Unknown Card"
        return "{color} {number}".format(
            color=self.suit.full_name(self.game.variant),
            number=self.rank.value)

    def got_positive_color(self, color):
        self.positiveClueColor.append(color)

    def got_negative_color(self, color):
        self.negativeClueColor.append(color)

    def got_positive_value(self, value):
        self.positiveClueValue = value

    def got_negative_value(self, value):
        self.negativeClueValue.append(value)
