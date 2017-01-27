from enums import Color, Value
from testing.game_testing import GameSimulatorTesting
from dev.bot import Bot


class Game13412(GameSimulatorTesting):
    '''
    Turn 2 - Really bad early save, just play the B1
    Turn 34 - Just play the Y2, don't misreference Y5 >_>
    '''
    def test_turn_2(self):
        # Deck size 34, Bob, Clues 6, Score 0
        self.load_game(r'games\13412.json', position=1, turn=2, botcls=Bot)
        self.send_action()
        #self.connection.assert_clue_value(3, Value.V2)
        self.connection.assert_card_played_hand(3)

    def test_turn_6(self):
        # Deck size 33, Bob, Clues 4, Score 0
        self.load_game(r'games\13412.json', position=1, turn=6, botcls=Bot)
        self.send_action()
        self.connection.assert_card_played_hand(3)

    def test_turn_10(self):
        # Deck size 31, Bob, Clues 3, Score 1
        self.load_game(r'games\13412.json', position=1, turn=10, botcls=Bot)
        self.send_action()
        self.connection.assert_card_played_hand(2)

    def test_turn_14(self):
        # Deck size 28, Bob, Clues 2, Score 4
        self.load_game(r'games\13412.json', position=1, turn=14, botcls=Bot)
        self.send_action()
        self.connection.assert_card_played_hand(0)

    def test_turn_18(self):
        # Deck size 26, Bob, Clues 1, Score 5
        self.load_game(r'games\13412.json', position=1, turn=18, botcls=Bot)
        self.send_action()
        self.connection.assert_card_played_hand(3)

    def test_turn_22(self):
        # Deck size 23, Bob, Clues 1, Score 7
        self.load_game(r'games\13412.json', position=1, turn=22, botcls=Bot)
        self.send_action()
        self.connection.assert_card_played_hand(0)

    def test_turn_26(self):
        # Deck size 20, Bob, Clues 1, Score 9
        self.load_game(r'games\13412.json', position=1, turn=26, botcls=Bot)
        self.send_action()
        self.connection.assert_clue_color(3, Color.Green)

    def test_turn_30(self):
        # Deck size 18, Bob, Clues 0, Score 10
        self.load_game(r'games\13412.json', position=1, turn=30, botcls=Bot)
        self.send_action()
        self.connection.assert_card_discarded_hand(0)

    def test_turn_34(self):
        # Deck size 16, Bob, Clues 0, Score 10
        self.load_game(r'games\13412.json', position=1, turn=34, botcls=Bot)
        self.send_action()
        #self.connection.assert_card_discarded_hand(0)
        self.connection.assert_card_played_hand(3)

    def test_turn_38(self):
        # Deck size 12, Bob, Clues 3, Score 12
        self.load_game(r'games\13412.json', position=1, turn=38, botcls=Bot)
        self.send_action()
        self.connection.assert_card_played_hand(2)

    def test_turn_42(self):
        # Deck size 8, Bob, Clues 5, Score 14
        self.load_game(r'games\13412.json', position=1, turn=42, botcls=Bot)
        self.send_action()
        self.connection.assert_card_discarded_hand(2)

    def test_turn_46(self):
        # Deck size 6, Bob, Clues 4, Score 14
        self.load_game(r'games\13412.json', position=1, turn=46, botcls=Bot)
        self.send_action()
        self.connection.assert_clue_color(0, Color.Red)

    def test_turn_50(self):
        # Deck size 4, Bob, Clues 3, Score 15
        self.load_game(r'games\13412.json', position=1, turn=50, botcls=Bot)
        self.send_action()
        self.connection.assert_card_discarded_hand(2)

    def test_turn_54(self):
        # Deck size 1, Bob, Clues 3, Score 17
        self.load_game(r'games\13412.json', position=1, turn=54, botcls=Bot)
        self.send_action()
        self.connection.assert_card_played_hand(3)

    def test_turn_58(self):
        # Deck size 0, Bob, Clues 4, Score 20
        self.load_game(r'games\13412.json', position=1, turn=58, botcls=Bot)
        self.send_action()
        self.connection.assert_card_played_hand(3)

