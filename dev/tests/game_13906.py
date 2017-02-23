from enums import Color, Value
from testing.game_testing import GameSimulatorTesting
from dev.bot import Bot


class Game13906(GameSimulatorTesting):
    def test_turn_3(self):
        # Deck size 34, Donald, Clues 5, Score 0
        self.load_game(r'games\13906.json', position=3, turn=3, botcls=Bot)
        self.send_action()
        self.connection.assert_card_played_hand(2)

    def test_turn_7(self):
        # Deck size 33, Donald, Clues 2, Score 1
        self.load_game(r'games\13906.json', position=3, turn=7, botcls=Bot)
        self.send_action()
        self.connection.assert_card_played_hand(0)

    def test_turn_11(self):
        # Deck size 30, Donald, Clues 2, Score 3
        self.load_game(r'games\13906.json', position=3, turn=11, botcls=Bot)
        self.send_action()
        self.connection.assert_clue_color(2, Color.Purple)

    def test_turn_15(self):
        # Deck size 28, Donald, Clues 0, Score 5
        self.load_game(r'games\13906.json', position=3, turn=15, botcls=Bot)
        self.send_action()
        self.connection.assert_card_discarded_hand(0)

    def test_turn_19(self):
        # Deck size 25, Donald, Clues 0, Score 5
        self.load_game(r'games\13906.json', position=3, turn=19, botcls=Bot)
        self.send_action()
        self.connection.assert_card_discarded_hand(2)

