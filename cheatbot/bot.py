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


class HandState(NamedTuple):
    critical: int
    future: int
    playable: int
    discard: int


class Bot(bot.Bot):
    '''
    Cheat Bot
    '''
    BOT_NAME = 'Cheat Bot'

    def update_game_state(self) -> None:
        c: Color
        v: Color
        discards = {c: [0] * 6 for c in self.game.variant.pile_colors}
        d: int
        for d in self.game.discards:
            ci: CardInfo = gameCards[d]
            discards[ci.color][ci.value] += 1
        self.nextCardPlay: Dict[Color, int]
        self.nextCardPlay = {c: len(self.game.playedCards[c]) + 1
                             for c in self.game.variant.pile_colors}
        self.maxCardPlay: Dict[Color, int]
        self.maxCardPlay = {c: Value.V5 for c in self.game.variant.pile_colors}
        for c in self.game.variant.pile_colors:
            for v in reversed(Value):
                if discards[c][v] < v.num_copies:
                    self.maxCardPlay[c] = v
                    break

    def decide_move(self, can_clue: bool, can_discard: bool) -> None:
        self.update_game_state()
        if can_discard and not can_clue:
            next: int = (self.position + 1) % self.game.numPlayers
            hs: HandState = self.player_hand_state(next)
            if hs.playable == 0 and hs.discard == 0 and hs.future == 0:
                if self.discard_a_card():
                    return

        if self.play_a_card(can_discard):
            return

        maxScore: int = len(self.game.variant.pile_colors) * len(Value)
        moreToPlay: int = maxScore - self.game.scoreCount
        shouldClue: bool = (moreToPlay <= clueTempo[self.game.clueCount]
                            or moreToPlay >= self.game.deckCount + 1)

        if shouldClue:
            if can_clue:
                next: int = (self.position + 1) % self.game.numPlayers
                ci = gameCards[self.game.players[next].hand[0]]
                self.give_value_clue(next, ci.value)
                return
            if can_discard and self.discard_a_card():
                return
        else:
            if can_discard and self.discard_a_card():
                return
            if can_clue and not shouldClue:
                next: int = (self.position + 1) % self.game.numPlayers
                ci = gameCards[self.game.players[next].hand[0]]
                self.give_value_clue(next, ci.value)
                return

        if can_discard and self.force_discard():
            return

        assert False

    def play_a_card(self, can_discard: bool) -> bool:
        ci: CardInfo
        i: int
        h: int
        playWeights: List[int] = [0] * len(self.hand)
        for i, h in enumerate(self.hand):
            ci = gameCards[h]
            if ci.value != self.nextCardPlay[ci.color]:
                continue
            if not can_discard and ci.value == Value.V5:
                continue
            playWeights[i] += 1
            for v in Value:
                if v <= ci.value:
                    continue
                located = self.who_has(ci.color, v)
                if located:
                    playWeights[i] += 1
        maxWeight: int = max(playWeights)
        if maxWeight:
            self.play_card(playWeights.index(maxWeight))
            return True
        return False

    def discard_a_card(self) -> bool:
        selfHandState: HandState = self.player_hand_state(self.position)
        canDiscard: int = selfHandState.discard + selfHandState.future
        possibleDoubleDiscards: List[int] = []
        unlikelyDoubleDiscards: List[int] = []
        nonBestDiscards: List[int] = []
        ci: CardInfo
        i: int
        h: int
        for i, h in enumerate(self.hand):
            ci = gameCards[h]
            if ci.value < self.nextCardPlay[ci.color]:
                self.discard_card(i)
                return True
            if self.card_is_critical(ci.color, ci.value):
                continue
            players: List[int] = self.who_has(ci.color, ci.value)
            if len(players) > 1:
                player: int
                if players[0] != self.position:
                    player = players[0]
                else:
                    player = players[1]
                handState: HandState = self.player_hand_state(player)
                if canDiscard > handState.discard + handState.future:
                    possibleDoubleDiscards.append(i)
                else:
                    unlikelyDoubleDiscards.append(i)
            else:
                nonBestDiscards.append(i)

        if possibleDoubleDiscards:
            self.discard_card(possibleDoubleDiscards[0])
            return True
        if nonBestDiscards:
            indexToDiscard: int = nonBestDiscards[0]
            ci = gameCards[self.hand[indexToDiscard]]
            valueToDiscard: Value = ci.value
            for i in nonBestDiscards[1:0]:
                ci = gameCards[self.hand[i]]
                if ci.value > valueToDiscard:
                    indexToDiscard = i
                    valueToDiscard = ci.value
            self.discard_card(indexToDiscard)
            return True
        if unlikelyDoubleDiscards:
            self.discard_card(unlikelyDoubleDiscards[0])
            return True

        return False

    def force_discard(self) -> bool:
        indexToDiscard: int = 0
        valueToDiscard: Value = gameCards[self.hand[indexToDiscard]].value

        ci: CardInfo
        i: int
        h: int
        for i, h in enumerate(self.hand[1:], 1):
            ci = gameCards[h]
            if ci.value > valueToDiscard:
                indexToDiscard = i
                valueToDiscard = ci.value
        self.discard_card(indexToDiscard)
        return True

    def card_is_critical(self, color: Color, value: Value) -> bool:
        numDiscarded: int = 0
        ci: CardInfo
        d: int
        if (self.nextCardPlay[color] >= value
                or self.maxCardPlay[color] < value):
            return False
        if self.game.variant == Variant.OneOfEach and color == Color.Black:
            return True
        for d in self.game.discards:
            ci = gameCards[d]
            if ci.color == color and ci.value == value:
                numDiscarded += 1
        return value.num_copies == numDiscarded + 1

    def player_hand_state(self, position: int) -> HandState:
        critical = 0
        playable = 0
        future = 0
        discard = 0
        ci: CardInfo
        h: int
        for h in self.hand:
            ci = gameCards[h]
            if self.nextCardPlay[ci.color] == ci.value:
                playable += 1
            if self.card_is_critical(ci.color, ci.value):
                critical += 1
                continue
            if self.nextCardPlay[ci.color] < ci.value:
                future += 1
            else:
                discard += 1
        return HandState(critical, future, playable, discard)

    def who_has(self, color: Color, value: Value) -> List[int]:
        players: List[int] = []
        p: int
        player: Player
        h: int
        for p, player in enumerate(self.game.players):
            for h in player.hand:
                ci: CardInfo = gameCards[h]
                if ci.color == color and ci.value == value:
                    players.append(p)
        return players

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
