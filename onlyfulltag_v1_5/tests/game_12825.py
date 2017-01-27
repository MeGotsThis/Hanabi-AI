from enums import Color, Value
from testing.game_testing import GameSimulatorTesting
from onlyfulltag_v1_5.bot import Bot


class Game12825(GameSimulatorTesting):
    def test_turn_0(self):
        # Deck size 35, Bob, Clues 8, Score 0
        self.load_game(r'games\12825.json', position=2, turn=0, botcls=Bot)
        self.send_action()
        self.connection.assert_clue_value(1, Value.V1)

    def test_turn_3(self):
        # Deck size 34, Bob, Clues 6, Score 1
        self.load_game(r'games\12825.json', position=2, turn=3, botcls=Bot)
        self.send_action()
        self.connection.assert_card_played_hand(3)

    def test_turn_6(self):
        # Deck size 32, Bob, Clues 5, Score 3
        self.load_game(r'games\12825.json', position=2, turn=6, botcls=Bot)
        self.send_action()
        self.connection.assert_card_played_hand(2)

    def test_turn_9(self):
        # Deck size 30, Bob, Clues 4, Score 5
        self.load_game(r'games\12825.json', position=2, turn=9, botcls=Bot)
        self.send_action()
        self.connection.assert_clue_value(1, Value.V2)

    def test_turn_12(self):
        # Deck size 29, Bob, Clues 2, Score 6
        self.load_game(r'games\12825.json', position=2, turn=12, botcls=Bot)
        self.send_action()
        self.connection.assert_card_played_hand(4)

    def test_turn_15(self):
        # Deck size 28, Bob, Clues 0, Score 7
        self.load_game(r'games\12825.json', position=2, turn=15, botcls=Bot)
        self.send_action()
        self.connection.assert_card_played_hand(2)

    def test_turn_18(self):
        # Deck size 26, Bob, Clues 0, Score 8
        self.load_game(r'games\12825.json', position=2, turn=18, botcls=Bot)
        self.send_action()
        #self.connection.assert_card_discarded_hand(1)
        self.connection.assert_card_played_hand(3)

    def test_turn_21(self):
        # Deck size 24, Bob, Clues 0, Score 9
        self.load_game(r'games\12825.json', position=2, turn=21, botcls=Bot)
        self.send_action()
        #self.connection.assert_card_discarded_hand(1)
        self.connection.assert_card_played_hand(2)

    def test_turn_24(self):
        # Deck size 22, Bob, Clues 1, Score 9
        self.load_game(r'games\12825.json', position=2, turn=24, botcls=Bot)
        self.send_action()
        #self.connection.assert_clue_value(1, Value.V3)
        self.connection.assert_card_played_hand(1)

    def test_turn_27(self):
        # Deck size 20, Bob, Clues 1, Score 10
        self.load_game(r'games\12825.json', position=2, turn=27, botcls=Bot)
        self.send_action()
        #self.connection.assert_clue_value(0, Value.V3)
        self.connection.assert_card_played_hand(1)

    def test_turn_30(self):
        # Deck size 18, Bob, Clues 1, Score 11
        self.load_game(r'games\12825.json', position=2, turn=30, botcls=Bot)
        self.send_action()
        #self.connection.assert_clue_color(0, Color.Purple)
        self.connection.assert_card_played_hand(1)

    def test_turn_33(self):
        # Deck size 16, Bob, Clues 1, Score 12
        self.load_game(r'games\12825.json', position=2, turn=33, botcls=Bot)
        self.send_action()
        #self.connection.assert_card_discarded_hand(3)
        self.connection.assert_card_played_hand(1)

    def test_turn_36(self):
        # Deck size 14, Bob, Clues 1, Score 13
        self.load_game(r'games\12825.json', position=2, turn=36, botcls=Bot)
        self.send_action()
        self.connection.assert_card_played_hand(3)

    def test_turn_39(self):
        # Deck size 12, Bob, Clues 0, Score 15
        self.load_game(r'games\12825.json', position=2, turn=39, botcls=Bot)
        self.send_action()
        self.connection.assert_card_played_hand(4)

    def test_turn_42(self):
        # Deck size 10, Bob, Clues 1, Score 16
        self.load_game(r'games\12825.json', position=2, turn=42, botcls=Bot)
        self.send_action()
        self.connection.assert_card_played_hand(1)

    def test_turn_45(self):
        # Deck size 8, Bob, Clues 0, Score 18
        self.load_game(r'games\12825.json', position=2, turn=45, botcls=Bot)
        self.send_action()
        self.connection.assert_card_discarded_hand(3)

    def test_turn_48(self):
        # Deck size 6, Bob, Clues 0, Score 19
        self.load_game(r'games\12825.json', position=2, turn=48, botcls=Bot)
        self.send_action()
        self.connection.assert_card_played_hand(4)

    def test_turn_51(self):
        # Deck size 4, Bob, Clues 0, Score 20
        self.load_game(r'games\12825.json', position=2, turn=51, botcls=Bot)
        self.send_action()
        self.connection.assert_card_played_hand(1)

    def test_turn_54(self):
        # Deck size 2, Bob, Clues 0, Score 21
        self.load_game(r'games\12825.json', position=2, turn=54, botcls=Bot)
        self.send_action()
        #self.connection.assert_card_discarded_hand(3)
        self.connection.assert_card_played_hand(2)

    def test_turn_57(self):
        # Deck size 0, Bob, Clues 1, Score 23
        self.load_game(r'games\12825.json', position=2, turn=57, botcls=Bot)
        self.send_action()
        self.connection.assert_card_played_hand(1)

