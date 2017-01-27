import time

from bot import bot
from enums import Value, Variant
from .card_knowledge import CardKnowledge
from .hint import Hint


class Bot(bot.Bot):
    '''
    Modified from AwwBot
    '''
    BOT_NAME = 'Full Tag Bot v0.9'

    def __init__(self, game, position, name, **kwargs):
        if game.variant != Variant.NoVariant:
            raise ValueError()

        super().__init__(game, position, name, **kwargs)
        self.colors = list(game.variant.pile_colors)
        self.values = list(Value)

        '''
        Next value for the color
        '''
        self.nextPlayValue = {c: 0 * 6 for c in self.colors}
        '''
        Max possible value for the color
        '''
        self.maxPlayValue = {c: 0 * 6 for c in self.colors}
        '''
        Pile Complete
        '''
        self.colorComplete = {c: 0 * 6 for c in self.colors}
        '''
        What cards have been played/discarded so far?
        '''
        self.playedCount = {c: [0] * 6 for c in self.colors}
        '''
        What cards have been discarded so far?
        '''
        self.discardCount = {c: [0] * 6 for c in self.colors}
        '''
        What cards in players' hands are definitely identified?
        This table is recomputed every turn.
        '''
        self.locatedCount = {c: [0] * 6 for c in self.colors}
        '''
        What cards are tagged in players' hands?
        This table is recomputed every turn.
        '''
        self.taggedCount = {c: [0] * 6 for c in self.colors}
        '''
        What cards in players' hands are visible to me in particular?
        This table is recomputed every turn.
        '''
        self.eyesightCount = {c: [0] * 6 for c in self.colors}
        '''
        What is the lowest-value card currently playable?
        This value is recomputed every turn.
        '''
        self.lowestPlayableValue = 0

    def create_player_card(self, player, deckPosition, color, value):
        return CardKnowledge(self, player, deckPosition, color, value)

    def next_turn(self, player):
        self.pleaseObserveBeforeMove()

    def someone_discard(self, player, deckIdx, position):
        self.pleaseObserveBeforeDiscard(player, position, deckIdx)

    def card_discarded(self, deckIdx, position):
        self.pleaseObserveBeforeDiscard(self.position, position, deckIdx)

    def someone_played(self, player, deckIdx, position):
        self.pleaseObserveBeforePlay(player, position, deckIdx)

    def card_played(self, deckIdx, position):
        self.pleaseObserveBeforePlay(self.position, position, deckIdx)

    def someone_got_color(self, from_, to, color, positions):
        self.pleaseObserveColorHint(from_, to, color, positions)

    def got_color_clue(self, player, color, positions):
        self.pleaseObserveColorHint(player, self.position, color, positions)

    def someone_got_value(self, from_, to, value, positions):
        self.pleaseObserveValueHint(from_, to, value, positions)

    def got_value_clue(self, player, value, positions):
        self.pleaseObserveValueHint(player, self.position, value, positions)

    def decide_move(self, can_clue, can_discard):
        time.sleep(1)
        self.pleaseMakeMove(can_discard)

    def isNowPlayable(self, color, value):
        assert color is not None or value is not None
        if color is not None and value is not None:
            return self.isPlayable(color, value)
        if color is not None:
            playableValue = len(self.game.playedCards[color]) + 1
            if (playableValue <= 5
                    and not self.taggedCount[color][playableValue]):
                return True
            return False
        if value is not None:
            for c in self.colors:
                if (len(self.game.playedCards[c]) + 1 == value
                        and not self.taggedCount[c][value]):
                    return True
            return False

    def possibleValuesInHand(self, color):
        assert color is not None
        values = []
        for v in self.values[len(self.game.playedCards[color]):]:
            if self.taggedCount[color][v]:
                continue
            if self.locatedCount[color][v]:
                continue
            if self.eyesightCount[color][v] == v.num_copies:
                continue
            values.append(v)
        return values

    def possibleColorsInHand(self, value):
        assert value is not None
        colors_ = []
        for c in self.colors:
            if self.taggedCount[c][value]:
                continue
            if self.locatedCount[c][value]:
                continue
            if self.eyesightCount[c][value] == value.num_copies:
                continue
            colors_.append(c)
        return colors_

    def isPlayable(self, color, value):
        playableValue = len(self.game.playedCards[color]) + 1
        return value == playableValue

    def isValuable(self, color, value):
        if self.playedCount[color][value] != value.num_copies - 1:
            return False
        return not self.isWorthless(color, value)

    def isWorthless(self, color, value):
        playableValue = len(self.game.playedCards[color]) + 1
        if value < playableValue:
            return True
        while(value > playableValue):
            value = Value(value - 1)
            if self.playedCount[color][value] == value.num_copies:
                return True
        return False

    def isUseful(self, color, value):
        if self.isWorthless(color, value):
            return False
        playableValue = len(self.game.playedCards[color]) + 1
        return value >= playableValue

    def updateEyesightCount(self):
        self.eyesightCount = {c: [0] * 6 for c in self.colors}
        for p in self.game.players:
            for c in p.hand:
                card = self.game.deck[c]
                if card.suit is not None and card.rank is not None:
                    self.eyesightCount[card.suit][card.rank] += 1
                elif card.color is not None and card.value is not None:
                    self.eyesightCount[card.color][card.value] += 1

    def updateLocatedCount(self):
        newCount = {c: [0] * 6 for c in self.colors}
        for p in self.game.players:
            for c in p.hand:
                card = self.game.deck[c]
                if card.color is not None and card.value is not None:
                    newCount[card.color][card.value] += 1

        if newCount != self.locatedCount:
            self.locatedCount = newCount
            return True
        return False

    def updateDiscardCount(self):
        self.discardCount = {c: [0] * 6 for c in self.colors}
        for c in self.game.discards:
            card = self.game.deck[c]
            self.discardCount[card.suit][card.rank] += 1

    def updateColorValueTables(self):
        for c in self.colors:
            self.nextPlayValue[c] = len(self.game.playedCards[c]) + 1
            self.maxPlayValue[c] = 0
            for v in self.values:
                if self.discardCount[c][v] == v.num_copies:
                    score = len(self.game.playedCards[c])
                    self.maxPlayValue[c] = v - 1
                    self.colorComplete[c] = v - 1 == score
                    break

    def seePublicCard(self, color, value):
        self.playedCount[color][value] += 1
        assert 1 <= self.playedCount[color][value] <= value.num_copies

    def nextPlayDiscardIndex(self, player):
        play_index = None
        discard_index = None
        worthless = False
        for c in range(len(self.game.players[player].hand)):
            card = self.game.deck[self.game.players[player].hand[c]]
            if card.playable is True:
                if card.playable:
                    # Play newest
                    play_index = c
                continue
            if card.worthless is True:
                # Discard worthless newest
                discard_index = c
                worthless = True
                continue
            if card.valuable is True:
                # Hold card
                continue

            if discard_index is None and not card.clued and not worthless:
                discard_index = c
        return play_index, discard_index, worthless

    def isCluedElsewhere(self, player, hand):
        returnVal = False
        handcard = self.game.deck[self.game.players[player].hand[hand]]
        color = handcard.suit
        value = handcard.rank
        for p in self.game.players:
            for c in p.hand:
                card = self.game.deck[c]
                if card.deckPosition == handcard.deckPosition:
                    continue
                if p is self:
                    if card.mustBeColor(color):
                        if card.mustBeValue(value):
                            return True
                        if card.cannotBeValue(value) and card.clued:
                            returnVal = None
                    elif card.mustBeValue(value):
                        if card.cannotBeColor(color) and card.clued:
                            returnVal = None
                else:
                    if (card.clued
                            and card.suit == color
                            and card.rank == value):
                        return True
                    elif card.color == color and card.value == value:
                        return True
        return returnVal

    def noValuableWarningWasGiven(self, from_):
        '''
        Awwbot:
        Something just happened that wasn't a warning. If what happened
        wasn't a hint to the guy expecting a warning, then he can safely
        deduce that his card isn't valuable enough to warn about.
        '''
        if self.game.deckCount == 0:
            return
        if self.game.clueCount == 0:
            return

        playerExpectingWarning = (from_ + 1) % self.game.numPlayers
        pi, di, wl = self.nextPlayDiscardIndex(playerExpectingWarning)
        player = self.game.players[playerExpectingWarning]
        card = self.game.deck[player.hand[di]]
        card.setIsValuable(False)

    def possibleDoubleDiscard(self):
        if self.game.numPlayers < 3:
            # Only valid with 3 or more players
            return False

        lh1 = (self.position + 1) % self.game.numPlayers
        lh2 = (self.position + 2) % self.game.numPlayers

        play1, discard1, worthless1 = self.nextPlayDiscardIndex(lh1)
        play2, discard2, worthless2 = self.nextPlayDiscardIndex(lh2)

        if worthless1 or worthless2:
            return False

        if play1 is not None or play2 is not None:
            return False

        if discard1 is None or discard2 is None:
            # Either player has no valid discards aka a full hand
            return None

        card1 = self.game.deck[self.game.players[lh1].hand[discard1]]
        card2 = self.game.deck[self.game.players[lh1].hand[discard2]]

        return card1.suit == card2.suit and card1.rank == card2.rank

    def bestHintForPlayer(self, distance):
        assert distance != 0
        player = (self.position + distance) % self.game.numPlayers
        hand = self.game.players[player].hand

        needToTag = {c: 0 for c in self.colors}
        for c in self.colors:
            nextValue = len(self.game.playedCards[c]) + 1
            while nextValue < 6:
                if not self.locatedCount[c][nextValue]:
                    needToTag[c] = nextValue
                    break
                nextValue += 1

        awayFromPlayable = [-10] * len(hand)
        awayFromTaggable = [-10] * len(hand)
        for i in range(len(hand)):
            card = self.game.deck[hand[i]]
            nextValue = len(self.game.playedCards[card.suit]) + 1
            awayFromPlayable[i] = nextValue - card.rank
            awayFromTaggable[i] = needToTag[card.suit] - card.rank

        play, discard, worthless = self.nextPlayDiscardIndex(player)

        best_so_far = Hint()
        best_so_far.to = player
        for c in self.colors:
            tagged = []
            clued = []
            needClarify = 0
            otherUseful = 0
            useless = 0
            numProtect = 0
            numNewTagged = 0
            nowPlayable = 0
            for i in range(len(hand)):
                card = self.game.deck[hand[i]]
                if card.suit & c:
                    if card.color is None:
                        numNewTagged += 1
                    if self.isNowPlayable(c, card.rank):
                        nowPlayable += 1
                    if card.value is not None:
                        needClarify += 1
                    else:
                        if not self.isUseful(c, card.rank):
                            useless += 1
                        elif card.color is None:
                            otherUseful += 1
                            if self.isValuable(c, card.rank):
                                numProtect += 1
                    tagged.append(i)
                if card.clued:
                    clued.append(i)
            if not tagged:
                continue

            colorFitness = 0

            # Decision Here
            if numNewTagged >= 1 and nowPlayable >= 1:
                colorFitness = (needClarify * 10 + otherUseful - useless
                                + numProtect * 5)

            if colorFitness > best_so_far.fitness:
                best_so_far.fitness = colorFitness
                best_so_far.color = c
                best_so_far.value = None

        for v in self.values:
            tagged = []
            clued = []
            numNewTagged = 0
            nowPlayable = 0
            numRepeat = 0
            for i in range(len(hand)):
                card = self.game.deck[hand[i]]
                if card.rank == v:
                    if card.value is None:
                        numNewTagged += 1
                    if self.isNowPlayable(card.suit, v):
                        nowPlayable += 1
                    if self.isCluedElsewhere(player, i):
                        numRepeat += 1
                    for t in tagged:
                        tcard = self.game.deck[hand[t]]
                        if tcard.suit == card.suit:
                            numRepeat += 1
                    tagged.append(i)

                if card.clued:
                    clued.append(i)
            if not tagged:
                continue

            valueFitness = 0

            # Decision Here
            if v < self.lowestPlayableValue:
                pass
            else:
                baseValue = 15 if v == Value.V5 else 10
                if numNewTagged >= 1 and nowPlayable >= 1:
                    valueFitness = ((nowPlayable + numNewTagged) * baseValue
                                    - numRepeat)

            if valueFitness > best_so_far.fitness:
                best_so_far.fitness = valueFitness
                best_so_far.color = None
                best_so_far.value = v

        if best_so_far.fitness == 0:
            return None
        return best_so_far

    def bestCardToPlay(self):
        for i in range(len(self.hand) - 1, -1, -1):
            card = self.game.deck[self.hand[i]]
            if card.playable:
                return i
        return None

    def maybePlayCard(self):
        best_index = self.bestCardToPlay()
        if best_index is not None:
            self.play_card(best_index)
            return True
        return False

    def maybeGiveHelpfulHint(self):
        if self.game.clueCount == 0:
            return False

        bestHint = Hint()
        for i in range(1, self.game.numPlayers):
            player = (self.position + i) % self.game.numPlayers
            candidate = self.bestHintForPlayer(i)
            if candidate is not None and candidate.fitness >= 0:
                play, discard, worthless = self.nextPlayDiscardIndex(player)
                if play is not None:
                    candidate.fitness += (self.game.numPlayers - i) * 3
            if candidate is not None and candidate.fitness > bestHint.fitness:
                bestHint = candidate
        if bestHint.fitness <= 0:
            return False

        bestHint.give(self)
        return True

    def giveHintOnNoDiscards(self):
        hint = Hint()
        for i in range(1, self.game.numPlayers):
            player = (self.position + i) % self.game.numPlayers
            hand = self.game.players[player].hand

            for v in self.values[:self.lowestPlayableValue-1] + [Value.V5]:
                tagged = 0
                match = 0
                for h in hand:
                    card = self.game.deck[h]
                    if card.rank == v:
                        if card.value is None:
                            tagged += 1
                        else:
                            match += 1
                if tagged or match:
                    base = 1
                    if v == Value.V5:
                        base = 50
                    elif v < self.lowestPlayableValue:
                        base = 10
                    fitness = tagged * base + match * 2 + i
                    if fitness > hint.fitness:
                        hint.fitness = fitness
                        hint.to = player
                        hint.color = None
                        hint.value = v
            for c in self.colors:
                tagged = 0
                matched = 0
                includeFive = False
                includeNonFive = False
                for h in hand:
                    card = self.game.deck[h]
                    if card.suit & c:
                        matched += 1
                        if card.color is None or not card.positiveClueColor:
                            tagged += 1
                        if card.rank == Value.V5 and card.value == Value.V5:
                            includeFive = True
                        if card.rank != Value.V5 and card.value is None:
                            includeNonFive = True
                if tagged:
                    fitness = 0
                    if self.colorComplete[c]:
                        fitness = tagged * 10 + i
                    if (includeFive and not includeNonFive
                            and (len(self.game.playedCards[c]) == 4
                                 or matched == 1)):
                        fitness = 100 + i
                    if fitness > hint.fitness:
                        hint.fitness = fitness
                        hint.to = player
                        hint.color = c
                        hint.value = None
        if hint.fitness:
            hint.give(self)
            return True
        else:
            assert None

    def maybeDiscardOldCard(self):
        play, discard, worthless = self.nextPlayDiscardIndex(self.position)
        if discard is not None:
            self.discard_card(discard)
            return True
        return False

    def pleaseObserveBeforeMove(self):
        self.lowestPlayableValue = 6
        for color in self.colors:
            lowest = len(self.game.playedCards[color]) + 1
            if lowest < self.lowestPlayableValue:
                self.lowestPlayableValue = lowest

        self.updateDiscardCount()
        self.updateColorValueTables()

        self.locatedCount = {c: [0] * 6 for c in self.colors}
        while self.updateLocatedCount():
            for p in range(self.game.numPlayers):
                for i in range(len(self.game.players[p].hand)):
                    knol = self.game.deck[self.game.players[p].hand[i]]
                    knol.update(False)

        self.updateEyesightCount()

        for k in self.colors:
            for v in self.values:
                assert self.locatedCount[k][v] <= self.eyesightCount[k][v]

    def pleaseObserveBeforeDiscard(self, from_, card_index, deckIdx):
        card = self.game.deck[deckIdx]
        self.seePublicCard(card.suit, card.rank)

    def pleaseObserveBeforePlay(self, from_, card_index, deckIdx):
        pass

    def pleaseObserveColorHint(self, from_, to, color, card_indices):
        for i in range(len(self.game.players[to].hand)):
            knol = self.game.deck[self.game.players[to].hand[i]]
            if i in card_indices:
                knol.clued = True
                knol.setMustBeColor(color)
                knol.update(False)
                if knol.value is not None:
                    playingValue = len(self.game.playedCards[color]) + 1
                    if knol.value == playingValue:
                        knol.setIsPlayable(True)
                    elif knol.value <= playingValue:
                        knol.setIsWorthless(True)
                elif len(self.game.playedCards[color]) == 5:
                    knol.setIsWorthless(True)
            else:
                knol.setCannotBeColor(color)

    def pleaseObserveValueHint(self, from_, to, value, card_indices):
        for i in range(len(self.game.players[to].hand)):
            knol = self.game.deck[self.game.players[to].hand[i]]
            if i in card_indices:
                knol.clued = True
                knol.setMustBeValue(value)
                knol.update(False)
                if knol.color is not None:
                    playingValue = len(self.game.playedCards[knol.color]) + 1
                    if knol.value == playingValue:
                        knol.setIsPlayable(True)
                    elif knol.value <= playingValue:
                        knol.setIsWorthless(True)
                elif value < self.lowestPlayableValue:
                    knol.setIsWorthless(True)
            else:
                knol.setCannotBeValue(value)

    def pleaseObserveAfterMove(self):
        pass

    def pleaseMakeMove(self, can_discard):
        assert self.game.currentPlayer == self.position

        if self.maybePlayCard():
            return
        if self.maybeGiveHelpfulHint():
            return

        if not can_discard:
            if self.giveHintOnNoDiscards():
                return
        else:
            if self.maybeDiscardOldCard():
                return

            best_index = 0
            for i in range(len(self.hand)):
                card = self.game.deck[self.hand[i]]
                bestCard = self.game.deck[self.hand[best_index]]
                if bestCard.value is None:
                    best_index = i
                elif card.value is not None and card.value > bestCard.value:
                    best_index = i
            self.discard_card(best_index)
