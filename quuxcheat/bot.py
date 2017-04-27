from itertools import chain
from typing import Dict, List, NamedTuple

from bot import bot
from bot.card import Card
from bot.player import Player
from enums import Color, Value, Variant

gameCards: Dict[int, 'CardInfo'] = {}
clueTempo: List[int] = [0, 1, 2, 3, 4, 5, 8, 30, 30]


class CardInfo(NamedTuple):
    color: Color
    value: Value


def countValues(items, value) -> int:
    return len([i for i in items if i == value])


class Bot(bot.Bot):
    '''
    Quuxplusone Cheat Bot
    Ported from: https://github.com/Quuxplusone/Hanabi/blob/master/CheatBot.cc
    '''
    BOT_NAME = 'Quuxplusone Cheat Bot'

    def visibleCopiesOf(self, card: CardInfo) -> int:
        result = 0
        p: Player
        h: int
        for h in chain(*[p.hand for p in self.game.players]):
            ci: CardInfo = gameCards[h]
            result += ci == card
        return result

    def noPlayableCardsVisible(self) -> bool:
        p: Player
        h: int
        for h in chain(*[p.hand for p in self.game.players]):
            card: CardInfo = gameCards[h]
            if len(self.game.playedCards[card.color]) + 1 == card.value.value:
                return False
        return True

    def noWorthlessOrDuplicateCardsVisible(self):
        discards: List[CardInfo] = [gameCards[d] for d in self.game.discards]
        p: Player
        h: int
        for h in chain(*[p.hand for p in self.game.players]):
            card: CardInfo = gameCards[h]
            score: int = len(self.game.playedCards[card.color])
            if card.value.value <= score:
                return False
            v: int
            for v in range(score + 1, card.value.value):
                earlier_card: CardInfo = CardInfo(card.color, Value(v))
                if countValues(discards, earlier_card) == Value(v).num_copies:
                    return False
            if self.visibleCopiesOf(card) >= 2:
                return False
        return True

    def decide_move(self, can_clue: bool, can_discard: bool) -> None:
        maxScore: int = len(self.game.variant.pile_colors) * len(Value)
        stillToGo: int = maxScore - self.game.scoreCount
        endGameNoMoreDiscarding = stillToGo >= self.game.deckCount + 1

        assert 1 <= stillToGo <= 30

        if self.maybePlayLowestPlayableCard():
            return

        if self.noPlayableCardsVisible():
            if self.maybeDiscardWorthlessCard(can_discard):
                return
            if self.maybeDiscardDuplicateCard(can_discard):
                return
            if self.noWorthlessOrDuplicateCardsVisible():
                if self.maybePlayProbabilities(can_discard):
                    return

        tempo: List[int] = [0, 1, 2, 3, 4, 5, 8, 30, 30]
        shouldTemporizeEarly: bool = stillToGo <= tempo[self.game.clueCount]

        if endGameNoMoreDiscarding or shouldTemporizeEarly:
            if self.maybeTemporize(can_clue):
                return
            if self.maybeDiscardWorthlessCard(can_discard):
                return
            if self.maybeDiscardDuplicateCard(can_discard):
                return
            if self.maybePlayProbabilities(can_discard):
                return
        else:
            if self.maybeDiscardWorthlessCard(can_discard):
                return
            if self.maybeDiscardDuplicateCard(can_discard):
                return
            if self.maybeTemporize(can_clue):
                return
            if self.maybePlayProbabilities(can_discard):
                return

        assert not can_clue
        self.discardHighestCard()

    def maybeEnablePlay(self, plus: int) -> bool:
        partner = (self.position + plus) % self.game.numPlayers
        assert partner != self.position

        lowest_value: int = 5
        best_index: int = -1

        i: int
        for i in range(len(self.hand)):
            card: CardInfo = gameCards[self.hand[i]]
            if card.value.value >= lowest_value:
                continue
            if len(self.game.playedCards[card.color]) + 1 != card.value.value:
                continue

            nextCard: CardInfo = CardInfo(card.color, Value(card.value + 1))
            cards: List[CardInfo] = [gameCards[h] for h
                                     in self.game.players[partner].hand]
            if countValues(cards, nextCard) != 0:
                lowest_value = card.value.value
                best_index = i

        if best_index != -1:
            assert 1 <= lowest_value <= 4
            self.play_card(best_index)
            return True
        return False

    def maybePlayLowestPlayableCard(self) -> bool:
        plus: int
        for plus in range(1, self.game.numPlayers):
            if self.maybeEnablePlay(plus):
                return True

        lowest_value: int = 10
        best_index: int = -1
        i: int
        for i in range(len(self.hand)):
            card: CardInfo = gameCards[self.hand[i]]
            if len(self.game.playedCards[card.color]) + 1 == card.value.value:
                if card.value.value < lowest_value:
                    best_index = i
                    lowest_value = card.value.value

        if best_index != -1:
            self.play_card(best_index)
            return True
        return False

    def tryHardToDisposeOf(self, card_index: int, can_discard: bool) -> bool:
        if can_discard:
            self.discard_card(card_index)
            return True
        elif self.game.strikeCount < 1:
            self.play_card(card_index)
            return True
        else:
            return False

    def maybeDiscardWorthlessCard(self, can_discard: bool) -> bool:
        discards: List[CardInfo] = [gameCards[d] for d in self.game.discards]
        cardHand: List[CardInfo] = [gameCards[h] for h in self.hand]
        i: int
        for i in range(len(self.hand)):
            card: CardInfo = gameCards[self.hand[i]]
            score: int = len(self.game.playedCards[card.color])
            if card.value <= score:
                return self.tryHardToDisposeOf(i, can_discard)
            elif countValues(cardHand, card) >= 2:
                return self.tryHardToDisposeOf(i, can_discard)
            else:
                assert card.value.value > score
                for v in range(score + 1, card.value.value):
                    earlier_card: CardInfo = CardInfo(card.color, Value(v))
                    discardCopies: int = countValues(discards, earlier_card)
                    if discardCopies == Value(v).num_copies:
                        return self.tryHardToDisposeOf(i, can_discard)
        return False

    def maybeDiscardDuplicateCard(self, can_discard: bool) -> bool:
        if not can_discard:
            return False

        for i in range(len(self.hand)):
            card: CardInfo = gameCards[self.hand[i]]
            if self.visibleCopiesOf(card) > 1:
                self.discard_card(i)
                return True
        return False

    def maybePlayProbabilities(self, can_discard: bool) -> bool:
        discards: List[CardInfo] = [gameCards[d] for d in self.game.discards]
        if not can_discard:
            return False

        bestGap: int = 0
        bestIndex: int = -1

        i: int
        for i in range(len(self.hand)):
            card: CardInfo = gameCards[self.hand[i]]
            if card.value == Value.V5:
                continue
            if self.game.variant == Variant.OneOfEach:
                if card.color == Color.Black:
                    continue
            score: int = len(self.game.playedCards[card.color])
            assert card.value.value > score

            gap: int = card.value.value - score
            assert gap >= 1
            if gap > bestGap:
                if countValues(discards, card) == card.value.num_copies - 1:
                    pass
                else:
                    bestGap = gap
                    bestIndex = i

        if bestIndex != -1:
            self.discard_card(bestIndex)
            return True
        return False

    def maybeTemporize(self, can_clue: bool) -> bool:
        if not can_clue:
            return False

        nextPlayer: int = (self.position + 1) % self.game.numPlayers
        index: int = self.game.players[nextPlayer].hand[0]
        self.give_value_clue(nextPlayer, gameCards[index].value)
        return True

    def discardHighestCard(self) -> None:
        bestIndex: int = 0
        i: int
        for i in range(len(self.hand)):
            card: CardInfo = gameCards[self.hand[i]]
            if card.value > gameCards[self.hand[bestIndex]].value:
                bestIndex = i
        self.discard_card(bestIndex)

    def someone_drew(self, player: int, deckIdx: int) -> None:
        card: Card = self.game.deck[deckIdx]
        if deckIdx not in gameCards:
            gameCards[deckIdx] = CardInfo(card.suit, card.rank)
        else:
            ci: CardInfo = gameCards[deckIdx]
            assert ci.color == card.suit
            assert ci.value == card.rank

    def game_ended(self):
        gameCards.clear()
