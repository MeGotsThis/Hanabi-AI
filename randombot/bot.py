import random

from bot import bot
from enums import Value

PLAY = 0
DISCARD = 1
CLUE_COLOR = 2
CLUE_VALUE = 3


class Bot(bot.Bot):
    '''
    This Bot will only do random actions from playing, cluing, discarding
    if possible
    '''
    BOT_NAME = 'Random Bot'

    def decide_move(self, can_clue, can_discard):
        actions = [PLAY]
        if can_clue:
            actions.append(CLUE_COLOR)
            actions.append(CLUE_VALUE)
        if can_discard:
            actions.append(DISCARD)

        while True:
            action = random.choice(actions)
            if action == PLAY:
                self.play_card(random.randrange(len(self.hand)))
                break
            elif action == DISCARD:
                self.discard_card(random.randrange(len(self.hand)))
                break
            elif action == CLUE_COLOR:
                options = []
                for p in range(self.game.numPlayers):
                    for c in self.game.variant.clue_colors:
                        if self.can_color_clue(p, c):
                            options.append((p, c))
                if options:
                    player, color = random.choice(options)
                    self.give_color_clue(player, color)
                    break
            elif action == CLUE_VALUE:
                options = []
                for p in range(self.game.numPlayers):
                    for v in Value:
                        if self.can_value_clue(p, v):
                            options.append((p, v))
                if options:
                    player, value = random.choice(options)
                    self.give_value_clue(player, value)
                    break
                break

    def next_turn(self, player):
        print('Current Turn: {}'.format(self.game.players[player].name))

    def striked(self, player):
        print('Striked: {}'.format(self.game.players[player].name))
        print('Strike Count: {}'.format(self.game.strikeCount))

    def someone_drew(self, player, deckIdx):
        print('Drew Card: {} {}'.format(self.game.players[player].name,
                                        self.game.deck[deckIdx]))

    def someone_played(self, player, deckIdx, position):
        print('Played Card: {} {} from slot {}'.format(
            self.game.players[player].name, self.game.deck[deckIdx], position))

    def someone_discard(self, player, deckIdx, position):
        print('Discarded Card: {} {} from slot {}'.format(
            self.game.players[player].name, self.game.deck[deckIdx], position))

    def someone_got_color(self, from_, to, color, positions):
        print('Got Color Clue: From {} To {}'.format(
            self.game.players[from_].name, self.game.players[to].name))
        print('{} On positions {}'.format(
            color.full_name(self.game.variant),
            ', '.join(str(p) for p in positions)))

    def someone_got_value(self, from_, to, value, positions):
        print('Got Number Clue: From {} To {}'.format(
            self.game.players[from_].name, self.game.players[to].name))
        print('{} On positions {}'.format(
            value.value, ', '.join(str(p) for p in positions)))

    def got_color_clue(self, player, color, positions):
        print('Got Color Clue: From {}'.format(
            self.game.players[player].name))
        print('{} On positions {}'.format(
            color.full_name(self.game.variant),
            ', '.join(str(p) for p in positions)))

    def got_value_clue(self, player, value, positions):
        print('Got Number Clue: From {}'.format(
            self.game.players[player].name))
        print('{} On positions {}'.format(
            value.value, ', '.join(str(p) for p in positions)))

    def card_played(self, deckIdx, position):
        print('Played Card: {} from slot {}'.format(
            self.game.deck[deckIdx], position))

    def card_discarded(self, deckIdx, position):
        print('Discarded Card: {} from slot {}'.format(
            self.game.deck[deckIdx], position))

    def card_revealed(self, deckIdx):
        print('Revealed Card: {}'.format(self.game.deck[deckIdx]))
