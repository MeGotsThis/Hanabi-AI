from enums import Color, Value
from testing.game_testing import GameSimulatorTesting
from multitagbot_v1_0.bot import Bot


class Game13157(GameSimulatorTesting):
    def test_turn_0(self):
        # Deck size 40, Bob, Clues 8, Score 0
        self.load_game(r'games\13157.json', position=1, turn=0, botcls=Bot)
        self.send_action()
        self.connection.assert_clue_value(0, Value.V5)

    def test_turn_2(self):
        # Deck size 40, Bob, Clues 6, Score 0
        self.load_game(r'games\13157.json', position=1, turn=2, botcls=Bot)
        self.send_action()
        self.connection.assert_card_played_hand(4)

    def test_turn_4(self):
        # Deck size 38, Bob, Clues 7, Score 1
        self.load_game(r'games\13157.json', position=1, turn=4, botcls=Bot)
        self.send_action()
        self.connection.assert_card_played_hand(0)

    def test_turn_6(self):
        # Deck size 37, Bob, Clues 6, Score 2
        self.load_game(r'games\13157.json', position=1, turn=6, botcls=Bot)
        self.send_action()
        self.connection.assert_card_discarded_hand(0)

    def test_turn_8(self):
        # Deck size 36, Bob, Clues 6, Score 2
        self.load_game(r'games\13157.json', position=1, turn=8, botcls=Bot)
        self.send_action()
        self.connection.assert_card_discarded_hand(2)

    def test_turn_10(self):
        # Deck size 35, Bob, Clues 6, Score 2
        self.load_game(r'games\13157.json', position=1, turn=10, botcls=Bot)
        self.send_action()
        self.connection.assert_card_played_hand(4)

    def test_turn_12(self):
        # Deck size 33, Bob, Clues 7, Score 3
        self.load_game(r'games\13157.json', position=1, turn=12, botcls=Bot)
        self.send_action()
        self.connection.assert_clue_color(0, Color.Red)

    def test_turn_14(self):
        # Deck size 32, Bob, Clues 6, Score 4
        self.load_game(r'games\13157.json', position=1, turn=14, botcls=Bot)
        self.send_action()
        self.connection.assert_card_discarded_hand(3)

    def test_turn_16(self):
        # Deck size 31, Bob, Clues 6, Score 4
        self.load_game(r'games\13157.json', position=1, turn=16, botcls=Bot)
        self.send_action()
        self.connection.assert_card_played_hand(0)

    def test_turn_18(self):
        # Deck size 30, Bob, Clues 5, Score 5
        self.load_game(r'games\13157.json', position=1, turn=18, botcls=Bot)
        self.send_action()
        self.connection.assert_card_played_hand(4)

    def test_turn_20(self):
        # Deck size 29, Bob, Clues 4, Score 6
        self.load_game(r'games\13157.json', position=1, turn=20, botcls=Bot)
        self.send_action()
        self.connection.assert_card_discarded_hand(3)

    def test_turn_22(self):
        # Deck size 28, Bob, Clues 4, Score 6
        self.load_game(r'games\13157.json', position=1, turn=22, botcls=Bot)
        self.send_action()
        self.connection.assert_card_discarded_hand(4)

    def test_turn_24(self):
        # Deck size 26, Bob, Clues 6, Score 6
        self.load_game(r'games\13157.json', position=1, turn=24, botcls=Bot)
        self.send_action()
        self.connection.assert_clue_color(0, Color.Blue)

    def test_turn_26(self):
        # Deck size 25, Bob, Clues 5, Score 7
        self.load_game(r'games\13157.json', position=1, turn=26, botcls=Bot)
        self.send_action()
        self.connection.assert_clue_color(0, Color.Yellow)

    def test_turn_28(self):
        # Deck size 24, Bob, Clues 4, Score 8
        self.load_game(r'games\13157.json', position=1, turn=28, botcls=Bot)
        self.send_action()
        self.connection.assert_card_discarded_hand(4)

    def test_turn_30(self):
        # Deck size 22, Bob, Clues 5, Score 9
        self.load_game(r'games\13157.json', position=1, turn=30, botcls=Bot)
        self.send_action()
        self.connection.assert_card_discarded_hand(4)

    def test_turn_32(self):
        # Deck size 21, Bob, Clues 5, Score 9
        self.load_game(r'games\13157.json', position=1, turn=32, botcls=Bot)
        self.send_action()
        self.connection.assert_card_played_hand(4)

    def test_turn_34(self):
        # Deck size 19, Bob, Clues 7, Score 10
        self.load_game(r'games\13157.json', position=1, turn=34, botcls=Bot)
        self.send_action()
        self.connection.assert_card_discarded_hand(4)

    def test_turn_36(self):
        # Deck size 18, Bob, Clues 7, Score 10
        self.load_game(r'games\13157.json', position=1, turn=36, botcls=Bot)
        self.send_action()
        self.connection.assert_card_discarded_hand(3)

    def test_turn_38(self):
        # Deck size 17, Bob, Clues 7, Score 10
        self.load_game(r'games\13157.json', position=1, turn=38, botcls=Bot)
        self.send_action()
        self.connection.assert_card_discarded_hand(4)

    def test_turn_40(self):
        # Deck size 16, Bob, Clues 7, Score 10
        self.load_game(r'games\13157.json', position=1, turn=40, botcls=Bot)
        self.send_action()
        self.connection.assert_card_discarded_hand(4)

    def test_turn_42(self):
        # Deck size 15, Bob, Clues 7, Score 10
        self.load_game(r'games\13157.json', position=1, turn=42, botcls=Bot)
        self.send_action()
        self.connection.assert_card_discarded_hand(4)

    def test_turn_44(self):
        # Deck size 14, Bob, Clues 7, Score 10
        self.load_game(r'games\13157.json', position=1, turn=44, botcls=Bot)
        self.send_action()
        self.connection.assert_card_discarded_hand(4)

    def test_turn_46(self):
        # Deck size 13, Bob, Clues 7, Score 10
        self.load_game(r'games\13157.json', position=1, turn=46, botcls=Bot)
        self.send_action()
        self.connection.assert_card_discarded_hand(4)

    def test_turn_48(self):
        # Deck size 12, Bob, Clues 7, Score 10
        self.load_game(r'games\13157.json', position=1, turn=48, botcls=Bot)
        self.send_action()
        self.connection.assert_card_played_hand(4)

    def test_turn_50(self):
        # Deck size 11, Bob, Clues 6, Score 11
        self.load_game(r'games\13157.json', position=1, turn=50, botcls=Bot)
        self.send_action()
        self.connection.assert_card_played_hand(4)

    def test_turn_52(self):
        # Deck size 9, Bob, Clues 7, Score 12
        self.load_game(r'games\13157.json', position=1, turn=52, botcls=Bot)
        self.send_action()
        self.connection.assert_card_played_hand(2)

    def test_turn_54(self):
        # Deck size 8, Bob, Clues 6, Score 13
        self.load_game(r'games\13157.json', position=1, turn=54, botcls=Bot)
        self.send_action()
        self.connection.assert_card_played_hand(4)

    def test_turn_56(self):
        # Deck size 7, Bob, Clues 5, Score 14
        self.load_game(r'games\13157.json', position=1, turn=56, botcls=Bot)
        self.send_action()
        self.connection.assert_card_played_hand(3)
        # Why R4 over Y4 hmmm

    def test_turn_58(self):
        # Deck size 5, Bob, Clues 6, Score 15
        self.load_game(r'games\13157.json', position=1, turn=58, botcls=Bot)
        self.send_action()
        self.connection.assert_card_played_hand(3)

    def test_turn_60(self):
        # Deck size 3, Bob, Clues 7, Score 17
        self.load_game(r'games\13157.json', position=1, turn=60, botcls=Bot)
        self.send_action()
        self.connection.assert_card_played_hand(1)

    def test_turn_62(self):
        # Deck size 2, Bob, Clues 7, Score 18
        self.load_game(r'games\13157.json', position=1, turn=62, botcls=Bot)
        self.send_action()
        self.connection.assert_card_played_hand(3)

    def test_turn_64(self):
        # Deck size 1, Bob, Clues 6, Score 19
        self.load_game(r'games\13157.json', position=1, turn=64, botcls=Bot)
        self.send_action()
        self.connection.assert_card_played_hand(1)

    def test_turn_66(self):
        # Deck size 0, Bob, Clues 7, Score 21
        self.load_game(r'games\13157.json', position=1, turn=66, botcls=Bot)
        self.send_action()
        self.connection.assert_card_played_hand(0)

