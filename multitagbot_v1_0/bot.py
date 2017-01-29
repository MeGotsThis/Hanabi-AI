import time

from itertools import chain

from bot import bot
from enums import Value, Variant
from .card_knowledge import CardKnowledge
from .hint import Hint


class Bot(bot.Bot):
    '''
    Multi-tag Bot v1.0
    This is based from Only Full Tag Bot v1.5
    Will Clue multiple cards where the newest is playable and next known card
    is playable and etc
    '''
    BOT_NAME = 'Multi-tag Bot v1.0'

    def __init__(self, game, position, name, wait=0, **kwargs):
        if game.variant != Variant.NoVariant:
            raise ValueError()

        super().__init__(game, position, name, **kwargs)
        self.waitTime = int(wait)
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
        self.colorComplete = {c: False * 6 for c in self.colors}
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
        if self.waitTime:
            time.sleep(self.waitTime)
        self.pleaseMakeMove(can_discard)

    def isNowPlayable(self, color, value):
        assert color is not None or value is not None
        if color is not None and value is not None:
            return self.isPlayable(color, value)
        if color is not None:
            playableValue = len(self.game.playedCards[color]) + 1
            if (playableValue <= 5
                    and not self.locatedCount[color][playableValue]):
                return True
            return False
        if value is not None:
            for c in self.colors:
                if (len(self.game.playedCards[c]) + 1 == value
                        and not self.locatedCount[c][value]):
                    return True
            return False

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
            score = len(self.game.playedCards[c])
            if score == 5:
                self.colorComplete[c] = True
                self.maxPlayValue[c] = 5
            else:
                self.maxPlayValue[c] = score
                for v in self.values[score:]:
                    if self.discardCount[c][v] == v.num_copies:
                        self.colorComplete[c] = self.maxPlayValue[c] == score
                        break
                    self.maxPlayValue[c] = v

    def seePublicCard(self, color, value):
        self.playedCount[color][value] += 1
        assert 1 <= self.playedCount[color][value] <= value.num_copies

    def nextPlayDiscardIndex(self, player):
        play_index = None
        playable_value = None
        discard_index = None
        worthless = False
        for c, h in enumerate(self.game.players[player].hand):
            card = self.game.deck[h]
            if card.playable is True:
                if card.playable:
                    # Play newest
                    playable = 10
                    #if card.value is not None:
                    #    playable += (6 - card.value) * 4
                    #elif card.playValue is not None:
                    #    playable += (6 - card.playValue) * 4
                    #if card.color is not None and card.value is not None:
                    #    playable += 2
                    if playable_value is None or playable >= playable_value:
                        play_index = c
                        playable_value = playable
                continue
            if card.worthless is True:
                # Discard worthless newest
                discard_index = c
                worthless = True
                continue
            if card.playWorthless is True:
                # Discard deduced worthless newest
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

    def isCluedSomewhere(self, color, value, player=None, strict=False):
        for p in self.game.players:
            if player == p.position:
                if strict:
                    continue
                # When it is the player, assume fully tagged cards as clued too
                for c in p.hand:
                    card = self.game.deck[c]
                    if card.color == color and card.value == value:
                        return True
            elif p is self:
                for c in p.hand:
                    card = self.game.deck[c]
                    if card.color == color and card.value == value:
                        return True
            else:
                for c in p.hand:
                    card = self.game.deck[c]
                    if (card.clued
                            and card.suit == color
                            and card.rank == value):
                        return True
        return False

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

    def maybeFixBeforeMisplay(self):
        return False

    def maybeSaveCriticalCard(self):
        return False

    def discardForCriticalCard(self):
        return False

    def valueOrderFromColor(self, color, taggedCards, player,
                            otherPlayer=None, otherColor=None,
                            otherValue=None):
        assert otherColor is None or otherValue is None
        assert otherPlayer is None or (otherColor is not None or
                                       otherValue is not None)
        tagged = taggedCards[:]
        values = []
        elseWhereColor = []
        elseWhereValue = []
        if isinstance(otherPlayer, int):
            for h in self.game.players[otherPlayer].hand:
                card = self.game.deck[h]
                if otherColor is not None and card.suit & otherColor:
                    elseWhereValue.append(card.rank)
                if otherValue is not None and card.rank == otherValue:
                    elseWhereColor.append(card.suit)
        score = len(self.game.playedCards[color])
        isNewestGood = None
        needFix = False
        numPlay, numWorthless = 0, 0
        for v in self.values[score:self.maxPlayValue[color]]:
            if not tagged:
                break
            if self.isCluedSomewhere(color, v, player, strict=True):
                continue
            if isinstance(otherPlayer, int):
                if v in elseWhereValue:
                    continue
                if color in elseWhereColor:
                    continue
            for i, t in enumerate(tagged[:]):
                card = self.game.deck[t]
                if (card.value == v
                        or (otherPlayer is True and otherValue == card.rank)):
                    if card.rank == score + 1:
                        isNewestGood = True
                    values.append((t, v))
                    tagged.remove(t)
                    numPlay += 1
                    break
            else:
                for t in tagged[:]:
                    card = self.game.deck[t]
                    if (card.value is not None
                        or (otherPlayer is True and otherValue == card.rank)):
                        continue
                    if v == score + 1:
                        isNewestGood = card.rank == score + 1
                    if card.rank != v:
                        needFix = True
                    values.append((t, v))
                    tagged.remove(t)
                    numPlay += 1
                    break
        if tagged:
            for t in tagged:
                values.append((t, None))
                numWorthless += 1
        return values, numPlay, numWorthless, isNewestGood, needFix

    def playOrderColorClue(self, player, color):
        assert player != self.position
        tagged = []
        hand = self.game.players[player].hand
        numNewTagged = 0
        badClarify = 0
        for h in reversed(hand):
            card = self.game.deck[h]
            if not (card.suit & color):
                continue
            tagged.append(h)
            if card.color is None:
                numNewTagged += 1
                if card.value is not None:
                    if card.playColorDirect or card.playable:
                        badClarify += 1
        (playOrder, numPlay, numWorthless, isNewestGood,
         needFix) = self.valueOrderFromColor(color, tagged, player)

        fixPlayer, fixColor, fixValue = None, None, None
        if needFix:
            for tagV in self.values:
                # Test Fix Clues
                (playOrder_, numPlay_, numWorthless_, isNewestGood_,
                 needFix_) = self.valueOrderFromColor(color, tagged, player,
                                                      otherPlayer=True,
                                                      otherValue=tagV)

                if not needFix_:
                    fixPlayer = player
                    fixColor = None
                    if fixValue is None:
                        fixValue = []
                    fixValue.append(tagV)

            for p in range(self.game.numPlayers):
                if p == player or p == self.position:
                    continue
                (playOrder_, numPlay_, numWorthless_, isNewestGood_,
                 needFix_) = self.valueOrderFromColor(color, tagged, player,
                                                      otherPlayer=p,
                                                      otherValue=tagV)

                if not needFix_:
                    fixPlayer = player
                    fixColor = None
                    if fixValue is None:
                        fixValue = []
                    fixValue.append(tagV)
        return (playOrder, numPlay, numWorthless, isNewestGood, needFix,
                numNewTagged, badClarify, fixPlayer, fixColor, fixValue)

    def playOrderValueClue(self, player, value):
        assert player != self.position
        tagged = []
        hand = self.game.players[player].hand
        for h in reversed(hand):
            card = self.game.deck[h]
            if card.rank == value:
                tagged.append(h)
        playColors = []
        futureColors = []
        for c in self.colors:
            if self.colorComplete[c]:
                continue
            if self.isCluedSomewhere(c, value, self.position):
                continue
            scoreTagged = len(self.game.playedCards[c])
            for v in self.values[scoreTagged:]:
                if self.isCluedSomewhere(c, value, self.position):
                    scoreTagged = v
            if scoreTagged > value:
                continue
            if scoreTagged == value - 1:
                playColors.append(c)
            elif scoreTagged < value - 1:
                futureColors.append(c)
        neededColors = playColors + futureColors
        playOrder = []
        colorUsed = []
        numPlay, numFuture, numWorthless = 0, 0, 0
        numPlayMismatch = 0
        numFutureMismatch = 0
        numCompleteMismatch = 0
        for i, t in enumerate(tagged):
            card = self.game.deck[t]
            if i < len(playColors):
                playOrder.append((t, playColors))
                if card.suit in playColors and card.suit not in colorUsed:
                    numPlay += 1
                    colorUsed.append(card.suit)
                else:
                    numPlayMismatch += 1
                if card.suit not in neededColors:
                    numCompleteMismatch += 1
            elif i < len(playColors) + len(futureColors):
                playOrder.append((t, futureColors))
                if card.suit in futureColors and card.suit not in colorUsed:
                    numFuture += 1
                    colorUsed.append(card.suit)
                else:
                    numFutureMismatch += 1
                if card.suit not in neededColors:
                    numCompleteMismatch += 1
            else:
                playOrder.append((t, None))
                numWorthless += 1

        return (playOrder,
                numPlay, numFuture, numWorthless,
                numPlayMismatch, numFutureMismatch, numCompleteMismatch)

    def bestHintForPlayer(self, player):
        assert player != self.position
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
            for i in range(len(hand)):
                card = self.game.deck[hand[i]]
                if card.suit & c:
                    tagged.append(i)
            if not tagged:
                continue

            colorFitness = 0

            # Decision Here
            (values, numPlay, numWorthless, isNewestGood, needFix,
             numNewTagged, badClarify, fixPlayer, fixColor,
             fixValue) = self.playOrderColorClue(player, c)
            needToPlay = self.maxPlayValue[c] - len(self.game.playedCards[c])
            if (not needFix and isNewestGood and values[0][1] is not None
                and (numNewTagged - badClarify > 0
                     or badClarify == needToPlay)):
                colorFitness = numPlay * 22 + numWorthless

            if colorFitness > best_so_far.fitness:
                best_so_far.fitness = colorFitness
                best_so_far.color = c
                best_so_far.value = None

        for v in self.values:
            tagged = []
            for i in range(len(hand)):
                card = self.game.deck[hand[i]]
                if card.rank == v:
                    tagged.append(i)
            if not tagged:
                continue

            valueFitness = 0

            # Decision Here
            if v < self.lowestPlayableValue:
                pass
            else:
                (playOrder, numPlay, numFuture, numWorthless,
                 numPlayMismatch, numFutureMismatch,
                 numCompleteMismatch) = self.playOrderValueClue(player, v)
                if (numPlay >= 1 and numPlayMismatch == 0
                        and numFutureMismatch == 0
                        and numCompleteMismatch == 0):
                    baseValue, baseFuture = (20, 7) if v != 5 else (5, 2)
                    valueFitness = (numPlay * baseValue
                                    + numFuture * baseFuture
                                    + numWorthless)

            if valueFitness > best_so_far.fitness:
                best_so_far.fitness = valueFitness
                best_so_far.color = None
                best_so_far.value = v

        if best_so_far.fitness == 0:
            return None
        return best_so_far

    def bestCardToPlay(self):
        play, discard, worthless = self.nextPlayDiscardIndex(self.position)
        return play

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
            candidate = self.bestHintForPlayer(player)
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
                        base = 100
                    elif v < self.lowestPlayableValue:
                        base = 20
                    fitness = tagged * base + match * 5 + i
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
                        fitness = tagged * 20 + i
                    if (includeFive and not includeNonFive
                            and (len(self.game.playedCards[c]) == 4
                                 or matched == 1)):
                        fitness = 200 + i
                    if fitness > hint.fitness:
                        hint.fitness = fitness
                        hint.to = player
                        hint.color = c
                        hint.value = None
            for v in self.values[self.lowestPlayableValue-1:4]:
                tagged = 0
                for h in hand:
                    card = self.game.deck[h]
                    if card.rank == v:
                        tagged += 1
                if tagged:
                    fitness = tagged + i
                    if fitness > hint.fitness:
                        hint.fitness = fitness
                        hint.to = player
                        hint.color = None
                        hint.value = v
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

    def discardSomeCard(self):
        best_index = 0
        for i in range(len(self.hand)):
            card = self.game.deck[self.hand[i]]
            bestCard = self.game.deck[self.hand[best_index]]
            if bestCard.value is None:
                best_index = i
            elif card.value is not None and card.value > bestCard.value:
                best_index = i
        self.discard_card(best_index)
        return True

    def updatePlayableValue(self, player):
        rtnValue = False
        player_ = self.game.players[player]
        cardsNeeded = {c: 0 for c in self.colors}
        fullyKnown = {c: 0 for c in self.colors}
        for c in self.colors:
            if self.colorComplete[c]:
                continue
            score = len(self.game.playedCards[c])
            for v in self.values[score:self.maxPlayValue[c]]:
                if not self.isCluedSomewhere(c, v, player):
                    cardsNeeded[c] += 1
                else:
                    if (self.locatedCount[c][v]
                            or self.eyesightCount[c][v] == v.num_copies):
                        fullyKnown[c] += 1
        for c in self.colors:
            if self.colorComplete[c]:
                continue
            tagged = []
            for h in reversed(player_.hand):
                card = self.game.deck[h]
                if card.clued and card.color == c:
                    tagged.append(h)
            if cardsNeeded[c] + fullyKnown[c] <= len(tagged):
                for t in tagged:
                    card = self.game.deck[t]
                    if not card.cluedAsPlay:
                        card.cluedAsPlay = True
                        rtnValue = True
            for v in self.values[len(self.game.playedCards[c]):]:
                if not tagged:
                    break
                if self.isCluedSomewhere(c, v, player):
                    continue
                for t in tagged[:]:
                    card = self.game.deck[t]
                    if card.cantBe[c][v]:
                        if card.playValue == v:
                            card.playValue = None
                            rtnValue = True
                        continue
                    if card.playValue != v:
                        card.playValue = v
                        card.playWorthless = False
                        rtnValue = True
                    tagged.remove(t)
                    break
            for t in tagged:
                card = self.game.deck[t]
                if card.clued and card.value is None and card.color == c:
                    card.playValue = None
                    card.playWorthless = True
        return rtnValue

    def pleaseObserveBeforeMove(self):
        self.updateDiscardCount()
        self.updateColorValueTables()

        self.lowestPlayableValue = 6
        for color in self.colors:
            if self.colorComplete[color]:
                continue
            lowest = len(self.game.playedCards[color]) + 1
            if lowest < self.lowestPlayableValue:
                self.lowestPlayableValue = lowest

        self.locatedCount = {c: [0] * 6 for c in self.colors}
        self.updateLocatedCount()
        while True:
            self.updateEyesightCount()
            done = True
            for p in range(self.game.numPlayers):
                for i in range(len(self.game.players[p].hand)):
                    knol = self.game.deck[self.game.players[p].hand[i]]
                    knol.update(False)
            t = not self.updateLocatedCount()
            done = t and done
            for p in range(self.game.numPlayers):
                t = not self.updatePlayableValue(p)
                done = t and done
            if done:
                break

        self.updateEyesightCount()

        for k in self.colors:
            for v in self.values:
                assert self.locatedCount[k][v] <= self.eyesightCount[k][v]

    def pleaseObserveBeforeDiscard(self, from_, card_index, deckIdx):
        card = self.game.deck[deckIdx]
        self.seePublicCard(card.suit, card.rank)

    def pleaseObserveBeforePlay(self, from_, card_index, deckIdx):
        card = self.game.deck[deckIdx]
        self.seePublicCard(card.suit, card.rank)

    def pleaseObserveColorHint(self, from_, to, color, card_indices):
        score = len(self.game.playedCards[color])
        playable, discard, worthless = self.nextPlayDiscardIndex(to)

        for i in range(len(self.game.players[to].hand)):
            knol = self.game.deck[self.game.players[to].hand[i]]
            if i in card_indices:
                knol.clued = True
                knol.setMustBeColor(color)
                knol.update(False)
                if knol.value is not None:
                    playingValue = score + 1
                    if knol.value == playingValue:
                        knol.setIsPlayable(True)
                    elif knol.value <= playingValue:
                        knol.setIsWorthless(True)
                elif self.colorComplete[color]:
                    knol.setIsWorthless(True)
                numToComplete = self.maxPlayValue[color] - score
                if (not worthless and discard in card_indices
                        and numToComplete > len(card_indices)):
                    knol.cluedAsDiscard = True
                else:
                    knol.cluedAsPlay = True
            else:
                knol.setCannotBeColor(color)

    def pleaseObserveValueHint(self, from_, to, value, card_indices):
        hand = self.game.players[to].hand
        possibleColors = []
        laterColors = []
        for c in self.colors:
            if self.isCluedSomewhere(c, value, to):
                continue
            match = False
            for i in card_indices:
                card = self.game.deck[hand[i]]
                if card.color == c:
                    match = True
                    break
            if match:
                continue
            score = len(self.game.playedCards[c])
            if len(self.game.playedCards[c]) >= value:
                continue
            if score < value - 1:
                for v in self.values[score:value - 1]:
                    if not self.isCluedSomewhere(c, v, to):
                        laterColors.append(c)
                        break
            else:
                possibleColors.append(c)
        playable, discard, worthless = self.nextPlayDiscardIndex(to)
        count = 0
        for i, h in reversed(list(enumerate(hand))):
            knol = self.game.deck[h]
            if i in card_indices:
                knol.clued = True
                knol.setMustBeValue(value)
                if knol.color is not None:
                    playingValue = len(self.game.playedCards[knol.color]) + 1
                    if knol.value == playingValue:
                        knol.setIsPlayable(True)
                    elif knol.value <= playingValue:
                        knol.setIsWorthless(True)
                elif value < self.lowestPlayableValue:
                    knol.setIsWorthless(True)
                else:
                    knol.playColors.clear()
                    if knol.color is None:
                        if count < len(possibleColors):
                            for c in possibleColors:
                                if knol.cannotBeColor(c):
                                    continue
                                knol.playColors.append(c)
                            knol.playColorDirect = True
                            count += 1
                        elif count < len(possibleColors) + len(laterColors):
                            for c in laterColors:
                                if knol.cannotBeColor(c):
                                    continue
                                knol.playColors.append(c)
                            count += 1
                        else:
                            knol.playWorthless = True
                if ((not worthless and discard in card_indices)
                        or value == Value.V5):
                    knol.cluedAsDiscard = True
                    knol.playColors.clear()
                    for c in chain(possibleColors, laterColors):
                        if knol.cannotBeColor(c):
                            continue
                        knol.playColors.append(c)
                elif len(card_indices) == 1:
                    if knol.color is None:
                        knol.cluedAsPlay = True
                    else:
                        for h in hand:
                            taggedCard = self.game.deck[h]
                            if taggedCard.color == knol.color:
                                taggedCard.cluedAsPlay = True
                knol.update(False)
            else:
                knol.setCannotBeValue(value)

    def pleaseObserveAfterMove(self):
        pass

    def pleaseMakeMove(self, can_discard):
        assert self.game.currentPlayer == self.position

        if self.maybeFixBeforeMisplay():
            return
        if self.maybeSaveCriticalCard():
            return
        if self.discardForCriticalCard():
            return
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
            if self.discardSomeCard():
                return
        assert False
