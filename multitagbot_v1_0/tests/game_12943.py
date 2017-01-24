from color import BLUE, GREEN, YELLOW, RED, PURPLE
from testing.game_testing import GameSimulatorTesting
from multitagbot_v1_0.bot import Bot


class Game12943(GameSimulatorTesting):
    '''
    Reasons for this test:
    Turn 10 - Clue just the Y1 instead of Y1 + Y3
    Turn 13 - Play Y4 as Y2
    Turn 19 - Play Y3
    Turn 55 - Clue G4 instead of repeating R5
    '''
    def test_turn_1(self):
        # Deck size 35, Cathy, Clues 7, Score 0
        self.load_game(r'games\12943.json', position=2, turn=1, botcls=Bot)
        self.send_action()
        self.connection.assert_clue_value(0, 1)

    def test_turn_4(self):
        # Deck size 34, Cathy, Clues 5, Score 1
        self.load_game(r'games\12943.json', position=2, turn=4, botcls=Bot)
        self.send_action()
        self.connection.assert_card_played_hand(1)

    def test_turn_7(self):
        # Deck size 32, Cathy, Clues 4, Score 3
        self.load_game(r'games\12943.json', position=2, turn=7, botcls=Bot)
        self.send_action()
        self.connection.assert_clue_color(1, GREEN)

    def test_turn_10(self):
        # Deck size 32, Cathy, Clues 1, Score 3
        self.load_game(r'games\12943.json', position=2, turn=10, botcls=Bot)
        self.send_action()
        #self.connection.assert_clue_color(0, YELLOW)
        self.connection.assert_clue_value(0, 1)

    def test_turn_13(self):
        # Deck size 30, Cathy, Clues 0, Score 5
        self.load_game(r'games\12943.json', position=2, turn=13, botcls=Bot)
        self.send_action()
        self.connection.assert_card_played_hand(2)

    def test_turn_16(self):
        # Deck size 28, Cathy, Clues 1, Score 5
        self.load_game(r'games\12943.json', position=2, turn=16, botcls=Bot)
        self.send_action()
        self.connection.assert_card_played_hand(1)

    def test_turn_19(self):
        # Deck size 26, Cathy, Clues 0, Score 7
        self.load_game(r'games\12943.json', position=2, turn=19, botcls=Bot)
        self.send_action()
        self.connection.assert_card_played_hand(0)

    def test_turn_22(self):
        # Deck size 24, Cathy, Clues 1, Score 7
        self.load_game(r'games\12943.json', position=2, turn=22, botcls=Bot)
        self.send_action()
        self.connection.assert_card_played_hand(0)

    def test_turn_25(self):
        # Deck size 22, Cathy, Clues 1, Score 8
        self.load_game(r'games\12943.json', position=2, turn=25, botcls=Bot)
        self.send_action()
        self.connection.assert_card_played_hand(0)

    def test_turn_28(self):
        # Deck size 20, Cathy, Clues 0, Score 10
        self.load_game(r'games\12943.json', position=2, turn=28, botcls=Bot)
        self.send_action()
        self.connection.assert_card_played_hand(4)

    def test_turn_31(self):
        # Deck size 18, Cathy, Clues 0, Score 11
        self.load_game(r'games\12943.json', position=2, turn=31, botcls=Bot)
        self.send_action()
        self.connection.assert_card_played_hand(0)

    def test_turn_34(self):
        # Deck size 16, Cathy, Clues 1, Score 12
        self.load_game(r'games\12943.json', position=2, turn=34, botcls=Bot)
        self.send_action()
        self.connection.assert_card_played_hand(3)

    def test_turn_37(self):
        # Deck size 14, Cathy, Clues 1, Score 12
        self.load_game(r'games\12943.json', position=2, turn=37, botcls=Bot)
        self.send_action()
        self.connection.assert_card_played_hand(4)

    def test_turn_40(self):
        # Deck size 12, Cathy, Clues 0, Score 14
        self.load_game(r'games\12943.json', position=2, turn=40, botcls=Bot)
        self.send_action()
        self.connection.assert_card_discarded_hand(2)

    def test_turn_43(self):
        # Deck size 10, Cathy, Clues 0, Score 15
        self.load_game(r'games\12943.json', position=2, turn=43, botcls=Bot)
        self.send_action()
        self.connection.assert_card_played_hand(3)

    def test_turn_46(self):
        # Deck size 8, Cathy, Clues 0, Score 16
        self.load_game(r'games\12943.json', position=2, turn=46, botcls=Bot)
        self.send_action()
        self.connection.assert_card_played_hand(0)

    def test_turn_49(self):
        # Deck size 6, Cathy, Clues 0, Score 17
        self.load_game(r'games\12943.json', position=2, turn=49, botcls=Bot)
        self.send_action()
        self.connection.assert_card_discarded_hand(0)

    def test_turn_52(self):
        # Deck size 3, Cathy, Clues 2, Score 18
        self.load_game(r'games\12943.json', position=2, turn=52, botcls=Bot)
        self.send_action()
        self.connection.assert_clue_color(0, RED)

    def test_turn_55(self):
        # Deck size 1, Cathy, Clues 3, Score 19
        self.load_game(r'games\12943.json', position=2, turn=55, botcls=Bot)
        self.send_action()
        self.connection.assert_clue_color(1, GREEN)

    def test_turn_58(self):
        # Deck size 0, Cathy, Clues 2, Score 20
        self.load_game(r'games\12943.json', position=2, turn=58, botcls=Bot)
        self.send_action()
        self.connection.assert_card_discarded_hand(0)

