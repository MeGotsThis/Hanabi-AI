import color

NO_VARIANT = 0
BLACK_SUIT = 1
ONE_OF_EACH = 2
RAINBOW = 3


def sixth_suit(variant):
    if variant == NO_VARIANT:
        return None
    if variant == BLACK_SUIT:
        return color.BLACK
    if variant == ONE_OF_EACH:
        return color.BLACK
    if variant == RAINBOW:
        return color.RAINBOW
    return None


def str_variant(variant):
    if variant == NO_VARIANT:
        return 'None'
    if variant == BLACK_SUIT:
        return 'Black Suit'
    if variant == ONE_OF_EACH:
        return '1 of each Black'
    if variant == RAINBOW:
        return 'Rainbow'
    raise Exception()
