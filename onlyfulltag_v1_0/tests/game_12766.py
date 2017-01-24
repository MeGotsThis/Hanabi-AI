from color import BLUE, GREEN, YELLOW, RED, PURPLE
from testing.game_testing import GameSimulatorTesting
from onlyfulltag_v1_0.bot import Bot


class Game12766(GameSimulatorTesting):
    def test_turn_1(self):
        # Deck size 40, Bob, Clues 7, Score 0
        self.load_game('games/12766.json', position=1, turn=1, botcls=Bot)
        self.send_action()
        self.connection.assert_clue_value(0, 1)

    def test_turn_3(self):
        # Deck size 40, Bob, Clues 5, Score 0
        self.load_game('games/12766.json', position=1, turn=3, botcls=Bot)
        self.send_action()
        self.connection.assert_clue_color(0, BLUE)

    def test_turn_5(self):
        # Deck size 40, Bob, Clues 3, Score 0
        self.load_game('games/12766.json', position=1, turn=5, botcls=Bot)
        self.send_action()
        self.connection.assert_card_played_hand(2)

    def test_turn_7(self):
        # Deck size 38, Bob, Clues 3, Score 2
        self.load_game('games/12766.json', position=1, turn=7, botcls=Bot)
        self.send_action()
        self.connection.assert_clue_color(0, YELLOW)

    def test_turn_9(self):
        # Deck size 38, Bob, Clues 1, Score 2
        self.load_game('games/12766.json', position=1, turn=9, botcls=Bot)
        self.send_action()
        self.connection.assert_card_played_hand(3)

    def test_turn_11(self):
        # Deck size 37, Bob, Clues 0, Score 3
        self.load_game('games/12766.json', position=1, turn=11, botcls=Bot)
        self.send_action()
        self.connection.assert_card_played_hand(1)

    def test_turn_13(self):
        # Deck size 35, Bob, Clues 0, Score 5
        self.load_game('games/12766.json', position=1, turn=13, botcls=Bot)
        self.send_action()
        self.connection.assert_card_played_hand(0)

    def test_turn_15(self):
        # Deck size 33, Bob, Clues 0, Score 7
        self.load_game('games/12766.json', position=1, turn=15, botcls=Bot)
        self.send_action()
        self.connection.assert_card_discarded_hand(1)

    def test_turn_17(self):
        # Deck size 32, Bob, Clues 0, Score 7
        self.load_game('games/12766.json', position=1, turn=17, botcls=Bot)
        self.send_action()
        self.connection.assert_card_discarded_hand(2)

    def test_turn_19(self):
        # Deck size 30, Bob, Clues 2, Score 7
        self.load_game('games/12766.json', position=1, turn=19, botcls=Bot)
        self.send_action()
        self.connection.assert_clue_value(0, 3)

    def test_turn_21(self):
        # Deck size 29, Bob, Clues 2, Score 7
        self.load_game('games/12766.json', position=1, turn=21, botcls=Bot)
        self.send_action()
        self.connection.assert_clue_color(0, BLUE)

    def test_turn_23(self):
        # Deck size 28, Bob, Clues 1, Score 8
        self.load_game('games/12766.json', position=1, turn=23, botcls=Bot)
        self.send_action()
        self.connection.assert_clue_value(0, 4)

    def test_turn_25(self):
        # Deck size 27, Bob, Clues 1, Score 8
        self.load_game('games/12766.json', position=1, turn=25, botcls=Bot)
        self.send_action()
        self.connection.assert_clue_color(0, BLUE)

    def test_turn_27(self):
        # Deck size 26, Bob, Clues 0, Score 9
        self.load_game('games/12766.json', position=1, turn=27, botcls=Bot)
        self.send_action()
        self.connection.assert_card_discarded_hand(2)

    def test_turn_29(self):
        # Deck size 25, Bob, Clues 0, Score 9
        self.load_game('games/12766.json', position=1, turn=29, botcls=Bot)
        self.send_action()
        self.connection.assert_card_discarded_hand(2)

    def test_turn_31(self):
        # Deck size 23, Bob, Clues 2, Score 9
        self.load_game('games/12766.json', position=1, turn=31, botcls=Bot)
        self.send_action()
        self.connection.assert_clue_value(0, 5)

    def test_turn_33(self):
        # Deck size 22, Bob, Clues 1, Score 9
        self.load_game('games/12766.json', position=1, turn=33, botcls=Bot)
        self.send_action()
        self.connection.assert_clue_color(0, BLUE)

    def test_turn_35(self):
        # Deck size 21, Bob, Clues 0, Score 9
        self.load_game('games/12766.json', position=1, turn=35, botcls=Bot)
        self.send_action()
        self.connection.assert_card_discarded_hand(2)

    def test_turn_37(self):
        # Deck size 19, Bob, Clues 2, Score 10
        self.load_game('games/12766.json', position=1, turn=37, botcls=Bot)
        self.send_action()
        self.connection.assert_clue_value(0, 2)

    def test_turn_39(self):
        # Deck size 18, Bob, Clues 1, Score 11
        self.load_game('games/12766.json', position=1, turn=39, botcls=Bot)
        self.send_action()
        self.connection.assert_clue_color(0, PURPLE)

