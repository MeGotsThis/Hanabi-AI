from bot import bot


class Bot(bot.Bot):
    BOT_NAME = 'Human Bot'

    def decide_move(self, can_clue, can_discard):
        colorOrder = self.game.variant.pile_colors

        print('Time To Decide a Move')
        print('Can Clue: {}'.format(can_clue))
        print('Can Discard: {}'.format(can_discard))
        while True:
            print()
            print('Options:')
            print('(0) Play a card')
            print('(1) Discard a card')
            print('(2) Clue a color')
            print('(3) Clue a number')
            print('(4) Print All Hands')
            print('(5) Check clues on card in own hand')
            print('(6) Check clues on card in other hands')
            print('(7) Print played cards')
            print('(8) Print trashed cards')
            print('(9) Print score, clues, strikes, deck count')
            try:
                i = int(input('--> '))
                if i < 0 or i > 9:
                    raise ValueError()
            except ValueError:
                continue
            if i == 0:
                try:
                    print('0 is Oldest')
                    print(str(len(self.hand) - 1) + ' is Newest')
                    i = int(input('Which Card --> '))
                    if i < 0 or i >= len(self.hand):
                        raise ValueError()
                except ValueError:
                    continue
                self.play_card(i)
                break
            elif i == 1:
                if not can_discard:
                    continue
                try:
                    print('0 is Oldest')
                    print(str(len(self.hand) - 1) + ' is Newest')
                    i = int(input('Which Card --> '))
                    if i < 0 or i >= len(self.hand):
                        raise ValueError()
                except ValueError:
                    continue
                self.discard_card(i)
                break
            elif i == 2:
                if not can_clue:
                    continue
                try:
                    print('Which Player?')
                    for p in self.game.players:
                        if p == self:
                            continue
                        print('({}) {}'.format(p.position, p.name))
                    w = int(input('--> '))
                    if (w < 0 or w >= len(self.game.players)
                            or w == self.position):
                        raise ValueError()
                except ValueError:
                    continue
                try:
                    print('Which Color?')
                    for i, c in enumerate(self.game.variant.clue_colors):
                        colorName = c.full_name(self.game.variant)
                        print('({}) {}'.format(i, colorName))
                    i = int(input('--> '))
                    if i < 0 or i >= len(self.game.variant.clue_colors):
                        raise ValueError()
                except ValueError:
                    continue
                if self.can_color_clue(w, self.game.variant.clue_colors[i]):
                    self.give_color_clue(w, self.game.variant.clue_colors[i])
                    break
                else:
                    print('The clue does not mark any cards')
            elif i == 3:
                if not can_clue:
                    continue
                try:
                    print('Which Player?')
                    for p in self.game.players:
                        if p == self:
                            continue
                        print('({}) {}'.format(p.position, p.name))
                    w = int(input('--> '))
                    if (w < 0 or w >= len(self.game.players)
                            or w == self.position):
                        raise ValueError()
                except ValueError:
                    continue
                try:
                    i = int(input('Which Number (1-5) --> '))
                    if i < 1 or i > 5:
                        raise ValueError()
                except ValueError:
                    continue
                if self.can_value_clue(w, i):
                    self.give_value_clue(w, i)
                    break
                else:
                    print('The clue does not mark any cards')
                break
            elif i == 4:
                print('Player Hands (From Oldest to Newest)')
                playerOrder = ((i + self.position + 1) % self.game.numPlayers
                               for i in range(self.game.numPlayers - 1))
                for i in playerOrder:
                    player = self.game.players[i]
                    cards = []
                    for d in player.hand:
                        card = self.game.deck[d]
                        cards.append(str(card))
                    print('{}: {}'.format(player.name, ', '.join(cards)))
            elif i == 5:
                for i in range(len(self.hand)):
                    extra = ''
                    if i == 0:
                        extra = '(Oldest)'
                    if i == len(self.hand) - 1:
                        extra = '(Newest)'
                    print('Card Index ' + str(i) + ' ' + extra)
                    card = self.game.deck[self.hand[i]]
                    if card.positiveClueColors or card.positiveClueValue:
                        clues = [c.full_name(self.game.variant)
                                 for c in card.positiveClueColors]
                        if card.positiveClueValue:
                            clues.append(str(card.positiveClueValue))
                        print('POSITIVE: ' + ', '.join(c for c in clues))
                    if card.negativeClueColors or card.negativeClueValue:
                        clues = [c.full_name(self.game.variant)
                                 for c in card.negativeClueColors]
                        clues.extend(str(n) for n in card.negativeClueValue)
                        print('negative: ' + ', '.join(c for c in clues))
                    if not (card.positiveClueColors
                            or card.positiveClueValue
                            or card.negativeClueColors
                            or card.negativeClueValue):
                        print('No Clues')
                    print()
            elif i == 6:
                try:
                    print('Which Player?')
                    for p in self.game.players:
                        if p == self:
                            continue
                        print('({}) {}'.format(p.position, p.name))
                    w = int(input('--> '))
                    if (w < 0 or w >= len(self.game.players)
                            or w == self.position):
                        raise ValueError()
                except ValueError:
                    continue
                player = self.game.players[w]
                for i in range(len(player.hand)):
                    extra = ''
                    if i == 0:
                        extra = '(Oldest)'
                    if i == len(player.hand) - 1:
                        extra = '(Newest)'
                    print('Card Index ' + str(i) + ' ' + extra)
                    card = self.game.deck[player.hand[i]]
                    if card.positiveClueColors or card.positiveClueValue:
                        clues = [c.full_name(self.game.variant)
                                 for c in card.positiveClueColors]
                        if card.positiveClueValue:
                            clues.append(str(card.positiveClueValue))
                        print('POSITIVE: ' + ', '.join(c for c in clues))
                    if card.negativeClueColors or card.negativeClueValue:
                        clues = [c.full_name(self.game.variant)
                                 for c in card.negativeClueColors]
                        clues.extend(str(n) for n in card.negativeClueValue)
                        print('negative: ' + ', '.join(c for c in clues))
                    if not (card.positiveClueColors
                            or card.positiveClueValue
                            or card.negativeClueColors
                            or card.negativeClueValue):
                        print('No Clues')
                    print()
            elif i == 7:
                for c in colorOrder:
                    if self.game.playedCards[c]:
                        topCard = str(self.game.playedCards[c][-1])
                    else:
                        topCard = 'Empty'
                    colorName = c.full_name(self.game.variant)
                    print('{}: {}'.format(colorName, topCard))
            elif i == 8:
                cards = {c: [] for c in self.game.variant.pile_colors}
                for c in self.game.discards:
                    cards[c.suit].append(c.rank)
                for pile in cards.values():
                    pile.sort()
                for co in colorOrder:
                    print('{}: {}'.format(
                        co.full_name(self.game.variant),
                        ', '.join(str(c) for c in cards[co])))
            elif i == 9:
                print('Score: {}'.format(self.game.scoreCount))
                print('Clues: {}'.format(self.game.clueCount))
                print('Strikes: {}'.format(self.game.strikeCount))
                print('Deck Count: {}'.format(self.game.deckCount))
                print('Turn Count: {}'.format(self.game.turnCount))
                print('Drawn Count: {}'.format(len(self.game.deck)))

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

    def someone_got_value(self, from_, to, number, positions):
        print('Got Number Clue: From {} To {}'.format(
            self.game.players[from_].name, self.game.players[to].name))
        print('{} On positions {}'.format(
            number, ', '.join(str(p) for p in positions)))

    def got_color_clue(self, player, color, positions):
        print('Got Color Clue: From {}'.format(
            self.game.players[player].name))
        print('{} On positions {}'.format(
            color.full_name(self.game.variant),
            ', '.join(str(p) for p in positions)))

    def got_value_clue(self, player, number, positions):
        print('Got Number Clue: From {}'.format(
            self.game.players[player].name))
        print('{} On positions {}'.format(
            number, ', '.join(str(p) for p in positions)))

    def card_played(self, deckIdx, position):
        print('Played Card: {} from slot {}'.format(
            self.game.deck[deckIdx], position))

    def card_discarded(self, deckIdx, position):
        print('Discarded Card: {} from slot {}'.format(
            self.game.deck[deckIdx], position))

    def card_revealed(self, deckIdx):
        print('Revealed Card: {}'.format(self.game.deck[deckIdx]))
