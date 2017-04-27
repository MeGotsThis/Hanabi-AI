from enums import Color, Value
from testing.game_testing import GameSimulatorTesting
from multitagbot_v2_2.bot import Bot


class Game13896(GameSimulatorTesting):
    def test_turn_2(self):
        # Deck size 34, Cathy, Clues 6, Score 0
        self.load_game(r'games\13896.json', position=2, turn=2, botcls=Bot)
        self.send_action()
        #self.connection.assert_card_played_hand(0)
        self.connection.assert_clue_value(3, Value.V1)

    def test_turn_6(self):
        # Deck size 33, Cathy, Clues 3, Score 1
        self.load_game(r'games\13896.json', position=2, turn=6, botcls=Bot)
        self.send_action()
        self.connection.assert_clue_color(3, Color.Purple)

    def test_turn_6_alt(self):
        # Deck size 33, Cathy, Clues 3, Score 1
        self.load_game(r'games\13896.json', position=2, turn=5, botcls=Bot)
        self.send_play_card(2, Color.Blue, Value.V4)
        self.send_action()
        self.connection.assert_clue_color(0, Color.Blue)

    def test_turn_10(self):
        # Deck size 31, Cathy, Clues 1, Score 3
        self.load_game(r'games\13896.json', position=2, turn=10, botcls=Bot)
        self.send_action()
        #self.connection.assert_clue_color(3, Color.Blue)
        self.connection.assert_clue_color(1, Color.Yellow)

    def test_turn_14(self):
        # Deck size 28, Cathy, Clues 0, Score 6
        self.load_game(r'games\13896.json', position=2, turn=14, botcls=Bot)
        self.send_action()
        self.connection.assert_card_played_hand(2)

    def test_turn_18(self):
        # Deck size 25, Cathy, Clues 0, Score 8
        self.load_game(r'games\13896.json', position=2, turn=18, botcls=Bot)
        self.send_action()
        self.connection.assert_card_discarded_hand(0)

    def test_turn_22(self):
        # Deck size 22, Cathy, Clues 0, Score 10
        self.load_game(r'games\13896.json', position=2, turn=22, botcls=Bot)
        self.send_action()
        self.connection.assert_card_discarded_hand(0)

    def test_turn_26(self):
        # Deck size 19, Cathy, Clues 1, Score 11
        self.load_game(r'games\13896.json', position=2, turn=26, botcls=Bot)
        self.send_action()
        self.connection.assert_clue_color(3, Color.Yellow)

    def test_turn_30(self):
        # Deck size 17, Cathy, Clues 0, Score 11
        self.load_game(r'games\13896.json', position=2, turn=30, botcls=Bot)
        self.send_action()
        self.connection.assert_card_discarded_hand(0)

    def test_turn_34(self):
        # Deck size 14, Cathy, Clues 0, Score 13
        self.load_game(r'games\13896.json', position=2, turn=34, botcls=Bot)
        self.send_action()
        self.connection.assert_card_played_hand(2)

    def test_turn_38(self):
        # Deck size 11, Cathy, Clues 0, Score 14
        self.load_game(r'games\13896.json', position=2, turn=38, botcls=Bot)
        self.send_action()
        self.connection.assert_card_discarded_hand(0)

    def test_turn_42(self):
        # Deck size 8, Cathy, Clues 0, Score 16
        self.load_game(r'games\13896.json', position=2, turn=42, botcls=Bot)
        self.send_action()
        self.connection.assert_card_played_hand(1)

    def test_turn_46(self):
        # Deck size 5, Cathy, Clues 1, Score 18
        self.load_game(r'games\13896.json', position=2, turn=46, botcls=Bot)
        self.send_action()
        self.connection.assert_clue_color(0, Color.Blue)

    def test_turn_50(self):
        # Deck size 3, Cathy, Clues 1, Score 19
        self.load_game(r'games\13896.json', position=2, turn=50, botcls=Bot)
        self.send_action()
        self.connection.assert_card_discarded_hand(1)

    def test_turn_54(self):
        # Deck size 1, Cathy, Clues 1, Score 20
        self.load_game(r'games\13896.json', position=2, turn=54, botcls=Bot)
        self.send_action()
        self.connection.assert_card_discarded_hand(1)

    def test_turn_58(self):
        # Deck size 0, Cathy, Clues 4, Score 21
        self.load_game(r'games\13896.json', position=2, turn=58, botcls=Bot)
        self.send_action()
        self.connection.assert_card_played_hand(0)

