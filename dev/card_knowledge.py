from bot import card
from enums import Value


class CardKnowledge(card.Card):
    def __init__(self, bot, player, deckPosition, suit, rank):
        super().__init__(bot.game, player, deckPosition, suit, rank)
        self.bot = bot
        self.cantBe = {c: [False] * 6 for c in self.bot.colors}
        self.color = None
        self.value = None
        self.playable = None
        self.valuable = None
        self.worthless = None
        self.cluedAsDiscard = False
        self.cluedAsClarify = False
        self.cluedAsPlay = False
        self.playWorthless = False
        self.playColors = []
        self.playColorDirect = False
        self.playValue = None
        self.playHold = False
        self.discardWorthless = False
        self.discardColors = []
        self.discardValues = []
        self.discardHold = False
        self.clued = False

    def __copy__(self):
        cls = self.__class__
        result = cls.__new__(cls)
        result.__dict__.update(self.__dict__)
        result.cantBe = {c: self.cantBe[c][:] for c in self.bot.colors}
        return result

    @property
    def maybeColor(self):
        if self.color is not None:
            return self.color
        if self.value is not None:
            if len(self.playColors) == 1:
                return self.playColors[0]
            if len(self.discardColors) == 1:
                return self.discardColors[0]
        return None

    @property
    def maybeValue(self):
        if self.value is not None:
            return self.value
        if self.color is not None:
            if self.playValue is not None:
                return self.playValue
            if len(self.discardValues) == 1:
                return self.discardValues
        return None

    def mustBeColor(self, color):
        return color == self.color

    def mustBeValue(self, value):
        return value == self.value

    def cannotBeColor(self, color):
        if self.color is not None:
            return self.color != color
        for v in self.bot.values:
            if not self.cantBe[color][v]:
                return False
        return True

    def cannotBeValue(self, value):
        if self.value is not None:
            return self.value != value
        for c in self.bot.colors:
            if not self.cantBe[c][value]:
                return False
        return True

    def setMustBeColor(self, color):
        tot = 0
        for c in self.bot.colors:
            if c == color:
                continue
            tot += self.setCannotBeColor(c)
        self.color = color
        return tot

    def setMustBeValue(self, value):
        tot = 0
        for v in self.bot.values:
            if v == value:
                continue
            tot += self.setCannotBeValue(v)
        self.value = value
        return tot

    def setCannotBeColor(self, color):
        tot = 0
        for v in self.bot.values:
            if not self.cantBe[color][v]:
                tot += 1
                self.cantBe[color][v] = True
        return tot

    def setCannotBeValue(self, value):
        tot = 0
        for c in self.bot.colors:
            if not self.cantBe[c][value]:
                tot += 1
                self.cantBe[c][value] = True
        return tot

    def setIsPlayable(self, knownPlayable, *, strict=True):
        if knownPlayable is not None and strict:
            for c in self.bot.colors:
                playableValue = len(self.bot.game.playedCards[c]) + 1
                for v in self.bot.values:
                    if self.cantBe[c][v]:
                        continue
                    if (v == playableValue) != knownPlayable:
                        self.cantBe[c][v] = True
        self.playable = knownPlayable

    def setIsValuable(self, knownValuable, *, strict=True):
        if knownValuable is not None and strict:
            for c in self.bot.colors:
                for v in self.bot.values:
                    if self.cantBe[c][v]:
                        continue
                    if self.bot.isValuable(c, v) != knownValuable:
                        self.cantBe[c][v] = True
        self.valuable = knownValuable

    def setIsWorthless(self, knownWorthless, *, strict=True):
        if knownWorthless is not None and strict:
            for c in self.bot.colors:
                for v in self.bot.values:
                    if self.cantBe[c][v]:
                        continue
                    if self.bot.isWorthless(c, v) != knownWorthless:
                        self.cantBe[c][v] = True
        self.worthless = knownWorthless

    def update(self, useMyEyesight):
        if useMyEyesight:
            self.update_count(useMyEyesight)
        else:
            self.update_valid_canbe(useMyEyesight)

        if self.color is not None and self.value is not None:
            score = len(self.game.playedCards[self.color])
            self.setIsPlayable(score + 1 == self.value)
            self.setIsWorthless(
                self.value <= len(self.game.playedCards[self.color])
                or self.value > self.bot.maxPlayValue[self.color])

            self.playColors.clear()
            self.discardColors.clear()
            self.playValue = None
            self.discardValues.clear()
            self.playHold = False
            self.playWorthless = False
        elif self.color is not None:
            if self.bot.colorComplete[self.color]:
                self.setIsWorthless(True)
            if self.bot.colorComplete[self.color]:
                self.setIsWorthless(True)
            self.playable = None
            score = len(self.game.playedCards[self.color])
            for v in self.discardValues[:]:
                if self.cannotBeValue(v):
                    self.discardValues.remove(v)
                    continue
                if self.bot.isCluedSomewhere(self.color, v, self.player):
                    self.discardValues.remove(v)
                    continue
                if score >= v:
                    self.discardValues.remove(v)
                    continue
            self.playColors.clear()
            self.discardColors.clear()
        elif self.value is not None:
            if self.value < self.bot.lowestPlayableValue:
                self.setIsPlayable(False)
                self.setIsWorthless(True)
            elif self.value == self.bot.lowestPlayableValue:
                if not self.playWorthless and self.clued:
                    self.setIsPlayable(True, strict=False)
                    self.setIsWorthless(None)
            else:
                self.setIsPlayable(None)
                self.setIsWorthless(None)
            self.playValue = None
            if self.worthless:
                self.playColors.clear()
            else:
                for c in self.playColors[:]:
                    if self.cannotBeColor(c):
                        self.playColors.remove(c)
                        continue
                    if self.bot.isCluedSomewhere(c, self.value, self.player):
                        self.playColors.remove(c)
                        continue
                    if len(self.game.playedCards[c]) >= self.value:
                        self.playColors.remove(c)
                        continue
            for c in self.discardColors[:]:
                if self.cannotBeColor(c):
                    self.discardColors.remove(c)
                    continue
                if self.bot.isCluedSomewhere(c, self.value, self.player):
                    self.discardColors.remove(c)
                    continue
                if len(self.game.playedCards[c]) >= self.value:
                    self.discardColors.remove(c)
                    continue
            self.playValue = None
            self.discardValues.clear()
        if self.playable is None and self.canBePlayable():
            self.setIsPlayable(True, strict=False)
            self.setIsWorthless(None)

        if self.worthless is True:
            self.valuable = False
            self.playable = False

        assert not self.playColors or not self.discardColors,\
            (self.playColors, self.discardColors)
        assert not self.playValue or not self.discardValues,\
            (self.playValue, self.discardValues)
        assert not self.playWorthless or not self.discardWorthless,\
            (self.playWorthless, self.discardWorthless)
        assert not self.playHold or not self.discardHold,\
            (self.playHold, self.discardHold)
        assert not self.playColors or not self.playValue,\
            (self.playColors, self.playValue)
        assert not self.discardColors or not self.discardValues,\
            (self.discardColors, self.discardValues)
        assert not self.playWorthless or not self.playHold,\
            (self.playWorthless, self.playHold)

    def canBePlayable(self):
        if self.worthless or self.playWorthless:
            return False
        if self.cluedAsPlay:
            if self.value is not None:
                if self.value == Value.V5:
                    for c in self.bot.colors:
                        if self.cantBe[c][5]:
                            continue
                        if len(self.game.playedCards[c]) != 4:
                            return False
                    return True
                for c in self.bot.colors:
                    if len(self.game.playedCards[c]) == self.value - 1:
                        break
                else:
                    return False
                if self.playColors:
                    for c in self.playColors:
                        if len(self.game.playedCards[c]) < self.value - 1:
                            break
                    else:
                        if self.playColors:
                            return True
            elif self.color is not None:
                score = len(self.game.playedCards[self.color])
                if self.playValue is not None:
                    return self.playValue == score + 1
                else:
                    return False
        if self.cluedAsDiscard:
            if self.value is not None:
                for c in self.discardColors:
                    if len(self.game.playedCards[c]) < self.value - 1:
                        break
                else:
                    if self.discardColors:
                        return True
            elif self.color is not None:
                score = len(self.game.playedCards[self.color])
                if len(self.discardValues) == 1:
                    if self.discardValues[0] == score + 1:
                        return True
                elif not self.discardValues:
                    return True
        return False

    def update_valid_canbe(self, useMyEyesight):
        color = self.color
        if color is None:
            for c in self.bot.colors:
                if self.cannotBeColor(c):
                    continue
                elif color is None:
                    color = c
                else:
                    color = None
                    break
            if color is not None:
                self.setMustBeColor(color)

        value = self.value
        if value is None:
            for v in self.bot.values:
                if self.cannotBeValue(v):
                    continue
                elif value is None:
                    value = v
                else:
                    value = None
                    break
            if value is not None:
                self.setMustBeValue(value)

        assert color == self.color
        assert value == self.value
        assert (self.color is None or self.suit is None
                or self.suit == self.color)
        assert (self.value is None or self.rank is None
                or self.rank == self.value)

        self.update_count(useMyEyesight)

    def update_count(self, useMyEyesight):
        if self.color is None or self.value is None:
            restart = False
            for c in self.bot.colors:
                for v in self.bot.values:
                    if self.cantBe[c][v]:
                        continue
                    total = v.num_copies
                    played = self.bot.playedCount[c][v]
                    if useMyEyesight:
                        held = self.bot.eyeSightCount[c][v]
                    else:
                        held = self.bot.locatedCount[c][v]
                    assert played + held <= total
                    if played + held == total:
                        self.cantBe[c][v] = True
                        restart = True
            if restart:
                self.update_valid_canbe(useMyEyesight)
