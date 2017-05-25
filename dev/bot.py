import time

import game

from enum import Enum, auto
from itertools import chain
from typing import ClassVar, Dict, Iterable, List, Optional, Set, Tuple, Union
from typing import cast

from bot import bot
from bot.card import Card
from bot.player import Player
from enums import Color, Value, Variant
from .card_knowledge import CardKnowledge, CardState
from .clue_info import ClueState
from .hint import Hint


class GameStage(Enum):
    '''State of the game'''
    Early = auto()
    Mid = auto()
    End = auto()


class HandState(Enum):
    '''State of the card in someone's hand'''
    Unclued = auto()
    Critical = auto()
    '''Critical card that is very valuable'''
    Critical2 = auto()
    '''Value 2 card that is on chop'''
    SoonPlay = auto()
    Playable = auto()
    Worthless = auto()
    Saved = auto()


cluePlayWeight = {
    Value.V1: 3,
    Value.V2: 5,
    Value.V3: 2,
    Value.V4: 1,
    Value.V5: 0,
    }
'''Weight of the values of clues that on cards that are now playable'''
clueFutureWeight = {
    Value.V1: 0,
    Value.V2: 2,
    Value.V3: 0,
    Value.V4: 0,
    Value.V5: 0,
    }
'''Weight of the values of clues that can infer cards in the future'''

