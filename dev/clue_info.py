class ClueState:
    def __init__(self, turn, isCritical, hand, indexes, was_clued,
                 discard_index, worthless, *,
                 color=None, value=None,
                 play_colors=None, later_colors=None,
                 discard_color=None, discard_values=None):
        self.turn = turn
        self.critical = isCritical
        self.color = color
        self.value = value
        self.hand = hand
        self.indexes = indexes
        self.wasClued = was_clued
        self.discardIndex = discard_index
        self.worthlessDiscard = worthless
        self.playColors = play_colors
        self.laterColors = later_colors
        self.discardColors = discard_color
        self.discardValues = discard_values
