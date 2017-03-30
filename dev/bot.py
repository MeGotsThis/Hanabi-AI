import time

from enum import Enum, auto
from itertools import chain

from bot import bot
from enums import Color, Value, Variant
from .card_knowledge import CardKnowledge, CardState
from .clue_info import ClueState
from .hint import Hint


class GameStage(Enum):
    Early = auto()
    Mid = auto()
    End = auto()


class HandState(Enum):
    Unclued = auto()
    Critical = auto()
    Critical2 = auto()
    SoonPlay = auto()
    Playable = auto()
    Worthless = auto()
    Saved = auto()


class Bot(bot.Bot):
    '''
    Multi-tag Bot

    Changes from v2.1
    '''
    BOT_NAME = 'Dev Bot'

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
        self.clueLog = [[] for p in range(self.game.numPlayers)]

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
        self.pleaseMakeMove(can_clue, can_discard)

    def game_stage(self):
        if len(self.game.discards) == 0:
            return GameStage.Early
        if self.game.deckCount <= len(self.game.players):
            return GameStage.End
        return GameStage.Mid

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

    def is2Valuable(self, color):
        if self.lowestPlayableValue > 2:
            return False
        if self.isCluedSomewhere(color, 2, maybe=True):
            return False
        return self.eyesightCount[color][2] != Value.V2.num_copies

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

    def handState(self, player, showCritical=True):
        handState = [HandState.Unclued] * len(self.game.players[player].hand)
        for c, h in enumerate(self.game.players[player].hand):
            card = self.game.deck[h]
            if card.worthless is True:
                handState[c] = HandState.Worthless
                continue
            if card.playWorthless is True:
                handState[c] = HandState.Worthless
                continue
            if card.playable is True:
                handState[c] = HandState.Playable
                continue
            if card.valuable is True:
                handState[c] = HandState.Saved
                continue
            if card.clued:
                handState[c] = HandState.SoonPlay
                continue
            if showCritical and player != self.position:
                if self.isValuable(card.suit, card.rank):
                    handState[c] = HandState.Critical
                elif card.rank == Value.V2 and self.is2Valuable(card.suit):
                    handState[c] = HandState.Critical2
        return handState

    def discardSlot(self, handState):
        discard = None
        worthless = None
        for c, h in enumerate(handState):
            if h in [HandState.Playable, HandState.SoonPlay, HandState.Saved]:
                continue
            if h == HandState.Worthless:
                worthless = c
            else:
                if discard is None:
                    discard = c
        return worthless if worthless is not None else discard

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

    def cluedCard(self, color, value, player=None, strict=False, maybe=False):
        for p in self.game.players:
            if player == p.position:
                if strict:
                    continue
                # When it is the player, assume fully tagged cards as clued too
                for c in p.hand:
                    card = self.game.deck[c]
                    if card.color == color and card.value == value:
                        return card.deckPosition
            elif p is self:
                for c in p.hand:
                    card = self.game.deck[c]
                    if card.color == color and card.value == value:
                        return card.deckPosition
                    if (maybe and card.maybeColor == color
                            and card.maybeValue == value):
                        return card.deckPosition
            else:
                for c in p.hand:
                    card = self.game.deck[c]
                    if (card.clued
                        and card.suit == color
                        and card.rank == value):
                        return card.deckPosition
        return None

    def isCluedSomewhere(self, color, value, player=None, strict=False,
                         maybe=False):
        return self.cluedCard(color, value, player, strict, maybe) is not None

    def maybeFixBeforeMisplay(self):
        if self.game.clueCount == 0:
            assert False

        # If a hand is near locked or is locked, maybe give a clue that can
        # free a hand up
        if self.game.clueCount == 1:
            for d in range(1, self.game.numPlayers):
                player = (self.position + d) % self.game.numPlayers
                hand = self.game.players[player].hand
                fullHand = True
                for h in hand:
                    card = self.game.deck[h]
                    if not card.clued:
                        fullHand = False

                if not fullHand:
                    continue

                for i, h in enumerate(hand):
                    card = self.game.deck[h]
                    if not self.isWorthless(card.suit, card.rank):
                        continue
                    if card.worthless is not None:
                        continue
                    for j in range(i):
                        jc = self.game.deck[h]
                        if card.suit == jc.suit and card.rank == jc.rank:
                            break
                    else:
                        continue
                    if card.value is None:
                        Hint(to=player, value=card.rank, fitness=1).give(self)
                        return True
                    if card.color is None:
                        Hint(to=player, color=card.suit, fitness=1).give(self)
                        return True

        return False

    def maybeEarlySaveCriticalCard(self, urgent):
        if self.game.clueCount == 0:
            assert False

        selfHandState = self.handState(self.position)

        if not urgent and HandState.Playable in selfHandState:
            return False

        if self.game.turnCount == 0:
            for i in range(1, self.game.numPlayers):
                player = (self.position + i) % self.game.numPlayers
                bestClue = self.bestEarlyHintForPlayer(player, False)
                if bestClue is not None:
                    if bestClue.color is not None:
                        return False
                    if bestClue.value == Value.V1:
                        if bestClue.fitness >= 60:
                            return False
        was1Clued = self.game.turnCount != 0
        hint = Hint()
        distance = range(1, self.game.numPlayers)
        if urgent:
            distance = range(1, 2)
        for i in distance:
            player = (self.position + i) % self.game.numPlayers
            hand = self.game.players[player].hand
            discard = self.discardSlot(self.handState(player))
            for v in [Value.V2, Value.V5]:
                tagged = []
                valueMDuplicate = 0
                valueDuplicate = 0
                valueUseless = 0
                numWasClued = 0
                for i, h in enumerate(hand):
                    card = self.game.deck[h]
                    if card.rank == v:
                        tagged.append(i)
                        if card.clued:
                            numWasClued += 1
                        if self.isWorthless(card.suit, card.rank):
                            valueUseless += 1
                        if self.locatedCount[card.suit][card.rank]:
                            valueDuplicate += 1
                        else:
                            for h in self.hand:
                                hcard = self.game.deck[h]
                                if (hcard.maybeColor == card.suit
                                        and hcard.maybeValue == card.rank):
                                    valueDuplicate += 1
                        if self.doesCardMatchHand(card.deckPosition):
                            valueMDuplicate += 1
                taggedDiscard = discard in tagged
                if not (urgent and taggedDiscard):
                    continue
                saveFitness = 0
                if (len(tagged) > numWasClued and valueDuplicate == 0
                        and valueMDuplicate == 0 and valueUseless == 0):
                    if v == Value.V2 and not was1Clued:
                        saveFitness = len(tagged) - numWasClued
                        saveFitness += taggedDiscard
                        saveFitness *= 2
                    else:
                        saveFitness = len(tagged) - numWasClued
                if saveFitness > 0 and saveFitness > hint.fitness:
                    hint.color = None
                    hint.value = v
                    hint.to = player
                    hint.fitness = saveFitness
        if hint.fitness > 0:
            hint.give(self)
            return True
        return False

    def maybeSaveCriticalCard(self, urgent):
        if self.game.clueCount == 0:
            assert False

        selfHandState = self.handState(self.position)

        if not urgent and HandState.Playable in selfHandState:
            return False

        distance = range(1, self.game.numPlayers)
        if urgent:
            distance = range(1, 2)
        for d in distance:
            player = (self.position + d) % self.game.numPlayers
            handState = self.handState(player)
            if HandState.Worthless in handState:
                continue
            if HandState.Critical in handState:
                critical = handState.index(HandState.Critical)
                if HandState.Unclued in handState:
                    unclued = handState.index(HandState.Unclued)
                    if unclued < critical:
                        continue
            elif HandState.Critical2 in handState:
                critical = handState.index(HandState.Critical2)
                if HandState.Unclued in handState:
                    unclued = handState.index(HandState.Unclued)
                    if unclued < critical:
                        continue
            elif HandState.Unclued in handState:
                critical = handState.index(HandState.Unclued)
            else:
                continue
            hand = self.game.players[player].hand
            card = self.game.deck[hand[critical]]
            valuable = self.isValuable(card.suit, card.rank)
            if not valuable and card.rank == 2 and self.is2Valuable(card.suit):
                if (self.game.numPlayers == 2
                        or self.doesCardMatchHand(hand[critical])):
                    valuable = None
            if valuable is False:
                continue

            valueTags = []
            colorTags = []

            for h in hand:
                hcard = self.game.deck[h]
                if hcard.suit & card.suit:
                    colorTags.append(hcard)
                if hcard.rank == card.rank:
                    valueTags.append(hcard)

            matchColors = self.matchCriticalCardValue(card.rank)
            matchValues = self.matchCriticalCardColor(card.suit)

            valueFitness = 0
            colorFitness = 0

            valueMDuplicate = 0
            valueDuplicate = 0
            valueClarify = 0
            valueUseless = 0
            valueNewTagged = 0
            valueNewSaves = 0
            valueOther = 0
            for i, tcard in enumerate(valueTags):
                if tcard.value is None:
                    valueNewTagged += 1
                    if self.isValuable(tcard.suit, tcard.rank):
                        valueNewSaves += 1
                    else:
                        valueOther += 1
                    if tcard.color is not None:
                        valueClarify += 1
                if self.isWorthless(tcard.suit, tcard.rank):
                    valueUseless += 1
                if self.locatedCount[tcard.suit][tcard.rank]:
                    valueDuplicate += 1
                else:
                    for h in self.hand:
                        hcard = self.game.deck[h]
                        if (hcard.maybeColor == tcard.suit
                                and hcard.maybeValue == tcard.rank):
                            valueDuplicate += 1
                if self.doesCardMatchHand(tcard.deckPosition):
                    valueMDuplicate += 1

                for j in range(i):
                    if (tcard.suit == valueTags[j].suit
                            and tcard.rank == valueTags[j].rank):
                        valueDuplicate += 1
            if card.rank == Value.V5:
                valueFitness += valueNewTagged * 21
            elif card.rank == Value.V2:
                if not (valuable is True
                        or (valueDuplicate == 0 and valueUseless == 0)):
                    # 2 save is not viable because it is not a valid complete
                    # save or it is tagging a duplicate
                    return False
                valueFitness += valueNewSaves * 21 + valueOther * 21
                valueFitness += valueClarify - len(matchColors)
            elif valueDuplicate == 0 and valueUseless == 0:
                valueFitness += valueNewSaves * 20 + valueOther * 3
                valueFitness -= valueMDuplicate * 20
                valueFitness += valueClarify - len(matchColors)

            colorMDuplicate = 0
            colorDuplicate = 0
            colorClarify = 0
            colorUseless = 0
            colorNewTagged = 0
            colorNewSaves = 0
            colorOther = 0
            colorSave5 = 0
            isSave5NextToDiscard = False
            for i, tcard in enumerate(colorTags):
                if tcard.color is None:
                    colorNewTagged += 1
                    if self.isValuable(tcard.suit, tcard.rank):
                        colorNewSaves += 1
                    else:
                        colorOther += 1
                    if tcard.value is not None:
                        colorClarify += 1
                    if tcard.rank == Value.V5:
                        colorSave5 += 1
                if self.isWorthless(tcard.suit, tcard.rank):
                    colorUseless += 1
                if self.locatedCount[tcard.suit][tcard.rank]:
                    colorDuplicate += 1
                for j in range(i):
                    if (tcard.suit == colorTags[j].suit
                            and tcard.rank == colorTags[j].rank):
                        colorDuplicate += 1
                if self.doesCardMatchHand(tcard.deckPosition):
                    colorMDuplicate += 1
            if colorSave5 and critical + 1 < len(hand):
                nextCard = self.game.deck[hand[critical + 1]]
                isSave5NextToDiscard = (nextCard.suit == card.suit
                                        and nextCard.rank == Value.V5)
            if colorDuplicate == 0 and colorUseless == 0 and valuable is True:
                if not (card.rank == Value.V5 and colorNewSaves):
                    colorFitness = colorNewSaves * 20 + colorOther * 3
                    colorFitness += (colorSave5 + isSave5NextToDiscard) * 10
                    colorFitness -= colorMDuplicate * 20
                    colorFitness -= len(matchValues)

            hint = Hint()
            hint.to = player
            if valueFitness > 0 and valueFitness >= colorFitness:
                hint.value = card.rank
                hint.color = None
                hint.fitness = valueFitness
            elif colorFitness > 0 and colorFitness > valueFitness:
                hint.value = None
                hint.color = card.suit
                hint.fitness = colorFitness
            else:
                # Find Worthless clue
                valueWorthlessHint = None
                colorWorthlessHint = None
                valueWorthlessFitness = None
                colorWorthlessFitness = None

                for v in self.values[:self.lowestPlayableValue-1]:
                    fitness = 0
                    for h in hand:
                        hcard = self.game.deck[h]
                        if hcard.rank == v:
                            fitness += 1
                    if fitness <= 0:
                        continue
                    if (valueWorthlessFitness is None
                            or fitness > valueWorthlessFitness):
                        valueWorthlessHint = v
                        valueWorthlessFitness = fitness
                for c in self.colors:
                    fitness = 0
                    if not self.colorComplete[c]:
                        continue
                    for h in hand:
                        hcard = self.game.deck[h]
                        if hcard.suit & c:
                            fitness += 1
                    if fitness <= 0:
                        continue
                    if (colorWorthlessFitness is None
                            or fitness > colorWorthlessFitness):
                        colorWorthlessHint = c
                        colorWorthlessFitness = fitness

                useValue = (valueWorthlessFitness is not None
                            and (colorWorthlessFitness is None
                                 or valueWorthlessFitness
                                      >= colorWorthlessFitness))
                useColor = (colorWorthlessFitness is not None
                            and (valueWorthlessFitness is None
                                 or valueWorthlessFitness
                                      < colorWorthlessFitness))
                if useColor and useValue:
                    assert False
                elif useColor:
                    hint.value = None
                    hint.color = colorWorthlessHint
                    hint.fitness = colorWorthlessFitness
                elif useValue:
                    hint.value = valueWorthlessHint
                    hint.color = None
                    hint.fitness = valueWorthlessFitness
                else:
                    valueBadFitness = valueDuplicate + valueUseless
                    colorBadFitness = colorDuplicate + colorUseless
                    if colorBadFitness <= valueBadFitness:
                        hint.value = None
                        hint.color = card.suit
                        hint.fitness = colorBadFitness
                    else:
                        hint.value = card.rank
                        hint.color = None
                        hint.fitness = valueBadFitness

            if urgent and HandState.Playable not in handState:
                playHint = self.bestHintForPlayer(player)
                if playHint is not None and self.game.clueCount >= 2:
                    hint = playHint
                hint.give(self)
                return True
        return False

    def maybeDiscardForCriticalCard(self):
        if self.game.clueCount == 8:
            assert False

        if self.game.clueCount != 0:
            return False

        # Don't bother for 2 player games, the hand might end up locked
        if self.game.numPlayers < 3:
            return False

        handState = self.handState(self.position)
        discard = self.discardSlot(handState)
        if discard is None:
            return None

        # First check adjacent player
        nextPlayer = (self.position + 1) % self.game.numPlayers
        handStateN = self.handState(nextPlayer)
        discardN = self.discardSlot(handStateN)
        maybeDiscard = (HandState.Playable not in handStateN
                        and HandState.Playable not in handStateN
                        and discardN is not None)
        if maybeDiscard:
            hand = self.game.players[nextPlayer].hand
            cardN = self.game.deck[hand[discardN]]
            if self.isValuable(cardN.suit, cardN.rank):
                self.discard_card(discard)
                return True

        distance = range(2, self.game.numPlayers)
        if HandState.Playable in handState:
            distance = range(2, 3)

        for d in distance:
            target = (self.position + d) % self.game.numPlayers

            handStateT = self.handState(target)
            discardT = self.discardSlot(handStateT)

            if HandState.Playable in handStateN:
                continue
            if HandState.Worthless not in handStateN:
                continue
            if discardT is None:
                continue

            targetHand = self.game.players[target].hand
            cardT = self.game.deck[targetHand[discardT]]
            if not self.isValuable(cardT.suit, cardT.rank):
                continue

            for c in range(1, d):
                between = (self.position + c) % self.game.numPlayers
                handStateB = self.handState(between)
                discardB = self.discardSlot(handStateB)
                needToDiscard = not (HandState.Playable in handStateB
                                     or HandState.Worthless in handStateB)
                if needToDiscard and discardB is not None:
                    betweenHand = self.game.players[between].hand
                    cardB = self.game.deck[betweenHand[discardB]]
                    if not self.isValuable(cardB.suit, cardB.rank):
                        needToDiscard = False
                if needToDiscard:
                    self.discard_card(discard)
                    return True
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
        nextToPlay = len(self.game.playedCards[color]) + 1
        for v in self.values[nextToPlay-1:self.maxPlayValue[color]]:
            if self.isCluedSomewhere(color, v, player, strict=True,
                                     maybe=True):
                continue
            nextToPlay = v
            break
        isNewestGood = None
        needFix = False
        numPlay, numWorthless, maybeDuplicate = 0, 0, 0
        for v in self.values[nextToPlay-1:self.maxPlayValue[color]]:
            if not tagged:
                break
            if self.isCluedSomewhere(color, v, player, strict=True,
                                     maybe=True):
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
                    if card.rank == nextToPlay:
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
                    if v == nextToPlay:
                        isNewestGood = card.rank == nextToPlay
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
        for deckIdx, value in values:
            if self.doesCardMatchHand(deckIdx):
                maybeDuplicate += 1
        return (values, numPlay, numWorthless, maybeDuplicate, isNewestGood,
                needFix)

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
        (playOrder, numPlay, numWorthless, maybeDuplicate, isNewestGood,
         needFix
         ) = self.valueOrderFromColor(color, tagged, player)

        fixPlayer, fixColor, fixValue = None, None, None
        if needFix:
            for tagV in self.values:
                # Test Fix Clues
                (playOrder_, numPlay_, numWorthless_, maybeDuplicate_,
                 isNewestGood_, needFix_
                 ) = self.valueOrderFromColor(color, tagged, player,
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
                 maybeDuplicate_, needFix_
                 ) = self.valueOrderFromColor(color, tagged, player,
                                              otherPlayer=p,
                                              otherValue=tagV)

                if not needFix_:
                    fixPlayer = player
                    fixColor = None
                    if fixValue is None:
                        fixValue = []
                    fixValue.append(tagV)
        return (playOrder,
                numPlay, numWorthless, maybeDuplicate, isNewestGood,
                needFix, numNewTagged, badClarify,
                fixPlayer, fixColor, fixValue)

    def playOrderValueClue(self, player, value):
        assert player != self.position
        numNewTagged = 0
        tagged = []
        hand = self.game.players[player].hand
        for h in reversed(hand):
            card = self.game.deck[h]
            if card.rank == value:
                if card.value is None:
                    numNewTagged += 1
                tagged.append(h)
        playColors = []
        futureColors = []
        for c in self.colors:
            if self.colorComplete[c]:
                continue
            if self.isCluedSomewhere(c, value, self.position, maybe=True):
                deckIdx = self.cluedCard(c, value, self.position, maybe=True)
                card = self.game.deck[deckIdx]
                if deckIdx not in tagged or not card.cluedAsDiscard:
                    continue
            scoreTagged = len(self.game.playedCards[c])
            for v in self.values[scoreTagged:self.maxPlayValue[c]]:
                if self.isCluedSomewhere(c, v, self.position, maybe=True):
                    deckIdx = self.cluedCard(c, v, self.position)
                    card = self.game.deck[deckIdx]
                    if deckIdx in tagged and card.cluedAsDiscard:
                        break
                    scoreTagged = v
                else:
                    break
            if scoreTagged > value:
                continue
            if scoreTagged == value - 1:
                playColors.append(c)
            elif scoreTagged < value - 1:
                futureColors.append(c)
        neededColors = playColors + futureColors
        playOrder = []
        futureOrder = []
        worthlessOrder = []
        colorUsed = []
        numPlay, numFuture, numWorthless, maybeDuplicate = 0, 0, 0, 0
        numPlayMismatch = 0
        numFutureMismatch = 0
        numCompleteMismatch = 0
        # Check fully tagged cards first
        for t in tagged:
            card = self.game.deck[t]
            if self.doesCardMatchHand(t):
                maybeDuplicate += 1
            color = card.maybeColor
            if color is not None:
                if color in playColors:
                    playOrder.append((t, [color]))
                    playColors.remove(color)
                    neededColors.remove(color)
                    colorUsed.append(color)
                    tagged.remove(t)
                    if card.value is None:
                        numPlay += 1
                elif color in futureColors:
                    futureOrder.append((t, [color]))
                    futureColors.remove(color)
                    neededColors.remove(color)
                    colorUsed.append(color)
                    tagged.remove(t)
                    if card.value is None:
                        numFuture += 1
                else:
                    worthlessOrder.append((t, None))
                    if card.value is None:
                        numWorthless += 1
        for i, t in enumerate(tagged):
            card = self.game.deck[t]
            if i < len(playColors):
                playOrder.append((t, playColors))
                if card.suit in playColors and card.suit not in colorUsed:
                    if card.value is None:
                        numPlay += 1
                    colorUsed.append(card.suit)
                else:
                    numPlayMismatch += 1
                if card.suit not in neededColors:
                    numCompleteMismatch += 1
            elif i < len(playColors) + len(futureColors):
                futureOrder.append((t, futureColors))
                if card.suit in futureColors and card.suit not in colorUsed:
                    if card.value is None:
                        numFuture += 1
                    colorUsed.append(card.suit)
                else:
                    numFutureMismatch += 1
                if card.suit not in neededColors:
                    numCompleteMismatch += 1
            else:
                worthlessOrder.append((t, None))
                if card.value is None:
                    numWorthless += 1

        return (playOrder + futureOrder + worthlessOrder,
                numPlay, numFuture, numWorthless, maybeDuplicate,
                numPlayMismatch, numFutureMismatch, numCompleteMismatch,
                numNewTagged)

    def doesCardMatchHand(self, deckIdx):
        deckCard = self.game.deck[deckIdx]
        assert deckCard.suit is not None
        assert deckCard.rank is not None
        if self.colorComplete[deckCard.suit]:
            return False
        if deckCard.rank == Value.V5:
            return False
        for h in self.hand:
            card = self.game.deck[h]
            if not card.clued:
                continue
            if card.worthless or card.playWorthless:
                continue
            if card.cantBe[deckCard.suit][deckCard.rank]:
                continue
            if card.color is not None and card.value is not None:
                continue
            if card.color == deckCard.suit:
                maybeValue = card.maybeValue
                if maybeValue is not None:
                    if maybeValue == deckCard.rank:
                        return True
                    continue
                if deckCard.rank in card.possibleValues:
                    return True
            if card.value == deckCard.rank:
                maybeColor = card.maybeColor
                if maybeColor is not None:
                    if maybeColor == deckCard.suit:
                        return True
                    continue
                if deckCard.suit in card.possibleColors:
                    return True
        return False

    def bestEarlyHintForPlayer(self, player, highValue):
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

        handState = self.handState(player)
        discard = self.discardSlot(handState)

        numClued = 0
        for h in hand:
            card = self.game.deck[h]
            if card.clued:
                numClued += 1

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
            (values, numPlay, numWorthless, maybeDuplicate, isNewestGood,
             needFix, numNewTagged, badClarify,
             fixPlayer, fixColor, fixValue
             ) = self.playOrderColorClue(player, c)
            goodTag = numNewTagged - badClarify - numWorthless
            if (not needFix and isNewestGood and values[0][1] is not None
                and maybeDuplicate == 0
                and goodTag > 0):
                baseValue, baseSave = 22, 11
                colorFitness = (numPlay * (baseValue + 6 - (values[0][1]))
                                + numWorthless)

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

            looksLikeSave = False
            if HandState.Worthless not in handState and discard in tagged:
                saveColors = self.matchCriticalCardValue(v)
                looksLikeSave = bool(saveColors) and v != Value.V5

            valueFitness = 0

            # Decision Here
            if v < self.lowestPlayableValue:
                pass
            else:
                (playOrder, numPlay, numFuture, numWorthless, maybeDuplicate,
                 numPlayMismatch, numFutureMismatch, numCompleteMismatch,
                 numNewTagged
                 ) = self.playOrderValueClue(player, v)
                if (numNewTagged >= 1 and numPlay >= 1
                        and maybeDuplicate == 0
                        and numPlayMismatch == 0
                        and numFutureMismatch == 0
                        and numCompleteMismatch == 0):
                    baseValue, baseFuture, baseSave = 20, 5, 20
                    valueFitness = (numPlay * (baseValue + 6 - v)
                                    + numFuture * baseFuture
                                    + numWorthless - looksLikeSave * baseSave)

            if valueFitness > best_so_far.fitness:
                best_so_far.fitness = valueFitness
                best_so_far.color = None
                best_so_far.value = v

        if best_so_far.fitness == 0:
            return None
        if highValue and best_so_far.fitness < 28:
            return None
        return best_so_far

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

        handState = self.handState(player)
        discard = self.discardSlot(handState)

        numClued = 0
        for h in hand:
            card = self.game.deck[h]
            if card.clued:
                numClued += 1

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

            looksLikeSave = False
            if HandState.Worthless not in handState and discard in tagged:
                saveValues = self.matchCriticalCardColor(c)
                looksLikeSave = bool(saveValues)

            colorFitness = 0

            # Decision Here
            (values, numPlay, numWorthless, maybeDuplicate, isNewestGood,
             needFix, numNewTagged, badClarify,
             fixPlayer, fixColor, fixValue
             ) = self.playOrderColorClue(player, c)
            goodTag = numNewTagged - badClarify - numWorthless
            needToPlay = self.maxPlayValue[c] - len(self.game.playedCards[c])
            if (not needFix and isNewestGood and values[0][1] is not None
                and maybeDuplicate == 0
                and goodTag > 0):
                baseValue, baseSave = 22, 11
                colorFitness = (numPlay * baseValue
                                + numWorthless
                                - looksLikeSave * baseSave)
                if numClued + numNewTagged == len(hand) and looksLikeSave:
                    colorFitness -= 22

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

            looksLikeSave = False
            if HandState.Worthless not in handState and discard in tagged:
                saveColors = self.matchCriticalCardValue(v)
                looksLikeSave = bool(saveColors) or v == Value.V5

            valueFitness = 0

            # Decision Here
            if v < self.lowestPlayableValue:
                pass
            else:
                (playOrder, numPlay, numFuture, numWorthless, maybeDuplicate,
                 numPlayMismatch, numFutureMismatch, numCompleteMismatch,
                 numNewTagged
                 ) = self.playOrderValueClue(player, v)
                if (numNewTagged >= 1 and numPlay >= 1
                        and maybeDuplicate == 0
                        and numPlayMismatch == 0
                        and numFutureMismatch == 0
                        and numCompleteMismatch == 0):
                    baseValue, baseFuture, baseSave = 20, 7, 20
                    if v == Value.V5:
                        baseValue, baseFuture, baseSave = 7, 2, 7
                    valueFitness = (numPlay * baseValue
                                    + numFuture * baseFuture
                                    + numWorthless
                                    - baseSave * looksLikeSave)
                if numClued + numNewTagged == len(hand) and looksLikeSave:
                    valueFitness -= 20

            if valueFitness > best_so_far.fitness:
                best_so_far.fitness = valueFitness
                best_so_far.color = None
                best_so_far.value = v

        if best_so_far.fitness == 0:
            return None
        return best_so_far

    def bestCardToPlay(self):
        handState = self.handState(self.position)
        for i, hs in reversed(list(enumerate(handState))):
            if hs == HandState.Playable:
                return i
        return None

    def maybePlayCard(self):
        best_index = self.bestCardToPlay()
        if best_index is not None:
            self.play_card(best_index)
            return True
        return False

    def maybeGiveEarlyGameHint(self, highValue):
        bestHint = Hint()
        for i in range(1, self.game.numPlayers):
            player = (self.position + i) % self.game.numPlayers
            candidate = self.bestEarlyHintForPlayer(player, highValue)
            if candidate is not None and candidate.fitness >= 0:
                handState = self.handState(player)
                if HandState.Playable not in handState:
                    candidate.fitness += (self.game.numPlayers - i) * 2
            if candidate is not None and candidate.fitness > bestHint.fitness:
                bestHint = candidate
        if bestHint.fitness <= 0:
            return False

        bestHint.give(self)
        return True

    def maybeGiveHelpfulHint(self):
        if self.game.clueCount == 0:
            assert False

        bestHint = Hint()
        for i in range(1, self.game.numPlayers):
            player = (self.position + i) % self.game.numPlayers
            candidate = self.bestHintForPlayer(player)
            if candidate is not None and candidate.fitness >= 0:
                handState = self.handState(player)
                if HandState.Playable not in handState:
                    candidate.fitness += (self.game.numPlayers - i) * 2
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
        handState = self.handState(self.position)
        discard = self.discardSlot(handState)
        if discard is not None:
            self.discard_card(discard)
            return True
        return False

    def discardSomeCard(self):
        best_index = 0
        for i in range(len(self.hand)):
            card = self.game.deck[self.hand[i]]
            bestCard = self.game.deck[self.hand[best_index]]
            if bestCard.maybeValue is None:
                best_index = i
            elif (card.maybeValue is not None
                    and card.maybeValue > bestCard.maybeValue):
                best_index = i
        self.discard_card(best_index)
        return True

    def reevaluateClue(self, clues, to):
        for clueState in clues:
            if clueState.value is not None:
                critical = clueState.critical
                possibleColors = clueState.playColors[:]
                laterColors = clueState.laterColors[:]
                criticalColors = clueState.discardColors[:]
                newestIndex = None
                for i in reversed(clueState.indexes):
                    if not clueState.wasClued[i]:
                        newestIndex = i
                        break
                newestCard = None
                if newestIndex is not None:
                    newestCard = self.game.deck[clueState.hand[newestIndex]]
                for c in self.colors:
                    played = self.playedCount[c][clueState.value]
                    held = self.eyesightCount[c][clueState.value]
                    score = len(self.game.playedCards[c])
                    cantBe = played + held == clueState.value.num_copies
                    cantBe = cantBe or score >= clueState.value
                    if newestCard is not None:
                        v = clueState.value
                        cantBe = cantBe or newestCard.cantBe[c][v]
                    cantBe = cantBe or self.isCluedSomewhere(
                        c, clueState.value, to)
                    if cantBe:
                        if c in possibleColors:
                            possibleColors.remove(c)
                        if c in laterColors:
                            laterColors.remove(c)
                        if c in criticalColors:
                            criticalColors.remove(c)
                numAllColors = len(possibleColors) + len(laterColors)
                if critical:
                    discardCard = self.game.deck[clueState.discardIndex]
                    for c in criticalColors[:]:
                        if discardCard.cannotBeColor(c):
                            criticalColors.remove(c)
                for h in reversed(clueState.indexes):
                    card = self.game.deck[clueState.hand[h]]
                    if card.state != CardState.Hand:
                        continue
                    clueIndex = (len(clueState.indexes)
                                 - clueState.indexes.index(h) - 1)
                    if card.color is not None:
                        score = len(self.game.playedCards[card.color])
                        playingValue = score + 1
                        if card.value == playingValue:
                            card.setIsPlayable(True)
                        elif card.value <= playingValue:
                            card.setIsWorthless(True)
                    elif clueState.value < self.lowestPlayableValue:
                        card.setIsWorthless(True)
                    else:
                        card.discardColors.clear()
                        card.playColors.clear()
                        if card.color is None:
                            if clueIndex < len(possibleColors):
                                for c in possibleColors:
                                    if card.cannotBeColor(c):
                                        continue
                                    card.playColors.append(c)
                                card.playColorDirect = True
                            if clueIndex < numAllColors or not card.playColors:
                                for c in laterColors:
                                    if card.cannotBeColor(c):
                                        continue
                                    card.playColors.append(c)
                            if (clueIndex >= numAllColors
                                    or not card.playColors):
                                card.playWorthless = True
                for h in clueState.indexes:
                    card = self.game.deck[clueState.hand[h]]
                    if card.state != CardState.Hand:
                        continue
                    if critical or critical is None:
                        if not clueState.wasClued[h]:
                            card.cluedAsDiscard = True
                            for c in criticalColors:
                                if card.cannotBeColor(c):
                                    continue
                                card.discardColors.append(c)
                            card.playColors.clear()
                            card.setIsValuable(True, strict=False)
                            if not card.discardColors:
                                card.cluedAsDiscard = False
                                card.playWorthless = True
                            if (critical and criticalColors
                                    and clueState.value != 5):
                                if len(criticalColors) == 1:
                                    color = criticalColors[0]
                                    criticalColors.clear()
                                    for c in chain(possibleColors,
                                                   laterColors):
                                        if c != color:
                                            criticalColors.append(c)
                                else:
                                    for c in chain(possibleColors,
                                                   laterColors):
                                        if c not in criticalColors:
                                            criticalColors.append(c)
                                critical = None
                    elif len(clueState.indexes) == 1:
                        if card.color is None:
                            card.cluedAsPlay = True
                        else:
                            for h in clueState.hand:
                                taggedCard = self.game.deck[h]
                                if taggedCard.color == card.color:
                                    taggedCard.cluedAsPlay = True
                                    taggedCard.valuable = None
                                    taggedCard.discardValues.clear()
                    else:
                        card.cluedAsPlay = True

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
            score = len(self.game.playedCards[c])
            for v in self.values[score:]:
                if not tagged:
                    break
                if self.isCluedSomewhere(c, v, player):
                    continue
                for t in tagged[:]:
                    card = self.game.deck[t]
                    if card.valuable:
                        continue
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
                if card.valuable:
                    continue
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
                    knol.update(p == self.position)
                    if (knol.clued and knol.color is None
                            and knol.value is not None
                            and not knol.playColors
                            and not knol.discardColors
                            and not (knol.playWorthless or knol.worthless)):
                        clues = []
                        for clueState in self.clueLog[p]:
                            if knol.deckPosition not in clueState.hand:
                                continue
                            i = clueState.hand.index(knol.deckPosition)
                            if i not in clueState.indexes:
                                continue
                            clues.append(clueState)
                        self.reevaluateClue(clues, p)
                        done = False
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
        card.state = CardState.Discard
        self.seePublicCard(card.suit, card.rank)

    def pleaseObserveBeforePlay(self, from_, card_index, deckIdx):
        card = self.game.deck[deckIdx]
        card.state = CardState.Play
        self.seePublicCard(card.suit, card.rank)

    def matchCriticalCardColor(self, color):
        if self.colorComplete[color]:
            return []
        # Not saving 5's with a color clue
        score = len(self.game.playedCards[color])
        if len(self.game.playedCards[color]) >= 4:
            return []
        possibleValues = []
        for v in self.values[score:self.maxPlayValue[color]]:
            if v.num_copies == 1:
                continue
            if self.discardCount[color][v] == v.num_copies - 1:
                if self.isCluedSomewhere(color, v):
                    continue
                if self.locatedCount[color][v]:
                    continue
                possibleValues.append(v)
        return possibleValues

    def matchCriticalCardValue(self, value):
        if value == Value.V5:
            possibleColors = []
            for c in self.colors:
                if self.playedCount[c][value] or self.locatedCount[c][value]:
                    continue
                if not self.isUseful(c, value):
                    continue
                possibleColors.append(c)
            return possibleColors
        # 2 saves maybe
        if value == Value.V2:
            possibleColors = []
            for c in self.colors:
                if self.playedCount[c][2] or self.locatedCount[c][2]:
                    continue
                if not self.is2Valuable(c):
                    continue
                possibleColors.append(c)
            return possibleColors
        if value < self.lowestPlayableValue:
            return []
        possibleColors = []
        for c in self.colors:
            if self.colorComplete[c]:
                continue
            if not self.isUseful(c, value):
                continue
            score = len(self.game.playedCards[c])
            if len(self.game.playedCards[c]) >= 4:
                continue
            if score > value:
                continue
            if self.discardCount[c][value] == value.num_copies - 1:
                if self.isCluedSomewhere(c, value):
                    continue
                if self.locatedCount[c][value]:
                    continue
                possibleColors.append(c)
        return possibleColors

    def pleaseObserveColorHint(self, from_, to, color, card_indices):
        hand = self.game.players[to].hand
        score = len(self.game.playedCards[color])
        handState = self.handState(to)
        discard = self.discardSlot(handState)

        possibleValues = []
        for v in self.values[score:self.maxPlayValue[color]]:
            if self.isCluedSomewhere(color, v, to):
                continue
            match = False
            for i in card_indices:
                card = self.game.deck[hand[i]]
                if card.value == v:
                    match = True
                    break
            if match:
                continue
            possibleValues.append(v)

        numToComplete = self.maxPlayValue[color] - score
        criticalValues = self.matchCriticalCardColor(color)
        criticalClue = (HandState.Worthless not in handState
                            and discard in card_indices)
        if HandState.Worthless not in handState and discard in card_indices:
            criticalClue = bool(criticalValues
                                and numToComplete > len(card_indices))
        criticalState = criticalClue

        wasClued = [None] * len(hand)
        for i, h in reversed(list(enumerate(hand))):
            knol = self.game.deck[hand[i]]
            if i in card_indices:
                wasClued[i] = knol.clued
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
            else:
                knol.setCannotBeColor(color)
        for i, h in enumerate(hand):
            knol = self.game.deck[h]
            if i in card_indices:
                if criticalState or criticalState is None:
                    if not wasClued[i]:
                        knol.cluedAsDiscard = True
                        for v in criticalValues:
                            if knol.cannotBeValue(v):
                                continue
                            knol.discardValues.append(v)
                        knol.playValue = None
                        knol.setIsValuable(True, strict=False)
                        if criticalState:
                            if len(criticalValues) == 1:
                                value = criticalValues[0]
                                criticalValues.clear()
                                for v in possibleValues:
                                    if v != value:
                                        criticalValues.append(v)
                            else:
                                for v in possibleValues:
                                    if v not in criticalValues:
                                        criticalValues.append(v)
                            criticalState = None
                else:
                    knol.cluedAsPlay = True
        for h in hand:
            knol = self.game.deck[h]
            knol.update(False)

        clueLog = ClueState(self.game.turnCount, criticalClue,
                            hand[:], card_indices[:], wasClued[:],
                            discard, HandState.Worthless in handState,
                            color=color, discard_values=criticalValues[:])
        self.clueLog[to].append(clueLog)

    def pleaseObserveValueHint(self, from_, to, value, card_indices):
        hand = self.game.players[to].hand
        possibleColors = []
        laterColors = []
        newestCard = self.game.deck[hand[card_indices[-1]]]
        for c in self.colors:
            if self.isCluedSomewhere(c, value, to, maybe=True):
                continue
            if newestCard.cantBe[c][value]:
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
            if score >= value:
                continue
            if score < value - 1:
                for v in self.values[score:value-1]:
                    if not self.isCluedSomewhere(c, v, to, maybe=True):
                        laterColors.append(c)
                        break
                else:
                    possibleColors.append(c)
            else:
                possibleColors.append(c)
        handState = self.handState(to)
        discard = self.discardSlot(handState)

        criticalColors = self.matchCriticalCardValue(value)
        criticalClue = ((HandState.Worthless not in handState
                         and discard in card_indices)
                        or value == Value.V5)
        if criticalClue and discard is not None:
            discardCard = self.game.deck[hand[discard]]
            for c in criticalColors:
                if not discardCard.cannotBeColor(c):
                    criticalClue = True
                    break
            else:
                criticalClue = False
        criticalState = criticalClue

        numAllColors = len(possibleColors) + len(laterColors)
        wasClued = [None] * len(hand)
        for i, h in reversed(list(enumerate(hand))):
            knol = self.game.deck[h]
            if i in card_indices:
                wasClued[i] = knol.clued
                clueIndex = len(card_indices) - card_indices.index(i) - 1
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
                    knol.discardColors.clear()
                    knol.playColors.clear()
                    if knol.color is None:
                        if clueIndex < len(possibleColors):
                            for c in possibleColors:
                                if knol.cannotBeColor(c):
                                    continue
                                knol.playColors.append(c)
                            knol.playColorDirect = True
                        elif clueIndex < numAllColors:
                            for c in laterColors:
                                if knol.cannotBeColor(c):
                                    continue
                                knol.playColors.append(c)
                        else:
                            knol.playWorthless = True
            else:
                knol.setCannotBeValue(value)
        for i, h in enumerate(hand):
            knol = self.game.deck[h]
            if i in card_indices:
                if criticalState or criticalState is None:
                    if not wasClued[i]:
                        knol.cluedAsDiscard = True
                        for c in criticalColors:
                            if knol.cannotBeColor(c):
                                continue
                            knol.discardColors.append(c)
                        knol.playColors.clear()
                        knol.setIsValuable(True, strict=False)
                        if criticalState and value != 5:
                            if len(criticalColors) == 1:
                                color = criticalColors[0]
                                criticalColors.clear()
                                for c in chain(possibleColors, laterColors):
                                    if c != color:
                                        criticalColors.append(c)
                            else:
                                for c in chain(possibleColors, laterColors):
                                    if c not in criticalColors:
                                        criticalColors.append(c)
                            criticalState = None
                elif len(card_indices) == 1:
                    if knol.color is None:
                        knol.cluedAsPlay = True
                    else:
                        for h in hand:
                            taggedCard = self.game.deck[h]
                            if taggedCard.color == knol.color:
                                taggedCard.cluedAsPlay = True
                                taggedCard.valuable = None
                                taggedCard.discardValues.clear()
                else:
                    knol.cluedAsPlay = True
        for h in hand:
            knol = self.game.deck[h]
            knol.update(False)

        clueLog = ClueState(self.game.turnCount, criticalClue,
                            hand[:], card_indices[:], wasClued[:],
                            discard, HandState.Worthless in handState,
                            value=value,
                            play_colors=possibleColors[:],
                            later_colors=laterColors[:],
                            discard_color=criticalColors[:])
        self.clueLog[to].append(clueLog)

    def pleaseObserveAfterMove(self):
        pass

    def pleaseMakeMove(self, can_clue, can_discard):
        assert self.game.currentPlayer == self.position

        stage = self.game_stage()
        if stage == GameStage.Early:
            if can_clue and self.maybeEarlySaveCriticalCard(True):
                return
            if can_clue and self.maybeGiveEarlyGameHint(True):
                return
            if self.maybePlayCard():
                return
            if can_clue and self.maybeGiveEarlyGameHint(False):
                return
            if can_clue and self.maybeEarlySaveCriticalCard(False):
                return
        else:
            if can_clue and self.maybeFixBeforeMisplay():
                return
            if can_clue and self.maybeSaveCriticalCard(True):
                return
            if can_discard and self.maybeDiscardForCriticalCard():
                return
            if self.maybePlayCard():
                return
            if can_clue and self.maybeGiveHelpfulHint():
                return
            if can_clue and self.maybeSaveCriticalCard(False):
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