class Bot(bot.Bot):
    '''
    Dev Bot
    '''
    BOT_NAME: ClassVar[str] = 'Dev Bot'

    waitTime: float
    '''Time to sleep before making a move, helps keldon UI to load properly for
    humans'''
    colors: List[Color]
    '''Valid colors for the game mode'''
    values: List[Value]
    '''Valid values for the game mode'''
    nextPlayValue: Dict[Color, int]
    '''Next playable value for the color pile'''
    maxPlayValue: Dict[Color, int]
    '''Maximum playable value for the color pile'''
    colorComplete: Dict[Color, bool]
    '''True if the color pile is completed (implies the pile has no more
     playable cards)'''
    playedCount: Dict[Color, List[int]]
    '''Count cards have been played/discarded
    First index is the color, second index is the value, value is a count'''
    discardCount: Dict[Color, List[int]]
    '''Count cards have been discarded
    First index is the color, second index is the value, value is a count'''
    locatedCount: Dict[Color, List[int]]
    '''Count cards in players' hands are definitely identified
    First index is the color, second index is the value, value is a count'''
    eyesightCount: Dict[Color, List[int]]
    '''Count cards in players' hands are visible to me in particular
    First index is the color, second index is the value, value is a count'''
    lowestPlayableValue: int
    '''Lowest-value card currently playable'''
    clueLog: List[List[ClueState]]
    '''Logs all the clues given to players from players
    Index is the from player'''

    def __init__(self,
                 gameObj: 'game.Game',
                 position: int,
                 name: str, *,
                 wait: float=0, **kwargs) -> None:
        if gameObj.variant != Variant.NoVariant:
            raise ValueError()

        super().__init__(gameObj, position, name, **kwargs)
        self.waitTime = float(wait)
        self.colors = list(gameObj.variant.pile_colors)
        self.values = list(Value)  # type: ignore

        numListValues: int = int(max(self.values) + 1)
        self.nextPlayValue = {c: 0 * numListValues for c in self.colors}
        self.maxPlayValue = {c: 0 * numListValues for c in self.colors}
        self.colorComplete = {c: False for c in self.colors}
        self.playedCount = {c: [0] * numListValues for c in self.colors}
        self.discardCount = {c: [0] * numListValues for c in self.colors}
        self.locatedCount = {c: [0] * numListValues for c in self.colors}
        self.eyesightCount = {c: [0] * numListValues for c in self.colors}
        self.lowestPlayableValue = 0
        self.clueLog = [[] for p in range(self.game.numPlayers)]

    def create_player_card(self,
                           player: int,
                           deckPosition: int,
                           color: Optional[Color],
                           value: Optional[Value]) -> CardKnowledge:
        return CardKnowledge(self, player, deckPosition, color, value)

    def next_turn(self, player: int) -> None:
        self.pleaseObserveBeforeMove()

    def someone_discard(self,
                        player: int,
                        deckIdx: int,
                        position: int) -> None:
        self.pleaseObserveBeforeDiscard(player, position, deckIdx)

    def card_discarded(self, deckIdx: int, position: int) -> None:
        self.pleaseObserveBeforeDiscard(self.position, position, deckIdx)

    def someone_played(self,
                       player: int,
                       deckIdx: int,
                       position: int) -> None:
        self.pleaseObserveBeforePlay(player, position, deckIdx)

    def card_played(self, deckIdx: int, position: int) -> None:
        self.pleaseObserveBeforePlay(self.position, position, deckIdx)

    def someone_got_color(self,
                          from_: int,
                          to: int,
                          color: Color,
                          positions: List[int]) -> None:
        self.pleaseObserveColorHint(from_, to, color, positions)

    def got_color_clue(self,
                       player: int,
                       color: Color,
                       positions: List[int]) -> None:
        self.pleaseObserveColorHint(player, self.position, color, positions)

    def someone_got_value(self,
                          from_: int,
                          to: int,
                          value: Value,
                          positions: List[int]) -> None:
        self.pleaseObserveValueHint(from_, to, value, positions)

    def got_value_clue(self,
                       player: int,
                       value: Value,
                       positions: List[int]) -> None:
        self.pleaseObserveValueHint(player, self.position, value, positions)

    def decide_move(self, can_clue: bool, can_discard: bool) -> None:
        if self.waitTime:
            time.sleep(self.waitTime)
        self.pleaseMakeMove(can_clue, can_discard)

    def game_stage(self) -> GameStage:
        '''Determines what stage of the game it is'''
        if len(self.game.discards) == 0:
            return GameStage.Early
        if self.game.deckCount <= len(self.game.players):
            return GameStage.End
        moreToPlay: int
        moreToPlay = sum(self.maxPlayValue.values()) - self.game.scoreCount
        if moreToPlay <= len(self.game.players):
            return GameStage.End
        return GameStage.Mid

    def isNowPlayable(self,
                      color: Optional[Color],
                      value: Optional[Value]) -> bool:
        '''Returns True the color and/or value is playable'''
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
        assert False

    def isPlayable(self, color: Color, value: Value) -> bool:
        '''Returns True if the color and value is now playable'''
        playableValue: int = len(self.game.playedCards[color]) + 1
        return value == playableValue

    def isValuable(self, color: Color, value: Value) -> bool:
        '''Returns True if the color and value is critical'''
        if self.playedCount[color][value] != value.num_copies - 1:
            return False
        return not self.isWorthless(color, value)

    def is2Valuable(self, color: Color) -> bool:
        '''Returns True if value 2 for a color is useful in the future'''
        if self.lowestPlayableValue > 2:
            return False
        if self.isCluedSomewhere(color, Value.V2, maybe=True):
            return False
        return self.eyesightCount[color][2] != Value.V2.num_copies

    def isWorthless(self, color: Color, value: Value) -> bool:
        '''Returns True if the color and value is completely useless'''
        playableValue: int = len(self.game.playedCards[color]) + 1
        if value < playableValue:
            return True
        while(value > playableValue):
            value = Value(value - 1)
            if self.playedCount[color][value] == value.num_copies:
                return True
        return False

    def isUseful(self, color: Color, value: Value) -> bool:
        '''Returns True if the color and value is useful now or later'''
        if self.isWorthless(color, value):
            return False
        playableValue = len(self.game.playedCards[color]) + 1
        return value >= playableValue

    def updateEyesightCount(self) -> None:
        self.eyesightCount = {c: [0] * 6 for c in self.colors}
        p: Player
        c: int
        card: CardKnowledge
        for p in self.game.players:
            for c in p.hand:
                card = cast(CardKnowledge, self.game.deck[c])
                if card.suit is not None and card.rank is not None:
                    self.eyesightCount[card.suit][card.rank] += 1
                elif card.color is not None and card.value is not None:
                    self.eyesightCount[card.color][card.value] += 1

    def updateLocatedCount(self) -> bool:
        '''Returns True if played/discarded cards has changed'''
        newCount: Dict[Color, List[int]] = {c: [0] * 6 for c in self.colors}
        p: Player
        c: int
        for p in self.game.players:
            for c in p.hand:
                card = cast(CardKnowledge, self.game.deck[c])
                if card.color is not None and card.value is not None:
                    newCount[card.color][card.value] += 1

        if newCount != self.locatedCount:
            self.locatedCount = newCount
            return True
        return False

    def updateDiscardCount(self) -> None:
        self.discardCount = {c: [0] * 6 for c in self.colors}
        for c in self.game.discards:
            card = self.game.deck[c]
            self.discardCount[card.suit][card.rank] += 1

    def updateColorValueTables(self) -> None:
        c: Color
        for c in self.colors:
            self.nextPlayValue[c] = len(self.game.playedCards[c]) + 1
            self.maxPlayValue[c] = 0
            score: int = len(self.game.playedCards[c])
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

    def seePublicCard(self, color: Color, value: Value) -> None:
        self.playedCount[color][value] += 1
        assert 1 <= self.playedCount[color][value] <= value.num_copies

    def handState(self,
                  player: int,
                  showCritical: bool=True) -> List[HandState]:
        handState: List[HandState]
        handState = [HandState.Unclued] * len(self.game.players[player].hand)
        c: int
        h: int
        card: CardKnowledge
        for c, h in enumerate(self.game.players[player].hand):
            card = cast(CardKnowledge, self.game.deck[h])
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

    def discardSlot(self, handState: List[HandState]) -> Optional[int]:
        discard: Optional[int] = None
        worthless: Optional[int] = None
        for c, h in enumerate(handState):
            if h in [HandState.Playable, HandState.SoonPlay, HandState.Saved]:
                continue
            if h == HandState.Worthless:
                worthless = c
            else:
                if discard is None:
                    discard = c
        return worthless if worthless is not None else discard

    def isCluedElsewhere(self, player: int, hand: int) -> bool:
        returnVal: bool = False
        cardIdx: int = self.game.players[player].hand[hand]
        handcard: CardKnowledge
        handcard = cast(CardKnowledge, self.game.deck[cardIdx])
        color: Color = handcard.suit
        value: Value = handcard.rank
        p: Player
        c: int
        card: CardKnowledge
        for p in self.game.players:
            for c in p.hand:
                card = cast(CardKnowledge, self.game.deck[c])
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

    def cluedCard(self,
                  color: Color,
                  value: Value,
                  player: Optional[int]=None,
                  strict: bool=False,
                  maybe: bool=False) -> Optional[int]:
        p: Player
        c: int
        card: CardKnowledge
        for p in self.game.players:
            if player == p.position:
                if strict:
                    continue
                # When it is the player, assume fully tagged cards as clued too
                for c in p.hand:
                    card = cast(CardKnowledge, self.game.deck[c])
                    if card.color == color and card.value == value:
                        return card.deckPosition
                    if p is self:
                        if (maybe and card.maybeColor == color
                                and card.maybeValue == value):
                            return card.deckPosition
            elif p is self:
                for c in p.hand:
                    card = cast(CardKnowledge, self.game.deck[c])
                    if card.color == color and card.value == value:
                        return card.deckPosition
                    if (maybe and card.maybeColor == color
                            and card.maybeValue == value):
                        return card.deckPosition
            else:
                for c in p.hand:
                    card = cast(CardKnowledge, self.game.deck[c])
                    if (card.clued
                        and card.suit == color
                        and card.rank == value):
                        return card.deckPosition
        return None

    def isCluedSomewhere(self,
                         color: Color,
                         value: Value,
                         player: Optional[int]=None,
                         strict: bool=False,
                         maybe: bool=False) -> bool:
        return self.cluedCard(color, value, player, strict, maybe) is not None

    def maybeFixBeforeMisplay(self) -> bool:
        assert self.game.clueCount != 0

        # If a hand is near locked or is locked, maybe give a clue that can
        # free a hand up
        if self.game.clueCount == 1:
            d: int
            i: int
            j: int
            h: int
            card: CardKnowledge
            jcard: CardKnowledge
            for d in range(1, self.game.numPlayers):
                player: int = (self.position + d) % self.game.numPlayers
                hand: List[int] = self.game.players[player].hand
                fullHand: bool = True
                for h in hand:
                    card = cast(CardKnowledge, self.game.deck[h])
                    if not card.clued:
                        fullHand = False

                if not fullHand:
                    continue

                for i, h in enumerate(hand):
                    card = cast(CardKnowledge, self.game.deck[h])
                    if not self.isWorthless(card.suit, card.rank):
                        continue
                    if card.worthless is not None:
                        continue
                    for j in range(i):
                        jcard = cast(CardKnowledge, self.game.deck[h])
                        if card.suit == jcard.suit and card.rank == jcard.rank:
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

    def maybeEarlySaveCriticalCard(self, urgent: bool) -> bool:
        assert self.game.clueCount != 0

        selfHandState: List[HandState] = self.handState(self.position)

        if not urgent and HandState.Playable in selfHandState:
            return False

        i: int
        player: int
        if self.game.turnCount == 0:
            bestClue: Hint
            for i in range(1, self.game.numPlayers):
                player = (self.position + i) % self.game.numPlayers
                bestClue = self.bestEarlyHintForPlayer(player, False)
                if bestClue is not None:
                    if bestClue.color is not None:
                        return False
                    if bestClue.value == Value.V1:
                        if bestClue.fitness >= 60:
                            return False
        was1Clued: bool = self.game.turnCount != 0
        hint: Hint = Hint()
        distance: Iterable[int] = range(1, self.game.numPlayers)
        if urgent:
            distance = range(1, 2)
        hand: List[int]
        discard: Optional[int]
        v: Value
        h: int
        card: CardKnowledge
        hcard: CardKnowledge
        for i in distance:
            player = (self.position + i) % self.game.numPlayers
            hand = self.game.players[player].hand
            discard = self.discardSlot(self.handState(player))
            for v in [Value.V2, Value.V5]:
                tagged: List[int] = []
                valueMDuplicate: int = 0
                valueDuplicate: int = 0
                valueUseless: int = 0
                numWasClued: int = 0
                for i, h in enumerate(hand):
                    card = cast(CardKnowledge, self.game.deck[h])
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
                                hcard = cast(CardKnowledge, self.game.deck[h])
                                if (hcard.maybeColor == card.suit
                                        and hcard.maybeValue == card.rank):
                                    valueDuplicate += 1
                        if self.doesCardMatchHand(card.deckPosition):
                            valueMDuplicate += 1
                taggedDiscard: bool = discard in tagged
                if not (urgent and taggedDiscard):
                    continue
                saveFitness: int = 0
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

    def maybeSaveCriticalCard(self, urgent: bool) -> bool:
        assert self.game.clueCount != 0

        selfHandState: List[HandState] = self.handState(self.position)

        if not urgent and HandState.Playable in selfHandState:
            return False

        distance: Iterable[int] = range(1, self.game.numPlayers)
        if urgent:
            distance = range(1, 2)
        d: int
        i: int
        for d in distance:
            player: int = (self.position + d) % self.game.numPlayers
            handState: List[HandState] = self.handState(player)
            critical: int
            unclued: int
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

            hand: List[int] = self.game.players[player].hand
            card: CardKnowledge
            card = cast(CardKnowledge, self.game.deck[hand[critical]])
            valuable: bool = self.isValuable(card.suit, card.rank)
            if not valuable and card.rank == 2 and self.is2Valuable(card.suit):
                if (self.game.numPlayers == 2
                        or self.doesCardMatchHand(hand[critical])):
                    valuable = None
            if valuable is False:
                continue

            valueTags: List[CardKnowledge] = []
            colorTags: List[CardKnowledge] = []

            h: int
            for h in hand:
                hcard: CardKnowledge
                hcard = cast(CardKnowledge, self.game.deck[h])
                if hcard.suit & card.suit:
                    colorTags.append(hcard)
                if hcard.rank == card.rank:
                    valueTags.append(hcard)

            matchColors: List[Color] = self.matchCriticalCardValue(card.rank)
            matchValues: List[Value] = self.matchCriticalCardColor(card.suit)

            valueFitness: int = 0
            colorFitness: int = 0

            valueMDuplicate: int = 0
            valueDuplicate: int = 0
            valueClarify: int = 0
            valueUseless: int = 0
            valueNewTagged: int = 0
            valueNewSaves: int = 0
            valueOther: int = 0
            tcard: CardKnowledge
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
                        hcard = cast(CardKnowledge, self.game.deck[h])
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

            colorMDuplicate: int = 0
            colorDuplicate: int = 0
            colorClarify: int = 0
            colorUseless: int = 0
            colorNewTagged: int = 0
            colorNewSaves: int = 0
            colorOther: int = 0
            colorSave5: int = 0
            isSave5NextToDiscard: bool = False
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
                nextCard: CardKnowledge
                h = hand[critical + 1]
                nextCard = cast(CardKnowledge, self.game.deck[h])
                isSave5NextToDiscard = (nextCard.suit == card.suit
                                        and nextCard.rank == Value.V5)
            if colorDuplicate == 0 and colorUseless == 0 and valuable is True:
                if not (card.rank == Value.V5 and colorNewSaves):
                    colorFitness = colorNewSaves * 20 + colorOther * 3
                    colorFitness += (colorSave5 + isSave5NextToDiscard) * 10
                    colorFitness -= colorMDuplicate * 20
                    colorFitness -= len(matchValues)

            hint: Hint = Hint()
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
                valueWorthlessHint: Optional[Value] = None
                colorWorthlessHint: Optional[Color] = None
                valueWorthlessFitness: Optional[int] = None
                colorWorthlessFitness: Optional[int] = None

                fitness: int
                v: Value
                c: Color
                for v in self.values[:self.lowestPlayableValue-1]:
                    fitness = 0
                    for h in hand:
                        hcard = cast(CardKnowledge, self.game.deck[h])
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
                        hcard = cast(CardKnowledge, self.game.deck[h])
                        if hcard.suit & c:
                            fitness += 1
                    if fitness <= 0:
                        continue
                    if (colorWorthlessFitness is None
                            or fitness > colorWorthlessFitness):
                        colorWorthlessHint = c
                        colorWorthlessFitness = fitness

                useValue: bool
                useColor: bool
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

    def maybeDiscardForCriticalCard(self) -> bool:
        assert 0 < self.game.clueCount < 8

        # Don't bother for 2 player games, the hand might end up locked
        if self.game.numPlayers < 3:
            return False

        handState: List[HandState] = self.handState(self.position)
        discard: Optional[int] = self.discardSlot(handState)
        # If I don't have a good discard...
        if discard is None:
            return False

        # First check adjacent player
        nextPlayer: int = (self.position + 1) % self.game.numPlayers
        handStateN: List[HandState] = self.handState(nextPlayer)
        discardN: Optional[int] = self.discardSlot(handStateN)
        maybeDiscard: bool
        maybeDiscard = (HandState.Playable not in handStateN
                        and HandState.Playable not in handStateN
                        and discardN is not None)
        if maybeDiscard:
            hand: List[int] = self.game.players[nextPlayer].hand
            cardN: CardKnowledge
            cardN = cast(CardKnowledge, self.game.deck[hand[discardN]])
            if self.isValuable(cardN.suit, cardN.rank):
                self.discard_card(discard)
                return True

        distance: Iterable[int] = range(2, self.game.numPlayers)
        if HandState.Playable in handState:
            distance = range(2, 3)

        for d in distance:
            target: int = (self.position + d) % self.game.numPlayers

            handStateT: List[HandState] = self.handState(target)
            discardT: Optional[int] = self.discardSlot(handStateT)

            if HandState.Playable in handStateN:
                continue
            if HandState.Worthless not in handStateN:
                continue
            if discardT is None:
                continue

            targetHand: List[int] = self.game.players[target].hand
            cardT: CardKnowledge
            cardT = cast(CardKnowledge, self.game.deck[targetHand[discardT]])
            if not self.isValuable(cardT.suit, cardT.rank):
                continue

            c: int
            for c in range(1, d):
                between: int = (self.position + c) % self.game.numPlayers
                handStateB: List[HandState] = self.handState(between)
                discardB: Optional[int] = self.discardSlot(handStateB)
                needToDiscard: bool
                needToDiscard = not (HandState.Playable in handStateB
                                     or HandState.Worthless in handStateB)
                if needToDiscard and discardB is not None:
                    betweenHand: List[int] = self.game.players[between].hand
                    h: int = betweenHand[discardB]
                    cardB: CardKnowledge
                    cardB = cast(CardKnowledge, self.game.deck[h])
                    if not self.isValuable(cardB.suit, cardB.rank):
                        needToDiscard = False
                if needToDiscard:
                    self.discard_card(discard)
                    return True
        return False

    def valueOrderFromColor(self,
                            color: Color,
                            taggedCards: List[int],
                            player: int,
                            otherPlayer: Optional[Union[int, bool]]=None,
                            otherColor: Optional[Color]=None,
                            otherValue: Optional[Value]=None
                            ) -> Tuple[List[Tuple[int, Value]], int, int, int,
                                       Optional[bool], bool]:
        assert otherColor is None or otherValue is None
        assert otherPlayer is None or (otherColor is not None or
                                       otherValue is not None)
        tagged: List[int] = taggedCards[:]
        values: List[Tuple[int, Value]] = []
        elseWhereColor: List[Color] = []
        elseWhereValue: List[Value] = []
        card: CardKnowledge
        if isinstance(otherPlayer, int):
            for h in self.game.players[otherPlayer].hand:
                card = cast(CardKnowledge, self.game.deck[h])
                if otherColor is not None and card.suit & otherColor:
                    elseWhereValue.append(card.rank)
                if otherValue is not None and card.rank == otherValue:
                    elseWhereColor.append(card.suit)
        nextToPlay: int = len(self.game.playedCards[color]) + 1
        v: Value
        for v in self.values[nextToPlay-1:self.maxPlayValue[color]]:
            if self.isCluedSomewhere(color, v, player, strict=True,
                                     maybe=True):
                continue
            nextToPlay = v
            break
        isNewestGood: Optional[bool] = None
        needFix: bool = False
        numPlay: int = 0
        numWorthless: int = 0
        maybeDuplicate: int = 0
        i: int
        t: int
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
                card = cast(CardKnowledge, self.game.deck[t])
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
                    card = cast(CardKnowledge, self.game.deck[t])
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
        deckIdx: int
        value: Value
        for deckIdx, value in values:
            if self.doesCardMatchHand(deckIdx):
                maybeDuplicate += 1
        return (values, numPlay, numWorthless, maybeDuplicate, isNewestGood,
                needFix)

    def playOrderColorClue(self, player: int, color: Color
                           ) -> Tuple[List[Tuple[int, Value]], int, int, int,
                                      Optional[bool], bool, int, int,
                                      Optional[int], Optional[Color],
                                      Optional[List[Value]]]:
        assert player != self.position
        tagged: List[int] = []
        hand: List[int] = self.game.players[player].hand
        numNewTagged: int = 0
        badClarify: int = 0
        h: int
        card: CardKnowledge
        for h in reversed(hand):
            card = cast(CardKnowledge, self.game.deck[h])
            if not (card.suit & color):
                continue
            tagged.append(h)
            if card.color is None:
                numNewTagged += 1
                if card.value is not None:
                    if card.playColorDirect or card.playable:
                        badClarify += 1
        playOrder: List[Tuple[int, Value]]
        numPlay: int
        numWorthless: int
        maybeDuplicate: int
        isNewestGood: Optional[bool]
        needFix: bool
        (playOrder, numPlay, numWorthless, maybeDuplicate, isNewestGood,
         needFix
         ) = self.valueOrderFromColor(color, tagged, player)

        fixPlayer: Optional[int] = None
        fixColor: Optional[Color] = None
        fixValue: Optional[List[Value]] = None
        if needFix:
            playOrder_: List[Tuple[int, Value]]
            numPlay_: int
            numWorthless_: int
            maybeDuplicate_: int
            isNewestGood_: Optional[bool]
            needFix_: bool
            tagV: Value
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

            p: int
            for p in range(self.game.numPlayers):
                if p == player or p == self.position:
                    continue
                (playOrder_, numPlay_, numWorthless_, maybeDuplicate_,
                 isNewestGood_, needFix_
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

    def playOrderValueClue(self, player: int, value: Value
                           ) -> Tuple[List[Tuple[int, Set[Color]]], int, int,
                                      int, int, int, int, int, int]:
        assert player != self.position
        numNewTagged: int = 0
        tagged: List[int] = []
        hand: List[int] = self.game.players[player].hand
        h: int
        card: CardKnowledge
        for h in reversed(hand):
            card = cast(CardKnowledge, self.game.deck[h])
            if card.rank == value:
                if card.value is None:
                    numNewTagged += 1
                tagged.append(h)
        playColors: List[Color] = []
        futureColors: List[Color] = []
        c: Color
        for c in self.colors:
            if self.colorComplete[c]:
                continue
            deckIdx: Optional[int]
            if self.isCluedSomewhere(c, value, self.position, maybe=True):
                deckIdx = self.cluedCard(c, value, self.position, maybe=True)
                card = cast(CardKnowledge, self.game.deck[deckIdx])
                if deckIdx not in tagged or not card.cluedAsDiscard:
                    continue
            scoreTagged: int = len(self.game.playedCards[c])
            v: Value
            for v in self.values[scoreTagged:self.maxPlayValue[c]]:
                if self.isCluedSomewhere(c, v, self.position, maybe=True):
                    deckIdx = self.cluedCard(c, v, self.position, maybe=True)
                    card = cast(CardKnowledge, self.game.deck[deckIdx])
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
        neededColors: List[Color] = playColors + futureColors
        numNeed: int = len(neededColors)
        playOrder: List[Tuple[int, Set[Color]]] = []
        futureOrder: List[Tuple[int, Set[Color]]] = []
        worthlessOrder: List[Tuple[int, Set[Color]]] = []
        colorUsed: Set[Color] = set()
        numPlay: int = 0
        numFuture: int = 0
        numWorthless: int = 0
        maybeDuplicate: int = 0
        numPlayMismatch: int = 0
        numFutureMismatch: int = 0
        numCompleteMismatch: int = 0
        # Check fully tagged cards first
        i: int
        t: int
        for t in tagged:
            card = cast(CardKnowledge, self.game.deck[t])
            if self.doesCardMatchHand(t):
                maybeDuplicate += 1
            color: Optional[Color] = card.maybeColor
            if color is not None:
                if color in playColors:
                    playOrder.append((t, {color}))
                    playColors.remove(color)
                    neededColors.remove(color)
                    colorUsed.add(color)
                    tagged.remove(t)
                    if card.value is None:
                        numPlay += 1
                elif color in futureColors:
                    futureOrder.append((t, {color}))
                    futureColors.remove(color)
                    neededColors.remove(color)
                    colorUsed.add(color)
                    tagged.remove(t)
                    if card.value is None:
                        numFuture += 1
                else:
                    worthlessOrder.append((t, set()))
                    if card.value is None:
                        numWorthless += 1
        for i, t in enumerate(tagged):
            card = cast(CardKnowledge, self.game.deck[t])
            if i < len(playColors):
                playOrder.append((t, set(playColors)))
                if card.suit in playColors and card.suit not in colorUsed:
                    if card.value is None:
                        numPlay += 1
                    colorUsed.add(card.suit)
                else:
                    if len(colorUsed) < numNeed:
                        numPlayMismatch += 1
                if card.suit not in neededColors:
                    numCompleteMismatch += 1
            elif i < len(playColors) + len(futureColors):
                futureOrder.append((t, set(futureColors)))
                if card.suit in futureColors and card.suit not in colorUsed:
                    if card.value is None:
                        numFuture += 1
                    colorUsed.add(card.suit)
                else:
                    numFutureMismatch += 1
                if card.suit not in neededColors:
                    numCompleteMismatch += 1
            else:
                worthlessOrder.append((t, set()))
                if card.value is None:
                    numWorthless += 1

        return (playOrder + futureOrder + worthlessOrder,
                numPlay, numFuture, numWorthless, maybeDuplicate,
                numPlayMismatch, numFutureMismatch, numCompleteMismatch,
                numNewTagged)

    def doesCardMatchHand(self, deckIdx: int) -> bool:
        deckCard: CardKnowledge
        deckCard = cast(CardKnowledge, self.game.deck[deckIdx])
        assert deckCard.suit is not None
        assert deckCard.rank is not None
        if self.colorComplete[deckCard.suit]:
            return False
        if deckCard.rank == Value.V5:
            return False
        h: int
        for h in self.hand:
            card: CardKnowledge
            card = cast(CardKnowledge, self.game.deck[h])
            if not card.clued:
                continue
            if card.worthless or card.playWorthless:
                continue
            if card.cantBe[deckCard.suit][deckCard.rank]:
                continue
            if card.color is not None and card.value is not None:
                continue
            if card.color == deckCard.suit:
                maybeValue: Optional[Value] = card.maybeValue
                if maybeValue is not None:
                    if maybeValue == deckCard.rank:
                        return True
                    continue
                if deckCard.rank in card.possibleValues:
                    return True
            if card.value == deckCard.rank:
                maybeColor: Optional[Color] = card.maybeColor
                if maybeColor is not None:
                    if maybeColor == deckCard.suit:
                        return True
                    continue
                if deckCard.suit in card.possibleColors:
                    return True
        return False

    def bestEarlyHintForPlayer(self,
                               player: int,
                               highValue: bool) -> Optional[Hint]:
        assert player != self.position
        hand: List[int] = self.game.players[player].hand

        c: Color
        needToTag: Dict[Color, int] = {c: 0 for c in self.colors}
        for c in self.colors:
            nextValue: int = len(self.game.playedCards[c]) + 1
            while nextValue < 6:
                if not self.locatedCount[c][nextValue]:
                    needToTag[c] = nextValue
                    break
                nextValue += 1

        handState: List[HandState] = self.handState(player)
        discard: Optional[int] = self.discardSlot(handState)

        numClued: int = 0
        h: int
        card: CardKnowledge
        for h in hand:
            card = cast(CardKnowledge, self.game.deck[h])
            if card.clued:
                numClued += 1

        best_so_far: Hint = Hint()
        best_so_far.to = player
        tagged: List[int]
        for c in self.colors:
            tagged = []
            i: int
            for i in range(len(hand)):
                card = cast(CardKnowledge, self.game.deck[hand[i]])
                if card.suit & c:
                    tagged.append(i)
            if not tagged:
                continue

            colorFitness: int = 0

            # Decision Here
            values: List[Tuple[int, Value]]
            numPlay: int
            numWorthless: int
            maybeDuplicate: int
            isNewestGood: Optional[bool]
            needFix: bool
            numNewTagged: int
            badClarify: int
            fixPlayer: Optional[int]
            fixColor: Optional[Color]
            fixValue: Optional[List[Value]]
            (values, numPlay, numWorthless, maybeDuplicate, isNewestGood,
             needFix, numNewTagged, badClarify,
             fixPlayer, fixColor, fixValue
             ) = self.playOrderColorClue(player, c)
            goodTag: int = numNewTagged - badClarify - numWorthless
            if (not needFix and isNewestGood and values[0][1] is not None
                and maybeDuplicate == 0
                and goodTag > 0):
                baseValue: int = 22 + cluePlayWeight[values[0][1]]
                baseSave: int = 11
                colorFitness = (numPlay * baseValue
                                + numWorthless)

            if colorFitness > best_so_far.fitness:
                best_so_far.fitness = colorFitness
                best_so_far.color = c
                best_so_far.value = None

        v: Value
        for v in self.values:
            tagged = []
            for i in range(len(hand)):
                card = cast(CardKnowledge, self.game.deck[hand[i]])
                if card.rank == v:
                    tagged.append(i)
            if not tagged:
                continue

            looksLikeSave: bool = False
            if HandState.Worthless not in handState and discard in tagged:
                saveColors: List[Color] = self.matchCriticalCardValue(v)
                looksLikeSave = bool(saveColors) and v != Value.V5
            if v == self.lowestPlayableValue:
                looksLikeSave = False

            valueFitness: int = 0

            # Decision Here
            if v < self.lowestPlayableValue:
                pass
            else:
                playOrder: List[Tuple[int, Set[Color]]]
                #numPlay: int
                numFuture: int
                #numWorthless: int
                #maybeDuplicate: int
                numPlayMismatch: int
                numFutureMismatch: int
                numCompleteMismatch: int
                #numNewTagged: int
                (playOrder, numPlay, numFuture, numWorthless, maybeDuplicate,
                 numPlayMismatch, numFutureMismatch, numCompleteMismatch,
                 numNewTagged
                 ) = self.playOrderValueClue(player, v)
                if (numNewTagged >= 1 and numPlay >= 1
                        and maybeDuplicate == 0
                        and numPlayMismatch == 0
                        and numFutureMismatch == 0
                        and numCompleteMismatch == 0):
                    baseValue = 20 + cluePlayWeight[v]
                    baseFuture = 5 + clueFutureWeight[v]
                    baseSave = 20
                    valueFitness = (numPlay * baseValue
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

    def bestHintForPlayer(self, player: int) -> Optional[Hint]:
        assert player != self.position
        hand: List[int] = self.game.players[player].hand

        needToTag: Dict[Color, int] = {c: 0 for c in self.colors}
        c: Color
        for c in self.colors:
            nextValue: int = len(self.game.playedCards[c]) + 1
            while nextValue < 6:
                if not self.locatedCount[c][nextValue]:
                    needToTag[c] = nextValue
                    break
                nextValue += 1

        awayFromPlayable: List[int] = [-10] * len(hand)
        awayFromTaggable: List[int] = [-10] * len(hand)
        i: int
        card: CardKnowledge
        for i in range(len(hand)):
            card = cast(CardKnowledge, self.game.deck[hand[i]])
            nextValue = len(self.game.playedCards[card.suit]) + 1
            awayFromPlayable[i] = nextValue - card.rank
            awayFromTaggable[i] = needToTag[card.suit] - card.rank

        handState: List[HandState] = self.handState(player)
        discard: Optional[int] = self.discardSlot(handState)

        numClued: int = 0
        h: int
        for h in hand:
            card = cast(CardKnowledge, self.game.deck[h])
            if card.clued:
                numClued += 1

        best_so_far: Hint = Hint()
        best_so_far.to = player
        tagged: List[int]
        for c in self.colors:
            tagged = []
            for i in range(len(hand)):
                card = cast(CardKnowledge, self.game.deck[hand[i]])
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
            values: List[Tuple[int, Value]]
            numPlay: int
            numWorthless: int
            maybeDuplicate: int
            isNewestGood: Optional[bool]
            needFix: bool
            numNewTagged: int
            badClarify: int
            fixPlayer: Optional[int]
            fixColor: Optional[Color]
            fixValue: Optional[List[Value]]
            (values, numPlay, numWorthless, maybeDuplicate, isNewestGood,
             needFix, numNewTagged, badClarify,
             fixPlayer, fixColor, fixValue
             ) = self.playOrderColorClue(player, c)
            goodTag: int = numNewTagged - badClarify - numWorthless
            needToPlay: int
            needToPlay = self.maxPlayValue[c] - len(self.game.playedCards[c])
            if (not needFix and isNewestGood and values[0][1] is not None
                and maybeDuplicate == 0
                and goodTag > 0):
                baseValue: int = 22 + cluePlayWeight[values[0][1]]
                baseSave: int = 11
                colorFitness = (numPlay * baseValue
                                + numWorthless
                                - looksLikeSave * baseSave)
                if numClued + numNewTagged == len(hand) and looksLikeSave:
                    colorFitness -= 22

            if colorFitness > best_so_far.fitness:
                best_so_far.fitness = colorFitness
                best_so_far.color = c
                best_so_far.value = None

        v: Value
        for v in self.values:
            tagged = []
            for i in range(len(hand)):
                card = cast(CardKnowledge, self.game.deck[hand[i]])
                if card.rank == v:
                    tagged.append(i)
            if not tagged:
                continue

            looksLikeSave = False
            if HandState.Worthless not in handState and discard in tagged:
                saveColors: List[Color] = self.matchCriticalCardValue(v)
                looksLikeSave = bool(saveColors) or v == Value.V5
            if v == self.lowestPlayableValue:
                looksLikeSave = False

            valueFitness: int = 0

            # Decision Here
            if v < self.lowestPlayableValue:
                pass
            else:
                playOrder: List[Tuple[int, Set[Color]]]
                #numPlay: int
                numFuture: int
                #numWorthless: int
                #maybeDuplicate: int
                numPlayMismatch: int
                numFutureMismatch: int
                numCompleteMismatch: int
                #numNewTagged: int
                (playOrder, numPlay, numFuture, numWorthless, maybeDuplicate,
                 numPlayMismatch, numFutureMismatch, numCompleteMismatch,
                 numNewTagged
                 ) = self.playOrderValueClue(player, v)
                if (numNewTagged >= 1 and numPlay >= 1
                        and maybeDuplicate == 0
                        and numPlayMismatch == 0
                        and numFutureMismatch == 0
                        and numCompleteMismatch == 0):
                    baseValue = 20
                    baseFuture: int = 7
                    baseSave = 20
                    if v == Value.V5:
                        baseValue = 7
                        baseFuture = 2
                        baseSave = 7
                    baseValue += cluePlayWeight[v]
                    baseFuture += clueFutureWeight[v]
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

    def bestCardToPlay(self) -> Optional[int]:
        handState: List[HandState] = self.handState(self.position)
        handInfo: List[Tuple[int, Tuple[HandState, int]]]
        handInfo = list(enumerate(zip(handState, self.hand)))

        lowestValue: int
        index: Optional[int]
        i: int
        hs: HandState
        h: int
        card: CardKnowledge
        value: Optional[Value]
        passed: bool

        lowestValue = 6
        index = None
        for i, (hs, h) in reversed(handInfo):
            if hs == HandState.Playable:
                card = cast(CardKnowledge, self.game.deck[h])
                value = card.maybeValue
                assert value is not None
                passed = False
                if value < Value.V5:
                    for c in card.maybeColors:
                        nextClued = self.isCluedSomewhere(
                            c, Value(value + 1), player=self.position,
                            strict=True)
                        if nextClued:
                            passed = True
                if not passed:
                    continue
                if value.value < lowestValue:
                    index = i
                    lowestValue = value.value
        if index is not None:
            return index

        lowestValue = 6
        index = None
        for i, (hs, h) in reversed(handInfo):
            if hs == HandState.Playable:
                card = cast(CardKnowledge, self.game.deck[h])
                value = card.maybeValue
                passed = False
                if value < Value.V5:
                    for c in card.maybeColors:
                        nextClued = self.isCluedSomewhere(c, Value(value + 1),
                                                          maybe=True)
                        if nextClued:
                            passed = True
                if not passed:
                    continue
                if value.value < lowestValue:
                    index = i
                    lowestValue = value.value
        if index is not None:
            return index

        lowestValue = 6
        index = None
        for i, (hs, h) in reversed(handInfo):
            if hs == HandState.Playable:
                card = cast(CardKnowledge, self.game.deck[h])
                value = card.maybeValue
                if value.value < lowestValue:
                    index = i
                    lowestValue = value.value
        return index

    def maybePlayCard(self) -> bool:
        best_index: Optional[int] = self.bestCardToPlay()
        if best_index is not None:
            self.play_card(best_index)
            return True
        return False

    def maybeGiveEarlyGameHint(self, highValue: bool) -> bool:
        bestHint: Hint = Hint()
        i: int
        for i in range(1, self.game.numPlayers):
            player: int = (self.position + i) % self.game.numPlayers
            candidate: Optional[Hint]
            candidate = self.bestEarlyHintForPlayer(player, highValue)
            if candidate is not None and candidate.fitness >= 0:
                handState: List[HandState] = self.handState(player)
                if HandState.Playable not in handState:
                    candidate.fitness += (self.game.numPlayers - i) * 2
            if candidate is not None and candidate.fitness > bestHint.fitness:
                bestHint = candidate
        if bestHint.fitness <= 0:
            return False

        bestHint.give(self)
        return True

    def maybeGiveHelpfulHint(self) -> bool:
        assert self.game.clueCount != 0

        bestHint: Hint = Hint()
        i: int
        for i in range(1, self.game.numPlayers):
            player: int = (self.position + i) % self.game.numPlayers
            candidate: Optional[Hint]
            candidate = self.bestHintForPlayer(player)
            if candidate is not None and candidate.fitness >= 0:
                handState: List[HandState] = self.handState(player)
                if HandState.Playable not in handState:
                    candidate.fitness += (self.game.numPlayers - i) * 2
            if candidate is not None and candidate.fitness > bestHint.fitness:
                bestHint = candidate
        if bestHint.fitness <= 0:
            return False

        bestHint.give(self)
        return True

    def maybeSpendEndGameClue(self):
        moreToPlay: int
        moreToPlay = sum(self.maxPlayValue.values()) - self.game.scoreCount
        shouldClue: bool = moreToPlay <= self.game.clueCount
        hs: List[HandState] = self.handState(self.position)
        player: int
        if HandState.SoonPlay in hs:
            shouldClue = True
        elif self.game.clueCount == 1:
            player = (self.position + 1) % self.game.numPlayers
            hs = self.handState(player)
            if HandState.Playable not in hs and HandState.SoonPlay in hs:
                shouldClue = False

        if not shouldClue:
            return False

        hint: Hint = Hint()
        for i in range(1, self.game.numPlayers):
            player = (self.position + i) % self.game.numPlayers
            hand: List[int] = self.game.players[player].hand

            v: Value
            c: Color
            h: int
            tagged: int
            match: int
            base: int
            fitness: int
            card: CardKnowledge
            for v in self.values[:self.lowestPlayableValue-1]:
                tagged = 0
                match = 0
                for h in hand:
                    card = cast(CardKnowledge, self.game.deck[h])
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
                    card = cast(CardKnowledge, self.game.deck[h])
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
        if hint.fitness:
            hint.give(self)
            return True
        else:
            return False

    def giveHintOnNoDiscards(self) -> bool:
        hint: Hint = Hint()
        i: int
        for i in range(1, self.game.numPlayers):
            player: int = (self.position + i) % self.game.numPlayers
            hand: List[int] = self.game.players[player].hand

            v: Value
            c: Color
            tagged: int
            match: int
            fitness: int
            card: CardKnowledge
            for v in self.values[:self.lowestPlayableValue-1] + [Value.V5]:
                tagged = 0
                match = 0
                for h in hand:
                    card = cast(CardKnowledge, self.game.deck[h])
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
                includeFive: bool = False
                includeNonFive: bool = False
                for h in hand:
                    card = cast(CardKnowledge, self.game.deck[h])
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
                    card = cast(CardKnowledge, self.game.deck[h])
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
            assert False

    def maybeDiscardOldCard(self) -> bool:
        handState: List[HandState] = self.handState(self.position)
        discard: Optional[int] = self.discardSlot(handState)
        if discard is not None:
            self.discard_card(discard)
            return True
        return False

    def discardSomeCard(self) -> bool:
        best_index: int = 0
        card: CardKnowledge
        bestCard: CardKnowledge
        i: int
        for i in range(len(self.hand)):
            card = cast(CardKnowledge, self.game.deck[self.hand[i]])
            bestCard = cast(CardKnowledge,
                            self.game.deck[self.hand[best_index]])
            if bestCard.maybeValue is None:
                best_index = i
            elif (card.maybeValue is not None
                    and card.maybeValue > bestCard.maybeValue):
                best_index = i
        self.discard_card(best_index)
        return True

    def reevaluateClue(self, clues: List[ClueState], to: int) -> None:
        clueState: ClueState
        for clueState in clues:
            if clueState.value is not None:
                critical: bool = clueState.critical
                possibleColors: List[Color] = clueState.playColors[:]
                laterColors: List[Color] = clueState.laterColors[:]
                criticalColors: List[Color] = clueState.discardColors[:]
                newestIndex: Optional[int] = None
                i: int
                for i in reversed(clueState.indexes):
                    if not clueState.wasClued[i]:
                        newestIndex = i
                        break
                newestCard: Optional[CardKnowledge] = None
                h: int
                if newestIndex is not None:
                    h = clueState.hand[newestIndex]
                    newestCard = cast(CardKnowledge, self.game.deck[h])
                c: Color
                for c in self.colors:
                    played: int = self.playedCount[c][clueState.value]
                    held: int = self.eyesightCount[c][clueState.value]
                    score: int = len(self.game.playedCards[c])
                    cantBe: bool
                    cantBe = played + held == clueState.value.num_copies
                    cantBe = cantBe or score >= clueState.value
                    if newestCard is not None:
                        v: Value = clueState.value
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
                numAllColors: int = len(possibleColors) + len(laterColors)
                if critical:
                    discardCard: CardKnowledge
                    discardCard = cast(CardKnowledge,
                                       self.game.deck[clueState.discardIndex])
                    for c in criticalColors[:]:
                        if discardCard.cannotBeColor(c):
                            criticalColors.remove(c)
                card: CardKnowledge
                deckIdx: int
                for h in reversed(clueState.indexes):
                    deckIdx = clueState.hand[h]
                    card = cast(CardKnowledge, self.game.deck[deckIdx])
                    if card.state != CardState.Hand:
                        continue
                    clueIndex: int
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
                    deckIdx = clueState.hand[h]
                    card = cast(CardKnowledge, self.game.deck[deckIdx])
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
                                taggedCard: CardKnowledge
                                taggedCard = cast(CardKnowledge,
                                                  self.game.deck[h])
                                if taggedCard.color == card.color:
                                    taggedCard.cluedAsPlay = True
                                    taggedCard.valuable = None
                                    taggedCard.discardValues.clear()
                    else:
                        card.cluedAsPlay = True

    def updatePlayableValue(self, player: int) -> bool:
        rtnValue: bool = False
        player_: Player = self.game.players[player]
        cardsNeeded: Dict[Color, int] = {c: 0 for c in self.colors}
        fullyKnown: Dict[Color, int] = {c: 0 for c in self.colors}
        c: Color
        v: Value
        score: int
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
        card: CardKnowledge
        tagged: List[int]
        for c in self.colors:
            if self.colorComplete[c]:
                continue
            tagged = []
            h: int
            for h in reversed(player_.hand):
                card = cast(CardKnowledge, self.game.deck[h])
                if card.clued and card.color == c:
                    tagged.append(h)
            score = len(self.game.playedCards[c])
            t: int
            for v in self.values[score:]:
                if not tagged:
                    break
                if self.isCluedSomewhere(c, v, player):
                    continue
                for t in tagged[:]:
                    card = cast(CardKnowledge, self.game.deck[t])
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
                card = cast(CardKnowledge, self.game.deck[t])
                if card.valuable:
                    continue
                if card.clued and card.value is None and card.color == c:
                    card.playValue = None
                    card.playWorthless = True
        return rtnValue

    def pleaseObserveBeforeMove(self) -> None:
        self.updateDiscardCount()
        self.updateColorValueTables()

        self.lowestPlayableValue = 6
        color: Color
        for color in self.colors:
            if self.colorComplete[color]:
                continue
            lowest: int = len(self.game.playedCards[color]) + 1
            if lowest < self.lowestPlayableValue:
                self.lowestPlayableValue = lowest

        self.locatedCount = {c: [0] * 6 for c in self.colors}
        self.updateLocatedCount()
        while True:
            self.updateEyesightCount()
            done: bool = True
            p: int
            i: int
            for p in range(self.game.numPlayers):
                for i in range(len(self.game.players[p].hand)):
                    d: int = self.game.players[p].hand[i]
                    card: CardKnowledge
                    card = cast(CardKnowledge, self.game.deck[d])
                    beforeDiscard: bool = card.cluedAsDiscard
                    beforePlay: bool = card.cluedAsPlay
                    card.update(p == self.position)
                    if (card.clued and card.color is None
                            and card.value is not None
                            and not card.playColors
                            and not card.discardColors
                            and not (card.playWorthless or card.worthless)):
                        clues = []
                        clueState: ClueState
                        for clueState in self.clueLog[p]:
                            if card.deckPosition not in clueState.hand:
                                continue
                            i = clueState.hand.index(card.deckPosition)
                            if i not in clueState.indexes:
                                continue
                            clues.append(clueState)
                        self.reevaluateClue(clues, p)
                        done = False
                    if (beforeDiscard != card.cluedAsDiscard
                            or beforePlay != card.cluedAsPlay):
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

    def pleaseObserveBeforeDiscard(self,
                                   from_: int,
                                   card_index: int,
                                   deckIdx: int) -> None:
        card: CardKnowledge = cast(CardKnowledge, self.game.deck[deckIdx])
        card.state = CardState.Discard
        self.seePublicCard(card.suit, card.rank)

    def pleaseObserveBeforePlay(self,
                                from_: int,
                                card_index: int,
                                deckIdx: int) -> None:
        card: CardKnowledge = cast(CardKnowledge, self.game.deck[deckIdx])
        card.state = CardState.Play
        self.seePublicCard(card.suit, card.rank)

    def matchCriticalCardColor(self,
                               color: Color,
                               useEyeSight: bool=False) -> List[Value]:
        if self.colorComplete[color]:
            return []
        # Not saving 5's with a color clue
        score: int = len(self.game.playedCards[color])
        if len(self.game.playedCards[color]) >= 4:
            return []
        possibleValues: List[Value] = []
        v: Value
        for v in self.values[score:self.maxPlayValue[color]]:
            if v.num_copies == 1:
                continue
            if self.discardCount[color][v] == v.num_copies - 1:
                if self.isCluedSomewhere(color, v):
                    continue
                if self.locatedCount[color][v]:
                    continue
                if useEyeSight:
                    if self.eyesightCount[color][v] == v.num_copies:
                        continue
                possibleValues.append(v)
        return possibleValues

    def matchCriticalCardValue(self,
                               value: Value,
                               useEyeSight: bool=False) -> List[Color]:
        possibleColors: List[Color]
        c: Color
        if value == Value.V5:
            possibleColors = []
            for c in self.colors:
                if self.playedCount[c][value] or self.locatedCount[c][value]:
                    continue
                if not self.isUseful(c, value):
                    continue
                if useEyeSight:
                    if self.eyesightCount[c][value] == value.num_copies:
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

    def pleaseObserveColorHint(self,
                               from_: int,
                               to: int,
                               color: Color,
                               card_indices: List[int]):
        hand: List[int] = self.game.players[to].hand
        score: int = len(self.game.playedCards[color])
        handState: List[HandState] = self.handState(to)
        discard: Optional[int] = self.discardSlot(handState)

        possibleValues: List[Value] = []
        v: Value
        i: int
        for v in self.values[score:self.maxPlayValue[color]]:
            if self.isCluedSomewhere(color, v, to):
                continue
            match: bool = False
            for i in card_indices:
                card: CardKnowledge
                card = cast(CardKnowledge, self.game.deck[hand[i]])
                if card.value == v:
                    match = True
                    break
            if match:
                continue
            possibleValues.append(v)

        numToComplete: int = self.maxPlayValue[color] - score
        criticalValues: List[Value]
        criticalValues = self.matchCriticalCardColor(color, useEyeSight=True)
        criticalClue: bool
        criticalClue = (HandState.Worthless not in handState
                            and discard in card_indices)
        if HandState.Worthless not in handState and discard in card_indices:
            criticalClue = bool(criticalValues
                                and numToComplete > len(card_indices))
        criticalState: bool = criticalClue

        wasClued: List[bool] = [None] * len(hand)
        h: int
        card: CardKnowledge
        for i, h in reversed(list(enumerate(hand))):
            card = cast(CardKnowledge, self.game.deck[hand[i]])
            if i in card_indices:
                wasClued[i] = card.clued
                card.clued = True
                card.setMustBeColor(color)
                card.update(False)
                if card.value is not None:
                    playingValue = score + 1
                    if card.value == playingValue:
                        card.setIsPlayable(True)
                    elif card.value <= playingValue:
                        card.setIsWorthless(True)
                elif self.colorComplete[color]:
                    card.setIsWorthless(True)
            else:
                card.setCannotBeColor(color)
        for i, h in enumerate(hand):
            card = cast(CardKnowledge, self.game.deck[h])
            if i in card_indices:
                if criticalState or criticalState is None:
                    if not wasClued[i]:
                        card.cluedAsDiscard = True
                        for v in criticalValues:
                            if card.cannotBeValue(v):
                                continue
                            card.discardValues.append(v)
                        card.playValue = None
                        card.setIsValuable(True, strict=False)
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
                    card.cluedAsPlay = True
        for h in hand:
            card = cast(CardKnowledge, self.game.deck[h])
            card.update(False)

        clueLog = ClueState(self.game.turnCount, criticalClue,
                            hand[:], card_indices[:], wasClued[:],
                            discard, HandState.Worthless in handState,
                            color=color, discard_values=criticalValues[:])
        self.clueLog[to].append(clueLog)

    def pleaseObserveValueHint(self,
                               from_: int,
                               to: int,
                               value: Value,
                               card_indices: List[int]) -> None:
        hand: List[int] = self.game.players[to].hand
        possibleColors: List[Color] = []
        laterColors: List[Color] = []
        deckIdx: int = hand[card_indices[-1]]
        newestCard: CardKnowledge
        newestCard = cast(CardKnowledge, self.game.deck[deckIdx])
        c: Color
        i: int
        for c in self.colors:
            if self.isCluedSomewhere(c, value, to, maybe=True):
                continue
            if newestCard.cantBe[c][value]:
                continue
            match: bool = False
            for i in card_indices:
                card: CardKnowledge
                card = cast(CardKnowledge, self.game.deck[hand[i]])
                if card.color == c:
                    match = True
                    break
            if match:
                continue
            score: int = len(self.game.playedCards[c])
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
        handState: List[HandState] = self.handState(to)
        discard: Optional[int] = self.discardSlot(handState)

        criticalColors: List[Color]
        criticalColors = self.matchCriticalCardValue(value, useEyeSight=True)
        criticalClue: bool
        criticalClue = ((HandState.Worthless not in handState
                         and discard in card_indices)
                        or value == Value.V5)
        if criticalClue and discard is not None:
            discardCard: CardKnowledge
            discardCard = cast(CardKnowledge, self.game.deck[hand[discard]])
            for c in criticalColors:
                if not discardCard.cannotBeColor(c):
                    criticalClue = True
                    break
            else:
                criticalClue = False
        criticalState: bool = criticalClue

        numAllColors: int = len(possibleColors) + len(laterColors)
        wasClued: List[bool] = [None] * len(hand)
        h: int
        card: CardKnowledge
        for i, h in reversed(list(enumerate(hand))):
            card = cast(CardKnowledge, self.game.deck[h])
            if i in card_indices:
                wasClued[i] = card.clued
                clueIndex: int = len(card_indices) - card_indices.index(i) - 1
                card.clued = True
                card.setMustBeValue(value)
                if card.color is not None:
                    playingValue: int
                    playingValue = len(self.game.playedCards[card.color]) + 1
                    if card.value == playingValue:
                        card.setIsPlayable(True)
                    elif card.value <= playingValue:
                        card.setIsWorthless(True)
                elif value < self.lowestPlayableValue:
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
                        elif clueIndex < numAllColors:
                            for c in laterColors:
                                if card.cannotBeColor(c):
                                    continue
                                card.playColors.append(c)
                        else:
                            card.playWorthless = True
            else:
                card.setCannotBeValue(value)
        for i, h in enumerate(hand):
            card = cast(CardKnowledge, self.game.deck[h])
            if i in card_indices:
                if criticalState or criticalState is None:
                    if not wasClued[i]:
                        card.cluedAsDiscard = True
                        card.playWorthless = False
                        for c in criticalColors:
                            if card.cannotBeColor(c):
                                continue
                            card.discardColors.append(c)
                        card.playColors.clear()
                        card.setIsValuable(True, strict=False)
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
                    if card.color is None:
                        card.cluedAsPlay = True
                    else:
                        for h in hand:
                            taggedCard: CardKnowledge
                            taggedCard = cast(CardKnowledge, self.game.deck[h])
                            if taggedCard.color == card.color:
                                taggedCard.cluedAsPlay = True
                                taggedCard.valuable = None
                                taggedCard.discardValues.clear()
                else:
                    card.cluedAsPlay = True
        for h in hand:
            card = cast(CardKnowledge, self.game.deck[h])
            card.update(False)

        clueLog = ClueState(self.game.turnCount, criticalClue,
                            hand[:], card_indices[:], wasClued[:],
                            discard, HandState.Worthless in handState,
                            value=value,
                            play_colors=possibleColors[:],
                            later_colors=laterColors[:],
                            discard_color=criticalColors[:])
        self.clueLog[to].append(clueLog)

    def pleaseObserveAfterMove(self) -> None:
        pass

    def pleaseMakeMove(self, can_clue: bool, can_discard: bool) -> None:
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
        if stage == GameStage.End:
            if can_clue and self.maybeSpendEndGameClue():
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
