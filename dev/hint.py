from typing import Optional

from enums import Color, Value


class Hint:
    def __init__(self, *,
                 fitness: int=0,
                 to: int=-1,
                 color: Optional[Color]=None,
                 value: Optional[Value]=None):
        self.fitness: int = fitness
        self.to: int = to
        self.color: Optional[Color] = color
        self.value: Optional[Value] = value

    def give(self, bot):
        assert self.to != -1
        assert self.to != bot.position
        assert (self.color is not None) != (self.value is not None)

        if self.color is not None:
            bot.give_color_clue(self.to, self.color)
        elif self.value is not None:
            bot.give_value_clue(self.to, self.value)
        else:
            assert False

    def __str__(self):
        return '''\
Fitness: {fitness}, To: {to}, Color: {color}, Value: {value}'''.format(
            fitness=self.fitness, to=self.to,
            color=self.color, value=self.value)

    def __repr__(self):
        args = []
        if self.fitness != 0:
            args.append('fitness=' + repr(self.fitness))
        if self.to is not None:
            args.append('to=' + repr(self.to))
        if self.color is not None:
            args.append('color=' + repr(self.color))
        if self.value is not None:
            args.append('value=' + repr(self.value))
        return 'Hint(' + ', '.join(args) + ')'

    def __eq__(self, other):
        if not isinstance(other, Hint):
            return False
        return (self.fitness == other.fitness
                and self.to == other.to
                and self.color == other.to
                and self.value == other.value)
