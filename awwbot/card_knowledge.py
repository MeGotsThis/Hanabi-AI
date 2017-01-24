import color

from bot import card

colors = [color.BLUE, color.GREEN, color.YELLOW, color.RED, color.PURPLE]
maxCards = [0, 3, 2, 2, 2, 1]


class CardKnowledge(card.Card):
    def __init__(self, bot, player, deckPosition, suit, rank):
        super().__init__(bot.game, player, deckPosition, suit, rank)
        self.bot = bot
        self.cantBe = {c: [False] * 6 for c in colors}
        self.color = None
        self.value = None
        self.playable = None
        self.valuable = None  # this means that it saving a card
        self.possibleSaveColors = []
        self.possibleSaveValues = []
        self.likelyPlayableColors = []
        self.likelyPlayableValues = []
        self.likelyPlayableValue = None
        self.worthless = None
        self.clued = False

    def __copy__(self):
        cls = self.__class__
        result = cls.__new__(cls)
        result.__dict__.update(self.__dict__)
        result.cantBe = {c: self.cantBe[c][:] for c in colors}
        return result

    def mustBeColor(self, color):
        return color == self.color

    def mustBeValue(self, value):
        return value == self.value

    def cannotBeColor(self, color):
        if self.color is not None:
            return self.color != color
        for v in range(1, 6):
            if not self.cantBe[color][v]:
                return False
        return True

    def cannotBeValue(self, value):
        if self.value is not None:
            return self.value != value
        for c in colors:
            if not self.cantBe[c][value]:
                return False
        return True

    def setMustBeColor(self, color):
        tot = 0
        for c in colors:
            if c == color:
                continue
            tot += self.setCannotBeColor(c)
        self.color = color
        return tot

    def setMustBeValue(self, value):
        tot = 0
        for v in range(1, 6):
            if v == value:
                continue
            tot += self.setCannotBeValue(v)
        self.value = value
        return tot

    def setCannotBeColor(self, color):
        tot = 0
        for v in range(1, 6):
            if not self.cantBe[color][v]:
                tot += 1
                self.cantBe[color][v] = True
        return tot

    def setCannotBeValue(self, value):
        tot = 0
        for c in colors:
            if not self.cantBe[c][value]:
                tot += 1
                self.cantBe[c][value] = True
        return tot

    def setIsPlayable(self, knownPlayable):
        for c in colors:
            playableValue = len(self.bot.game.playedCards[c]) + 1
            for v in range(1, 6):
                if self.cantBe[c][v]:
                    continue
                if (v == playableValue) != knownPlayable:
                    self.cantBe[c][v] = True
        self.playable = knownPlayable

    def setIsValuable(self, knownValuable):
        for c in colors:
            for v in range(1, 6):
                if self.cantBe[c][v]:
                    continue
                if self.bot.isValuable(c, v) != knownValuable:
                    self.cantBe[c][v] = True
        self.playable = knownValuable

    def setIsWorthless(self, knownWorthless):
        for c in colors:
            for v in range(1, 6):
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

        yesP, noP = False, False
        yesV, noV = False, False
        yesW, noW = False, False
        for c in colors:
            playableValue = len(self.bot.game.playedCards[c]) + 1
            for v in range(1, 6):
                if self.cantBe[c][v]:
                    continue
                if v < playableValue:
                    noP = True
                    noV = True
                    yesW = True
                elif v == playableValue:
                    yesP = True
                    if not yesV or not noV:
                        count = maxCards[v]
                        if self.bot.botPlayedCount[c][v] == count - 1:
                            yesV = True
                        else:
                            noV = True
                    noW = True
                else:
                    noP = True
                    if not yesV or not noV:
                        if self.bot.isValuable(c, v):
                            yesV = True
                        else:
                            noV = True
                    if not yesW or not noW:
                        if self.bot.isWorthless(c, v):
                            yesW = True
                        else:
                            noW = True
            if yesP and yesV and yesW:
                break

        assert yesP or noP
        assert yesV or noV
        assert yesW or noW

        self.playable = (None if noP else True) if yesP else False
        self.valuable = (None if noV else True) if yesV else False
        self.worthless = (None if noW else True) if yesW else False

        if self.worthless is True:
            assert self.valuable is False
            assert self.playable is False

    def update_valid_canbe(self, useMyEyesight):
        color = self.color
        if color is None:
            for c in colors:
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
            for v in range(1, 6):
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

        self.update_count(useMyEyesight)

    def update_count(self, useMyEyesight):
        if self.color is None or self.value is None:
            restart = False
            for c in colors:
                for v in range(1, 6):
                    if self.cantBe[c][v]:
                        continue
                    total = maxCards[v]
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
