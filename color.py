import variant

BLUE = 0x01
GREEN = 0x02
YELLOW = 0x04
RED = 0x08
PURPLE = 0x10
BLACK = 0x20
RAINBOW = 0x5F


def str_color(color):
    if color == BLUE:
        return "Blue"
    if color == GREEN:
        return "Green"
    if color == YELLOW:
        return "Yellow"
    if color == RED:
        return "Red"
    if color == PURPLE:
        return "Purple"
    if color == BLACK:
        return "Black"
    if color == RAINBOW:
        return "Rainbow"
    if color & RAINBOW:
        return "Mixed"
    raise Exception()


def clue_color(color):
    if color == BLUE:
        return 0
    if color == GREEN:
        return 1
    if color == YELLOW:
        return 2
    if color == RED:
        return 3
    if color == PURPLE:
        return 4
    if color == BLACK:
        return 5
    raise Exception()


def card_color(color, variant_):
    if color == 0:
        return BLUE
    if color == 1:
        return GREEN
    if color == 2:
        return YELLOW
    if color == 3:
        return RED
    if color == 4:
        return PURPLE
    if color == 5:
        if variant_ in [variant.BLACK_SUIT, variant.ONE_OF_EACH]:
            return BLACK
        if variant_ == variant.RAINBOW:
            return RAINBOW
    raise Exception()
