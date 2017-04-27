from enums import Color, Value
from testing.game_testing import GameSimulatorTesting
from multitagbot_v2_2.bot import Bot


class Game13907(GameSimulatorTesting):
    def test_turn_3(self):
        # Deck size 33, Donald, Clues 6, Score 1
        self.load_game(r'games\13907.json', position=3, turn=3, botcls=Bot)
        self.send_action()
        #self.connection.assert_clue_color(1, Color.Green)
        self.connection.assert_clue_color(0, Color.Green)

    def test_turn_7(self):
        # Deck size 31, Donald, Clues 4, Score 3
        self.load_game(r'games\13907.json', position=3, turn=7, botcls=Bot)
        self.send_action()
        self.connection.assert_card_played_hand(2)

    def test_turn_11(self):
        # Deck size 29, Donald, Clues 2, Score 5
        self.load_game(r'games\13907.json', position=3, turn=11, botcls=Bot)
        self.send_action()
        self.connection.assert_clue_color(2, Color.Yellow)

    def test_turn_15(self):
        # Deck size 27, Donald, Clues 1, Score 6
        self.load_game(r'games\13907.json', position=3, turn=15, botcls=Bot)
        self.send_action()
        self.connection.assert_clue_color(0, Color.Purple)

    def test_turn_19(self):
        # Deck size 24, Donald, Clues 1, Score 8
        self.load_game(r'games\13907.json', position=3, turn=19, botcls=Bot)
        self.send_action()
        self.connection.assert_card_played_hand(0)

    def test_turn_23(self):
        # Deck size 21, Donald, Clues 2, Score 9
        self.load_game(r'games\13907.json', position=3, turn=23, botcls=Bot)
        self.send_action()
        self.connection.assert_clue_color(0, Color.Green)

    def test_turn_27(self):
        # Deck size 19, Donald, Clues 1, Score 10
        self.load_game(r'games\13907.json', position=3, turn=27, botcls=Bot)
        self.send_action()
        self.connection.assert_card_played_hand(0)

    def test_turn_31(self):
        # Deck size 16, Donald, Clues 0, Score 12
        self.load_game(r'games\13907.json', position=3, turn=31, botcls=Bot)
        self.send_action()
        self.connection.assert_card_discarded_hand(1)

    def test_turn_35(self):
        # Deck size 13, Donald, Clues 1, Score 14
        self.load_game(r'games\13907.json', position=3, turn=35, botcls=Bot)
        self.send_action()
        self.connection.assert_clue_value(0, Value.V4)

    def test_turn_39(self):
        # Deck size 11, Donald, Clues 1, Score 14
        self.load_game(r'games\13907.json', position=3, turn=39, botcls=Bot)
        self.send_action()
        self.connection.assert_card_discarded_hand(2)

    def test_turn_43(self):
        # Deck size 8, Donald, Clues 2, Score 15
        self.load_game(r'games\13907.json', position=3, turn=43, botcls=Bot)
        self.send_action()
        self.connection.assert_card_played_hand(3)

    def test_turn_47(self):
        # Deck size 6, Donald, Clues 0, Score 17
        self.load_game(r'games\13907.json', position=3, turn=47, botcls=Bot)
        self.send_action()
        self.connection.assert_card_discarded_hand(2)

    def test_turn_51(self):
        # Deck size 3, Donald, Clues 0, Score 19
        self.load_game(r'games\13907.json', position=3, turn=51, botcls=Bot)
        self.send_action()
        self.connection.assert_card_played_hand(1)

