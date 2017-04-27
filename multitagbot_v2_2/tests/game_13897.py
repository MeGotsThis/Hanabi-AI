from enums import Color, Value
from testing.game_testing import GameSimulatorTesting
from multitagbot_v2_2.bot import Bot


class Game13897(GameSimulatorTesting):
    def test_turn_3(self):
        # Deck size 30, Bob, Clues 5, Score 0
        self.load_game(r'games\13897.json', position=1, turn=3, botcls=Bot)
        self.send_action()
        self.connection.assert_card_played_hand(1)

    def test_turn_3_alt(self):
        # Deck size 30, Bob, Clues 5, Score 0
        self.load_game(r'games\13897.json', position=1, turn=1, botcls=Bot)
        self.send_color_clue(1, Color.Yellow)
        self.send_color_clue(2, Color.Red)
        self.send_action()
        #self.connection.assert_card_played_hand(1)
        self.connection.assert_clue_value(3, Value.V1)

    def test_turn_8(self):
        # Deck size 28, Bob, Clues 3, Score 1
        self.load_game(r'games\13897.json', position=1, turn=8, botcls=Bot)
        self.send_action()
        self.connection.assert_clue_color(2, Color.Yellow)

    def test_turn_13(self):
        # Deck size 26, Bob, Clues 0, Score 3
        self.load_game(r'games\13897.json', position=1, turn=13, botcls=Bot)
        self.send_action()
        self.connection.assert_card_discarded_hand(0)

    def test_turn_18(self):
        # Deck size 22, Bob, Clues 0, Score 4
        self.load_game(r'games\13897.json', position=1, turn=18, botcls=Bot)
        self.send_action()
        self.connection.assert_card_discarded_hand(1)

    def test_turn_23(self):
        # Deck size 17, Bob, Clues 1, Score 8
        self.load_game(r'games\13897.json', position=1, turn=23, botcls=Bot)
        self.send_action()
        self.connection.assert_clue_value(2, Value.V4)

    def test_turn_28(self):
        # Deck size 13, Bob, Clues 2, Score 10
        self.load_game(r'games\13897.json', position=1, turn=28, botcls=Bot)
        self.send_action()
        #self.connection.assert_clue_color(2, Color.Purple)
        #self.connection.assert_clue_color(4, Color.Yellow)
        #self.connection.assert_clue_value(4, Value.V2)
        self.connection.assert_clue_value(3, Value.V2)

    def test_turn_33(self):
        # Deck size 11, Bob, Clues 0, Score 11
        self.load_game(r'games\13897.json', position=1, turn=33, botcls=Bot)
        self.send_action()
        self.connection.assert_card_played_hand(1)

    def test_turn_38(self):
        # Deck size 7, Bob, Clues 1, Score 13
        self.load_game(r'games\13897.json', position=1, turn=38, botcls=Bot)
        self.send_action()
        self.connection.assert_clue_color(4, Color.Blue)

    def test_turn_43(self):
        # Deck size 5, Bob, Clues 0, Score 14
        self.load_game(r'games\13897.json', position=1, turn=43, botcls=Bot)
        self.send_action()
        self.connection.assert_card_played_hand(3)

    def test_turn_48(self):
        # Deck size 1, Bob, Clues 1, Score 17
        self.load_game(r'games\13897.json', position=1, turn=48, botcls=Bot)
        self.send_action()
        self.connection.assert_card_played_hand(0)

    def test_turn_53(self):
        # Deck size 0, Bob, Clues 0, Score 20
        self.load_game(r'games\13897.json', position=1, turn=53, botcls=Bot)
        self.send_action()
        self.connection.assert_card_discarded_hand(1)

