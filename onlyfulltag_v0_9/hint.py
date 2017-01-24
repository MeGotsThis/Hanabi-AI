class Hint:
    def __init__(self):
        self.fitness = 0
        self.to = 0
        self.color = None
        self.value = None

    def give(self, bot):
        if self.color is not None:
            bot.give_color_clue(self.to, self.color)
        elif self.value is not None:
            bot.give_value_clue(self.to, self.value)
        else:
            assert False
