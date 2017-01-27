from copy import copy

from bot import bot
from enums import Color, Variant
from .card_knowledge import CardKnowledge
from .hint import Hint

colors = Variant.NoVariant.pile_colors
maxCount = [0, 3, 2, 2, 2, 1]


class Bot(bot.Bot):
    '''
    Note that this may not work on keldon since it may not support clues
    marking no cards.
    Has not been tested on Keldon
    Source: https://github.com/SliceOfBread/Hanabi
    '''
    BOT_NAME = 'Aww Bot'

    def __init__(self, game, position, name, **kwargs):
        if game.variant != Variant.NoVariant:
            raise ValueError()

        super().__init__(game, position, name, **kwargs)
        self.handLocked = [False] * 5
        self.handLockedIndex = [None] * 5
        self.clueWaiting = [False] * 5
        self.clueWaitingIndex = [0] * 5
        self.playedCount = {c: [0] * 6 for c in colors}
        self.locatedCount = {c: [0] * 6 for c in colors}
        self.eyesightCount = {c: [0] * 6 for c in colors}
        self.lowestPlayableValue = 0

    def create_player_card(self, player, deckPosition, color, value):
        return CardKnowledge(self.game, player, deckPosition, color, value)

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

    def someone_got_value(self, from_, to, number, positions):
        self.pleaseObserveValueHint(from_, to, number, positions)

    def got_value_clue(self, player, number, positions):
        self.pleaseObserveValueHint(player, self.position, number, positions)

    def decide_move(self, can_clue, can_discard):
        self.pleaseMakeMove(can_discard)

    def isPlayable(self, color, value):
        playableValue = len(self.game.playedCards[color]) + 1
        return value == playableValue

    def isValuable(self, color, value):
        if self.playedCount[color][value] != maxCount[value] - 1:
            return False
        return not self.isWorthless(color, value)

    def isWorthless(self, color, value):
        playableValue = len(self.game.playedCards[color]) + 1
        if value < playableValue:
            return True
        while(value > playableValue):
            value -= 1
            if self.playedCount[color][value] == maxCount[value]:
                return True
        return False

    def couldBePlayableWithValue(self, knol, value):
        if value < 1 or 5 < value:
            return False
        if knol.playable is not None:
            return knol.playable
        for c in colors:
            if knol.cantBe[c][value]:
                continue
            if self.isPlayable(c, value):
                return True
        return False

    def couldBeValuableWithValue(self, knol, value):
        if value < 1 or 5 < value:
            return False
        if knol.valuable is not None:
            return knol.valuable
        for c in colors:
            if knol.cantBe[c][value]:
                continue
            if self.isValuable(c, value):
                return True
        return False

    def updateEyesightCount(self):
        self.eyesightCount = {c: [0] * 6 for c in colors}
        for p in self.game.players:
            for c in p.hand:
                card = self.game.deck[c]
                if card.suit is not None and card.rank is not None:
                    self.eyesightCount[card.suit][card.rank] += 1
                elif card.color is not None and card.value is not None:
                    self.eyesightCount[card.color][card.value] += 1

    def updateLocatedCount(self):
        newCount = {c: [0] * 6 for c in colors}
        for p in self.game.players:
            for c in p.hand:
                card = self.game.deck[c]
                if card.color is not None and card.value is not None:
                    newCount[card.color][card.value] += 1

        if newCount != self.locatedCount:
            self.locatedCount = newCount
            return True
        return False

    def invalidateKnol(self, player, card):
        pass

    def seePublicCard(self, color, value):
        self.playedCount[color][value] += 1
        assert 1 <= self.playedCount[color][value] <= maxCount[value]

    def nextDiscardIndex(self, player):
        best_index = 0, None
        foundPlayable = 0
        for c in self.game.players[player].hand:
            card = self.game.deck[c]
            if card.playable is True:
                foundPlayable = 2
            if card.worthless is True:
                return 4, c
            if card.valuable is True:
                continue

            if best_index[0] == 0 and not card.clued:
                best_index = 1, c
        return best_index[0] + foundPlayable, best_index[1]

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
                    if (card.suit == color and card.rank == value
                            and card.clued):
                        return True
                    elif card.color == color and hand.value == value:
                        return True
        return returnVal

    def noValuableWarningWasGiven(self, from_):
        if self.game.deckCount == 0:
            return
        if self.game.clueCount == 0:
            return

        playerExpectingWarning = (from_ + 1) % self.game.numPlayers
        action, discardIndex = self.nextDiscardIndex(playerExpectingWarning)
        player = self.game.players[playerExpectingWarning]
        card = self.game.deck[player.hand[discardIndex]]
        card.setIsValuable(False)

    def bestHintForPlayer(self, player):
        assert player != self.position
        hand = self.game.players[player].hand

        lockCardIndex = None
        lockCard = None
        if (self.position + 2) % self.game.numPlayers == player:
            lh1 = (self.position + 1) % self.game.numPlayers
            lockCardIndex = self.lockCardToPlay(lh1)
            if lockCardIndex is not None:
                lockCard = hand[lockCardIndex]

        isReallyPlayable = [False] * len(hand)
        for c in range(len(hand)):
            card = self.game.deck[hand[c]]
            nextValue = len(self.game.playedCards[card.suit]) + 1
            isReallyPlayable[c] = card.rank == nextValue

        best_so_far = Hint()
        best_so_far.to = player
        for c in range(len(hand)):
            card = self.game.deck[hand[c]]
            colorClue = colors[4 - c]
            valueClue = len(hand) - c
            colorFitness = -1
            valueFitness = -1
            if isReallyPlayable[c]:
                if lockCardIndex is not None and lockCard == hand[c]:
                    continue
                if self.game.deck[hand[c]].playable is True:
                    continue

                clueElsewhere = self.isCluedElsewhere(player, c)
                if colorClue != Color.Blue:
                    colorFitness = 26 - card.value
                    if clueElsewhere is True:
                        colorFitness -= 5
                    for oc in range(len(hand)):
                        ocard = self.game.deck[hand[oc]]
                        if c == oc:
                            continue
                        eknol = copy(self.game.deck[hand[oc]])
                        if eknol.color is None:
                            continue
                        alreadyPlayable = eknol.playable is True
                        alreadyValuable = eknol.valuable is True
                        alreadyWorthless = eknol.worthless is True
                        alreadyClued = eknol.clued
                        if card.color == colorClue:
                            eknol.setMustBeColor(colorClue)
                        else:
                            eknol.setCannotBeColor(colorClue)
                        eknol.update(False)
                        if (ocard.color != card.color
                                or ocard.value != card.value):
                            if ocard.color == colorClue:
                                if not alreadyPlayable:
                                    colorFitness += 2
                                if (not alreadyValuable and not alreadyPlayable
                                        and self.isValuable(ocard.color,
                                                            ocard.value)):
                                    colorFitness += 15
                                elif (not alreadyValuable
                                      and not alreadyPlayable
                                      and eknol.valuable is not False):
                                    colorFitness += 1
                                if (not alreadyWorthless
                                        and eknol.worthless is True):
                                    colorFitness += 1
                                if (not alreadyWorthless
                                        and not alreadyPlayable
                                        and eknol.mustBeValue(ocard.value)):
                                    colorFitness += 5
                        else:
                            if not alreadyClued:
                                if ocard.color == colorClue:
                                    colorFitness -= 2
                if valueClue != 5:
                    valueFitness = 26 - card.value
                    if clueElsewhere is True:
                        valueFitness -= 2
                    for oc in range(len(hand)):
                        ocard = self.game.deck[hand[oc]]
                        if c == oc:
                            continue
                        eknol = copy(self.game.deck[hand[oc]])
                        if eknol.value is None:
                            continue
                        alreadyPlayable = eknol.playable is True
                        alreadyValuable = eknol.valuable is True
                        alreadyWorthless = eknol.worthless is True
                        alreadyClued = eknol.clued
                        if card.value == valueClue:
                            eknol.setMustBeValue(valueClue)
                        else:
                            eknol.setCannotBeValue(valueClue)
                        eknol.update(False)
                        if (ocard.color != card.color
                                or ocard.value != card.value):
                            if ocard.value == valueClue:
                                if not alreadyPlayable:
                                    valueFitness += 2
                                if (not alreadyValuable and not alreadyPlayable
                                        and self.isValuable(ocard.color,
                                                            ocard.value)):
                                    valueFitness += 15
                                elif (not alreadyValuable
                                      and not alreadyPlayable
                                      and eknol.valuable is not False):
                                    valueFitness += 1
                                if (not alreadyWorthless
                                        and eknol.worthless is True):
                                    valueFitness += 1
                                if (not alreadyWorthless
                                        and not alreadyPlayable
                                        and eknol.mustBeColor(ocard.color)):
                                    valueFitness += 5
                        else:
                            if not alreadyClued:
                                if ocard.color == colorClue:
                                    valueFitness -= 2
            if colorFitness > best_so_far.fitness:
                best_so_far.fitness = colorFitness
                best_so_far.color = colorClue
                best_so_far.value = None
            if valueFitness > best_so_far.fitness:
                best_so_far.fitness = valueFitness
                best_so_far.color = None
                best_so_far.value = valueClue
        return best_so_far


    def whatFinessePlay(self, partner, color, value):
        foundPart = False
        partIndex = None
        foundUnkown = False
        unknownIndex = None
        for c in range(len(self.game.players[partner].hand), -1, -1):
            knol = self.game.deck[self.game.players[partner].hand[c]]
            if knol.color == color and knol.value == value:
                return c
            if not foundPart:
                if knol.color == color or knol.value == value:
                    if not knol.cantBe[color][value]:
                        foundPart = True
                        partIndex = c
                        continue
            if not foundUnkown:
                if knol.color is None and knol.value is None:
                    foundUnkown = True
                    unknownIndex = c
        if foundPart:
            return partIndex
        return unknownIndex


    def lockCardToPlay(self, player):
        if self.clueWaiting[player]:
            return self.clueWaitingIndex[player]

        best_index = None
        best_fitness = 0
        for i in range(len(self.game.players[player].hand)):
            card = self.game.deck[self.game.players[player].hand[i]]
            if card.playable is not True:
                continue
            fitness = 6 - (card.value if card.value is not None else -1)
            if fitness >= best_fitness:
                best_index = i
                best_fitness = fitness
        return best_index

    def bestCardToPlay(self):
        if self.handLocked[self.position]:
            return self.handLockedIndex[self.position]

        eyeKnol = []
        for i in range(len(self.hand)):
            card = copy(self.game.deck[self.hand[i]])
            eyeKnol.append(card)
            card.update(True)

        best_index = None
        best_finess = 0
        for i in range(len(self.hand)):
            if eyeKnol[i].playable is True:
                continue
            fitness = 6 - (card.value if card.value is not None else -1)
            if self.game.clueCount < 1 and card.value == 5:
                fitness += 1
            if self.game.deck[self.hand[i]].playable is True:
                fitness += 100
            if fitness >= best_finess:
                best_index = i
                best_finess = fitness
        return best_index

    def maybePlayLowestPlayableCard(self):
        best_index = self.bestCardToPlay()
        if best_index is not None:
            self.play_card(best_index)
            return True
        return False

    def maybeGiveHelpfulHint(self):
        if self.game.clueCount == 0:
            return False

        bestHint = Hint()
        players = self.game.numPlayers if self.game.numPlayers <= 3 else 3
        for i in range(1, players):
            player = (self.position + i) % self.game.numPlayers
            if self.clueWaiting[player] or self.handLocked[player]:
                continue
            candidate = self.bestHintForPlayer(player)
            if candidate.fitness >= 0:
                hasPlayable = False
                for c in range(len(self.game.players[player].hand)):
                    knol = self.game.deck[self.game.players[player].hand[c]]
                    if knol.playable is True:
                        hasPlayable = True
                        break
                if not hasPlayable:
                    candidate.fitness += (self.game.numPlayers - i) * 3
            if candidate.fitness > bestHint.fitness:
                bestHint = candidate
        if bestHint.fitness <= 0:
            return False

        bestHint.give(self)
        return True

    def maybeFinesseNextPlayer(self, distanceToFinesse, distanceForFinesse):
        if (self.handLocked[self.position]
                and self.handLockedIndex[self.position] is None):
            return False

        numPlayers = self.game.numPlayers
        pToFinesse = (self.position + distanceToFinesse) % numPlayers
        pForFinesse = (self.position + distanceForFinesse) % numPlayers
        if pToFinesse == self.position and pForFinesse == self.position:
            return False

        if self.game.clueCount == 0:
            return False

        banned = {c: False for c in colors}
        nextValueForPile = {c: len(self.game.playedCards[c]) + 1
                            for c in colors}

        for i in range(2, distanceForFinesse):
            lp = (self.position + i) % numPlayers
            tmpLock = self.lockCardToPlay(lp)
            if tmpLock is None:
                playable, nextDiscard = self.nextDiscardIndex(lp)
                if playable < 2:
                    return False
            else:
                c = self.game.deck[self.game.players[lp].hand[tmpLock]].suit
                if banned[c]:
                    return False
                banned[c] = True

        isFinessable = [False] * 5
        havePotentialFinesse = False
        for c in range(len(self.game.players[pToFinesse].hand)):
            isFinessable[c] = False
            card = self.game.deck[self.game.players[pToFinesse].hand]
            if not banned[card.suit]:
                nextValue = len(self.game.playedCards[card.suit]) + 1
                isFinessable[c] = nextValue == card.rank

        for c in range(len(self.game.players[pToFinesse].hand)):
            card = self.game.deck[self.game.players[pToFinesse].hand]
            if isFinessable[c]:
                if card.rank == 5:
                    isFinessable[c] = False
                else:
                    findex = self.whatFinessePlay(pToFinesse, card.suit,
                                                  card.rank)
                    if findex != c:
                        isFinessable[c] = False
                    else:
                        havePotentialFinesse = True

        if not havePotentialFinesse:
            return False

        for c in range(len(self.game.players[pToFinesse].hand)):
            if isFinessable[c]:
                card = self.game.deck[self.game.players[pToFinesse].hand]
                fcolor = card.suit
                fvalue = card.rank + 1
                fplayer_hand = self.game.players[pForFinesse].hand
                for fc in range(len(fplayer_hand)):
                    handCard = self.game.deck[fplayer_hand[fc]]
                    if handCard.suit == fcolor and handCard.rank == fvalue:
                        colorFitness = -1
                        valueFitness = -1
                        colorClue = colors[4 - fc]
                        valueClue = len(fplayer_hand) - fc
                        for oc in range(len(fplayer_hand)):
                            if fc == oc:
                                continue
                            ocCard = self.game.deck[fplayer_hand[oc]]
                            if colorClue != Color.Blue:
                                colorFitness += 1
                                if fplayer_hand[oc].suit == colorClue:
                                    if not ocCard.mustBeColor(colorClue):
                                        colorFitness += 1
                                        if (not ocCard.clued
                                                and self.isValuable(
                                                    ocCard.suit, ocCard.rank)):
                                            colorFitness += 4
                            if valueClue != 5:
                                valueFitness += 1
                                if fplayer_hand[oc].rank == valueClue:
                                    if not ocCard.mustBeValue(valueClue):
                                        valueFitness += 1
                                        if (ocCard.clued
                                                and self.isValuable(
                                                    ocCard.suit, ocCard.rank)):
                                            valueFitness += 4
                        if colorFitness > valueFitness:
                            self.give_color_clue(pForFinesse, colorClue)
                            return True
                        elif valueFitness > -1:
                            self.give_value_clue(pForFinesse, valueClue)
                        else:
                            assert False
                if self.maybeFinesseNextPlayer(distanceToFinesse,
                                               distanceForFinesse + 1):
                    return True
        return False

    def maybeGiveValuableWarning(self, playerDistance):
        if self.handLocked[self.position]:
            return False

        if self.game.clueCount == 0:
            return False

        numPlayers = self.game.numPlayers
        player_to_warn = (self.position + playerDistance) % numPlayers

        action, discardIndex = self.nextDiscardIndex(player_to_warn)

        if action >= 4 or action % 2 == 0:
            return False

        doubleDiscardPossible = False
        warnedPlayer = self.game.players[player_to_warn]
        targetCard = self.game.deck[warnedPlayer.hand[discardIndex]]
        lh2 = -1
        lh2action, lh2discard = 0, None
        if not self.isValuable(targetCard.suit, targetCard.rank):
            if numPlayers > 2 and playerDistance == 1:
                lh2 = (player_to_warn + 1) % numPlayers
                lh2action, lh2discard = self.nextDiscardIndex(lh2)
                if lh2action >= 4 or lh2action % 2 == 0:
                    return False
                lh2player = self.game.players[lh2]
                lh2target = self.game.deck[lh2player.hand[lh2discard]]
                if (targetCard.suit == lh2target.suit
                        and targetCard.rank == lh2target.rank):
                    doubleDiscardPossible = True
                else:
                    return False
            else:
                return False

        if action >= 3:
            return False

        assert targetCard.playable is not True
        assert targetCard.valuable is not True
        assert targetCard.worthless is not True

        bestHint = self.bestHintForPlayer(player_to_warn)
        if bestHint.fitness > 0:
            bestHint.give(self)
            return True

        if doubleDiscardPossible:
            if lh2action >= 3:
                return False
            bestHint = self.bestHintForPlayer(lh2)
            if bestHint.fitness > 0:
                bestHint.give(self)
                return True

            self.give_value_clue(lh2, 5)
            return True

        if targetCard.rank == self.lowestPlayableValue:
            nextVal = len(self.game.playedCards[targetCard.suit]) + 1
            assert nextVal == targetCard.rank
        else:
            assert targetCard.rank > self.lowestPlayableValue

        if targetCard.rank == 5 and playerDistance == 1:
            self.give_value_clue(player_to_warn, 5)
        else:
            self.give_color_clue(player_to_warn, Color.Blue)
        return True

    def maybeGiveSuperHint(self):
        if self.game.clueCount == 0:
            return 0
        if self.game.deckCount > 1:
            return False

        numPlayers = self.game.numPlayers
        partner = (self.position + 1) % numPlayers
        bestHint = self.bestHintForPlayer(partner)
        if bestHint.fitness < 0:
            return False
        hasPlayable = False
        for c in range(len(self.game.players[partner].hand)):
            knol = self.game.deck[self.game.players[partner].hand[c]]
            if knol.playable is True:
                hasPlayable = True
                break
        if hasPlayable:
            return False

        bestHint.give(self)
        return True

    def maybePlayMysteryCard(self):
        if self.handLocked[self.position]:
            return False
        if self.clueWaiting[(self.position + 1) % self.game.numPlayers]:
            return False

        table = [-99, 1, 1, 3]
        if self.game.deckCount <= table[3 - self.game.strikeCount]:
            for i in range(len(self.hand)):
                eyeKnol = copy(self.game.deck[self.hand[i]])
                eyeKnol.update(True)
                assert eyeKnol.playable is not True
                if eyeKnol.playable is None:
                    self.play_card(i)
                    return True
        return False

    def maybeDiscardWorthlessCard(self):
        eyeKnol = []
        for i in range(len(self.hand)):
            eyeKnol.append(copy(self.game.deck[self.hand[i]]))
            eyeKnol[i].update(True)

        best_index = None
        best_fitness = 0
        for i in range(len(self.hand)):
            if eyeKnol[i].worthless is not True:
                continue

            if self.game.deck[self.hand[i]].worthless is True:
                fitness = 1
            else:
                fitness = 2

            if fitness > best_fitness:
                best_index = i
                best_fitness = fitness

        if best_index is not None:
            self.discard_card(best_index)
            return True
        return False

    def maybeDiscardOldCard(self):
        action, best_index = self.nextDiscardIndex(self.position)
        assert action < 4
        if action % 2 != 0:
            self.discard_card(best_index)
            return True
        return False

    def cardOnChop(self, player):
        numCards = len(self.hand)
        best_fitness = 0
        best_index = None
        for i in range(numCards):
            knol = self.game.deck[self.hand[i]]
            fitness = 0
            if knol.playable is True:
                continue
            if knol.worthless is True:
                return i
            if knol.valuable is True:
                continue

            if best_index is None and not knol.clued:
                best_index = i
        return best_index

    def upcomingIssues(self):
        numPlayers = self.game.numPlayers
        return 0

    def pleaseObserveBeforeMove(self):
        ap = self.game.currentPlayer
        if self.clueWaiting[ap]:
            deckIdx = self.game.players[ap].hand[self.clueWaitingIndex[ap]]
            self.game.deck[deckIdx].setIsPlayable(True)
            self.clueWaiting[ap] = False

        self.locatedCount = {c: [0] * 6 for c in colors}
        self.updateLocatedCount()
        while True:
            for p in range(self.game.numPlayers):
                for i in range(len(self.game.players[p].hand)):
                    knol = self.game.deck[self.game.players[p].hand[i]]
                    knol.update(False)
            if not self.updateLocatedCount():
                break

        self.updateEyesightCount()

        self.lowestPlayableValue = 6
        for color in colors:
            lowest = len(self.game.playedCards[color]) + 1
            if lowest < self.lowestPlayableValue:
                self.lowestPlayableValue = lowest

        for k in colors:
            for v in range(1, 5):
                assert self.locatedCount[k][v] <= self.eyesightCount[k][v]

    def pleaseObserveBeforeDiscard(self, from_, card_index, deckIdx):
        card = self.game.deck[deckIdx]
        self.seePublicCard(card.suit, card.rank)
        self.invalidateKnol(from_, card_index)

    def pleaseObserveBeforePlay(self, from_, card_index, deckIdx):
        card = self.game.deck[deckIdx]
        # assert card.worthless is not True
        if card.valuable is True:
            # assert self.isValuable(card.suit, card.rank)
            pass
        self.seePublicCard(card.suit, card.valuable)
        self.invalidateKnol(from_, card_index)

    def pleaseObserveColorHint(self, from_, to, color, card_indices):
        playableIndex = 4 - colors.index(color)
        toHandSize = len(self.game.players[to].hand)

        seenUnclued = False
        for i in range(toHandSize):
            knol = self.game.deck[self.game.players[to].hand[i]]
            if color == Color.Blue and not seenUnclued and not knol.clued:
                seenUnclued = True
                knol.clued = True
                knol.setIsValuable(True)
            if i in card_indices:
                knol.clued = True
                knol.setMustBeColor(color)
                knol.update(False)
            else:
                knol.setCannotBeColor(color)

        numPlayers = self.game.numPlayers
        if color != Color.Blue:
            knol = self.game.deck[self.game.players[to].hand[playableIndex]]
            if to != (from_ + 1) % numPlayers:
                self.clueWaiting[to] = True
                self.clueWaitingIndex[to] = playableIndex
                knol.clued = True
                lhp = (from_ + 1) % numPlayers
                self.handLocked[lhp] = True
                if self.position != to:
                    deckIdx = self.game.players[to].hand[playableIndex]
                    possibleFinesseCard = self.game.deck[deckIdx]
                    if self.isPlayable(possibleFinesseCard.suit,
                                       possibleFinesseCard.rank):
                        self.handLockedIndex[lhp] = self.lockCardToPlay(lhp)
                    else:
                        self.handLockedIndex[lhp] = self.whatFinessePlay(
                            lhp, possibleFinesseCard.suit,
                            possibleFinesseCard.rank)
                else:
                    self.handLockedIndex[lhp] = self.lockCardToPlay(lhp)
                while True:
                    lhp = (lhp + 1) % numPlayers
                    if lhp == to:
                        break
                    self.handLocked[lhp] = True
                    self.handLockedIndex[lhp] = self.lockCardToPlay(lhp)
            else:
                if knol.playable is not False:
                    knol.setIsPlayable(True)
                    knol.clued = True
                    knol.update(False)

    def pleaseObserveValueHint(self, from_, to, value, card_indices):
        toHandSize = self.game.players[to]
        playableIndex = toHandSize - value

        lh1 = (from_ + 1) % self.game.numPlayers
        _, lh1discard = self.nextDiscardIndex(lh1)
        _, lh2discard = self.nextDiscardIndex(to)

        for i in range(toHandSize - 1, -1, -1):
            knol = self.game.deck[self.game.players[to].hand[i]]
            if i in card_indices:
                knol.clued = True
                knol.setMustBeValue(value)
                knol.update(False)
            else:
                knol.setCannotBeValue(value)

        if value != 5:
            knol = self.game.deck[self.game.players[to].hand[playableIndex]]
            if to != (from_ + 1) % self.game.numPlayers:
                self.clueWaiting[to] = True
                self.clueWaitingIndex[to] = playableIndex
                knol.clued = True
                lhp = (from_ + 1) % self.game.numPlayers
                self.handLocked[lhp] = True
                if self.position != to:
                    deckIdx = self.game.players[to].hand[playableIndex]
                    possibleFinesseCard = self.game.deck[deckIdx]
                    if self.isPlayable(possibleFinesseCard.suit,
                                       possibleFinesseCard.rank):
                        self.handLockedIndex[lhp] = self.lockCardToPlay(lhp)
                    else:
                        self.handLockedIndex[lhp] = self.whatFinessePlay(
                            lhp, possibleFinesseCard.suit,
                            possibleFinesseCard.rank)
                    while True:
                        lhp = (lhp + 1) % self.game.numPlayers
                        if lhp == to:
                            break
                        self.handLocked[lhp] = True
                        self.handLockedIndex[lhp] = self.lockCardToPlay(lhp)
                elif knol.playable is not False:
                    knol.setIsPlayable(True)
                    knol.clued = True
                    knol.update(False)
        else:
            if to != (from_ + 2) % self.game.numPlayers:
                hand = self.game.players[to].hand
                lh1knol = self.game.deck[hand[lh1discard]]
                knol = self.game.deck[hand[lh2discard]]
                knol.clued = True
                if self.position == from_:
                    ct = self.game.deck[hand[lh2discard]]
                    hand = self.game.players[lh1].hand
                    cl = self.game.deck[hand[lh1discard]]
                    assert ct.suit == cl.suit and ct.rank == cl.rank
                if self.position != lh1:
                    hand = self.game.players[lh1].hand
                    lh1card = self.game.deck[hand[lh1discard]]
                    knol.setMustBeColor(lh1card.suit)
                    knol.setMustBeValue(lh1card.rank)
                    knol.update(False)
                else:
                    lh2card = self.game.deck[hand[lh2discard]]
                    knol.setMustBeColor(lh2card.suit)
                    knol.setMustBeValue(lh2card.value)
                    knol.update(False)

    def pleaseObserveAfterMove(self):
        player = self.game.currentPlayer
        self.handLocked[player] = False

    def pleaseMakeMove(self, can_discard):
        assert self.game.currentPlayer == self.position

        if self.game.deckCount > self.game.numPlayers:
            if self.maybeFinesseNextPlayer(1, 2):
                return
            if self.maybeGiveValuableWarning(1):
                return
            if self.game.clueCount == 1:
                if self.game.numPlayers > 2:
                    if self.maybeGiveValuableWarning(2):
                        return
            if self.maybePlayLowestPlayableCard():
                return
            if self.game.numPlayers > 2:
                if self.maybeGiveValuableWarning(2):
                    return
            if self.maybeGiveHelpfulHint():
                return
            if self.maybePlayMysteryCard():
                return
        elif self.game.deckCount == 0:
            if self.maybePlayLowestPlayableCard():
                return
            if self.maybeGiveSuperHint():
                return
            if self.maybePlayMysteryCard():
                return
        else:
            if self.maybeGiveValuableWarning(1):
                return
            if self.maybePlayLowestPlayableCard():
                return
            if self.maybeGiveHelpfulHint():
                return
            if self.maybePlayMysteryCard():
                return

        if not can_discard:
            # TODO: Fix uesless clue
            player = (self.position + 1) % self.game.numPlayers
            self.give_value_clue(player, 5)
        else:
            if self.maybeDiscardWorthlessCard():
                return
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
