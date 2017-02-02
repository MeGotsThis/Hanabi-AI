from enums import Color, Value
from testing.game_testing import GameSimulatorTesting
from dev.bot import Bot


class Game13515(GameSimulatorTesting):
    def test_turn_0(self):
        # Deck size 34, Bob, Clues 8, Score 0
        self.load_game(r'games\13515.json', position=1, turn=0, botcls=Bot)
        self.send_action()
        self.connection.assert_clue_value(2, Value.V1)

    def test_turn_4(self):
        # Deck size 33, Bob, Clues 5, Score 1
        self.load_game(r'games\13515.json', position=1, turn=4, botcls=Bot)
        self.send_action()
        #self.connection.assert_clue_value(2, Value.V3)
        self.connection.assert_clue_color(2, Color.Yellow)

    def test_turn_8(self):
        # Deck size 31, Bob, Clues 3, Score 3
        self.load_game(r'games\13515.json', position=1, turn=8, botcls=Bot)
        self.send_action()
        self.connection.assert_card_played_hand(3)

    def test_turn_12(self):
        # Deck size 28, Bob, Clues 3, Score 5
        self.load_game(r'games\13515.json', position=1, turn=12, botcls=Bot)
        self.send_action()
        self.connection.assert_card_played_hand(0)

    def test_turn_16(self):
        # Deck size 26, Bob, Clues 1, Score 7
        self.load_game(r'games\13515.json', position=1, turn=16, botcls=Bot)
        self.send_action()
        self.assertTrue(self.game.deck[self.bot.hand[0]].cluedAsPlay)
        self.assertCountEqual(self.game.deck[self.bot.hand[0]].playColors,
                              [Color.RED])
        self.connection.assert_card_discarded_hand(1)

    def test_turn_20(self):
        # Deck size 23, Bob, Clues 2, Score 8
        self.load_game(r'games\13515.json', position=1, turn=20, botcls=Bot)
        self.send_action()
        self.connection.assert_card_discarded_hand(1)

    def test_turn_24(self):
        # Deck size 22, Bob, Clues 0, Score 8
        self.load_game(r'games\13515.json', position=1, turn=24, botcls=Bot)
        self.send_action()
        self.connection.assert_card_played_hand(3)

    def test_turn_28(self):
        # Deck size 19, Bob, Clues 0, Score 10
        self.load_game(r'games\13515.json', position=1, turn=28, botcls=Bot)
        self.send_action()
        self.connection.assert_card_discarded_hand(3)

    def test_turn_32(self):
        # Deck size 16, Bob, Clues 1, Score 11
        self.load_game(r'games\13515.json', position=1, turn=32, botcls=Bot)
        self.send_action()
        self.connection.assert_card_played_hand(2)

    def test_turn_36(self):
        # Deck size 13, Bob, Clues 2, Score 13
        self.load_game(r'games\13515.json', position=1, turn=36, botcls=Bot)
        self.send_action()
        self.connection.assert_card_discarded_hand(2)

    def test_turn_40(self):
        # Deck size 10, Bob, Clues 3, Score 14
        self.load_game(r'games\13515.json', position=1, turn=40, botcls=Bot)
        self.send_action()
        self.connection.assert_card_discarded_hand(2)

    def test_turn_44(self):
        # Deck size 8, Bob, Clues 2, Score 15
        self.load_game(r'games\13515.json', position=1, turn=44, botcls=Bot)
        self.send_action()
        self.connection.assert_clue_color(3, Color.Yellow)

    def test_turn_48(self):
        # Deck size 5, Bob, Clues 4, Score 16
        self.load_game(r'games\13515.json', position=1, turn=48, botcls=Bot)
        self.send_action()
        self.connection.assert_clue_color(0, Color.Purple)

    def test_turn_52(self):
        # Deck size 3, Bob, Clues 2, Score 18
        self.load_game(r'games\13515.json', position=1, turn=52, botcls=Bot)
        self.send_action()
        self.connection.assert_card_played_hand(1)

    def test_turn_56(self):
        # Deck size 0, Bob, Clues 1, Score 21
        self.load_game(r'games\13515.json', position=1, turn=56, botcls=Bot)
        self.send_action()
        self.connection.assert_card_discarded_hand(0)

