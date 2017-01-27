from enum import Enum, Flag, IntEnum


class Variant(Enum):
    NoVariant = 0
    BlackSuit = 1
    Rainbow = 2
    OneOfEach = 3

    @property
    def full_name(self):
        if self is Variant.NoVariant:
            return 'No Variant'
        if self is Variant.BlackSuit:
            return 'Black Suit'
        if self is Variant.Rainbow:
            return 'Rainbow'
        if self is Variant.OneOfEach:
            return 'One Of Each'
        return self.name

    @property
    def pile_colors(self):
        if self is Variant.NoVariant:
            return [Color.Blue, Color.Green, Color.Yellow, Color.Red,
                    Color.Purple]
        if self in [Variant.BlackSuit, Variant.OneOfEach]:
            return [Color.Blue, Color.Green, Color.Yellow, Color.Red,
                    Color.Purple, Color.Black]
        if self is Variant.Rainbow:
            return [Color.Blue, Color.Green, Color.Yellow, Color.Red,
                    Color.Purple, Color.Rainbow]
        raise ValueError

    @property
    def clue_colors(self):
        if self in [Variant.NoVariant, Variant.Rainbow]:
            return [Color.Blue, Color.Green, Color.Yellow, Color.Red,
                    Color.Purple]
        if self in [Variant.BlackSuit, Variant.OneOfEach]:
            return [Color.Blue, Color.Green, Color.Yellow, Color.Red,
                    Color.Purple, Color.Black]
        raise ValueError


class Color(Flag):
    '''
    Only for internal usage
    '''
    Blue = 0x01
    Green = 0x02
    Yellow = 0x04
    Red = 0x08
    Purple = 0x10
    Black = 0x20

    Unknown = 0x00
    Rainbow = Blue | Green | Yellow | Red | Purple | Black
    NotRainbowFlag = 0x40
    OnlyBlue = Blue | NotRainbowFlag
    OnlyGreen = Green | NotRainbowFlag
    OnlyYellow = Yellow | NotRainbowFlag
    OnlyRed = Red | NotRainbowFlag
    OnlyPurple = Purple | NotRainbowFlag
    OnlyBlack = Black | NotRainbowFlag

    @property
    def solid(self):
        return Color.NotRainbowFlag in self

    @property
    def multiColor(self):
        count = 0
        count += Color.Blue in self
        count += Color.Green in self
        count += Color.Yellow in self
        count += Color.Red in self
        count += Color.Purple in self
        count += Color.Black in self
        return count > 1

    def valid(self, variant):
        if self in [Color.Unknown, Color.NotRainbowFlag]:
            return True

        if variant == Variant.NoVariant:
            colors = [Color.Blue, Color.Green, Color.Yellow, Color.Red,
                      Color.Purple,
                      Color.OnlyBlue, Color.OnlyGreen, Color.OnlyYellow,
                      Color.OnlyRed, Color.OnlyPurple]
            return self in colors
        if variant in [Variant.BlackSuit, Variant.OneOfEach]:
            colors = [Color.Blue, Color.Green, Color.Yellow, Color.Red,
                      Color.Purple, Color.Black,
                      Color.OnlyBlue, Color.OnlyGreen, Color.OnlyYellow,
                      Color.OnlyRed, Color.OnlyPurple, Color.OnlyBlack]
            return self in colors
        if variant == Variant.Rainbow:
            if self.solid and self.multiColor:
                return False
            if Color.Black in self:
                return False
            return True
        return False

    def full_name(self, variant):
        if self is Color.Unknown:
            return 'Unknown'
        if variant == Variant.Rainbow:
            if self is Color.NotRainbowFlag:
                return 'Not-Rainbow'
            if self is Color.Rainbow:
                return 'Rainbow'
            if self.multiColor:
                return 'Mixed'
            if self is Color.Blue:
                return 'Blue'
            if self is Color.Green:
                return 'Green'
            if self is Color.Yellow:
                return 'Yellow'
            if self is Color.Red:
                return 'Red'
            if self is Color.Purple:
                return 'Purple'
            if self is Color.OnlyBlue:
                return 'Only-Blue'
            if self is Color.OnlyGreen:
                return 'Only-Green'
            if self is Color.OnlyYellow:
                return 'Only-Yellow'
            if self is Color.OnlyRed:
                return 'Only-Red'
            if self is Color.OnlyPurple:
                return 'Only-Purple'
        else:
            if Color.Blue in self:
                return 'Blue'
            if Color.Green in self:
                return 'Green'
            if Color.Yellow in self:
                return 'Yellow'
            if Color.Red in self:
                return 'Red'
            if Color.Purple in self:
                return 'Purple'
            if Color.Black in self:
                if variant in [Variant.BlackSuit, Variant.OneOfEach]:
                    return 'Black'
        raise ValueError

    def suit(self, variant):
        if self.multiColor:
            raise ValueError
        if Color.Blue in self:
            return Suit.Blue
        if Color.Green in self:
            return Suit.Green
        if Color.Yellow in self:
            return Suit.Yellow
        if Color.Red in self:
            return Suit.Red
        if Color.Purple in self:
            return Suit.Purple
        if Color.Black in self:
            if variant in [Variant.BlackSuit, Variant.OneOfEach]:
                return Suit.Extra
        raise ValueError


class Value(IntEnum):
    '''
    Only for internal usage
    '''
    V1 = 1
    V2 = 2
    V3 = 3
    V4 = 4
    V5 = 5

    @property
    def num_copies(self):
        if self is Value.V1:
            return 3
        if self is Value.V2:
            return 2
        if self is Value.V3:
            return 2
        if self is Value.V4:
            return 2
        if self is Value.V5:
            return 1
        raise ValueError

    def rank(self):
        if self is Value.V1:
            return Rank.R1
        if self is Value.V2:
            return Rank.R2
        if self is Value.V3:
            return Rank.R3
        if self is Value.V4:
            return Rank.R4
        if self is Value.V5:
            return Rank.R5
        raise ValueError


class Suit(Enum):
    '''
    Only for server reference
    '''
    Blue = 0
    Green = 1
    Yellow = 2
    Red = 3
    Purple = 4
    Extra = 5

    def color(self, variant):
        if self is Suit.Blue:
            return Color.Blue
        if self is Suit.Green:
            return Color.Green
        if self is Suit.Yellow:
            return Color.Yellow
        if self is Suit.Red:
            return Color.Red
        if self is Suit.Purple:
            return Color.Purple
        if self is Suit.Extra:
            if variant in [Variant.BlackSuit, Variant.OneOfEach]:
                return Color.Black
            if variant == Variant.Rainbow:
                return Color.Rainbow
        raise ValueError


class Rank(Enum):
    '''
    Only for server reference
    '''
    R1 = 1
    R2 = 2
    R3 = 3
    R4 = 4
    R5 = 5

    def value(self):
        if self is Rank.R1:
            return Value.V1
        if self is Rank.R2:
            return Value.V2
        if self is Rank.R3:
            return Value.V3
        if self is Rank.R4:
            return Value.V4
        if self is Rank.R5:
            return Value.V5
        raise ValueError


class Action(Enum):
    Clue = 0
    Play = 1
    Discard = 2


class Clue(Enum):
    Rank = 0
    Suit = 1

