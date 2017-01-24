from testing.game_testing import GameSimulatorTesting
from onlyfulltag_v1_0.bot import Bot


class Game12689(GameSimulatorTesting):
    def test_turn_24(self):
        # Deck size 25, Bob, Clues 0, Score 4
        self.load_game('games/12689.json', position=2, turn=24, botcls=Bot)
        self.send_action()
        self.connection.assert_not_card_discarded(22)

    def test_turn_42(self):
        # Deck size 12, Bob, Clues 1, Score 11
        self.load_game('games/12689.json', position=2, turn=42, botcls=Bot)
        self.send_action()
        self.connection.assert_not_clue_value(0, 3)
