from enums import Color, Value
from testing.game_testing import GameSimulatorTesting
from multitagbot_v2_2.bot import Bot


class Game13516(GameSimulatorTesting):
    def test_turn_3(self):
        # Deck size 34, Donald, Clues 5, Score 0
        self.load_game(r'games\13516.json', position=3, turn=3, botcls=Bot)
        self.send_action()
        self.connection.assert_card_played_hand(0)

    def test_turn_7(self):
        # Deck size 32, Donald, Clues 3, Score 2
        self.load_game(r'games\13516.json', position=3, turn=7, botcls=Bot)
        self.send_action()
        self.connection.assert_clue_value(1, Value.V1)

    def test_turn_11(self):
        # Deck size 29, Donald, Clues 4, Score 3
        self.load_game(r'games\13516.json', position=3, turn=11, botcls=Bot)
        self.send_action()
        self.connection.assert_card_discarded_hand(2)

    def test_turn_15(self):
        # Deck size 26, Donald, Clues 5, Score 4
        self.load_game(r'games\13516.json', position=3, turn=15, botcls=Bot)
        self.send_action()
        self.connection.assert_clue_color(1, Color.Yellow)

    def test_turn_19(self):
        # Deck size 25, Donald, Clues 2, Score 5
        self.load_game(r'games\13516.json', position=3, turn=19, botcls=Bot)
        self.send_action()
        #self.connection.assert_clue_color(2, Color.Yellow)
        self.assertTrue(
            self.bot.doesCardMatchHand(self.game.players[2].hand[3]))
        self.assertFalse(
            self.bot.doesCardMatchHand(self.game.players[2].hand[1]))
        self.assertTrue(
            self.bot.doesCardMatchHand(self.game.players[1].hand[3]))
        self.assertFalse(
            self.bot.doesCardMatchHand(self.game.players[1].hand[1]))
        self.connection.assert_not_clue_color(2, Color.Yellow)
        self.connection.assert_card_discarded_hand(2)

    def test_turn_23(self):
        # Deck size 23, Donald, Clues 0, Score 7
        self.load_game(r'games\13516.json', position=3, turn=23, botcls=Bot)
        self.send_action()
        self.connection.assert_card_played_hand(1)

    def test_turn_27(self):
        # Deck size 20, Donald, Clues 1, Score 8
        self.load_game(r'games\13516.json', position=3, turn=27, botcls=Bot)
        self.send_action()
        self.connection.assert_card_played_hand(3)
        self.assertTrue(self.game.deck[self.bot.hand[0]].playWorthless)

    def test_turn_31(self):
        # Deck size 17, Donald, Clues 0, Score 11
        self.load_game(r'games\13516.json', position=3, turn=31, botcls=Bot)
        self.send_action()
        #self.connection.assert_card_played_hand(0)
        self.assertTrue(self.game.deck[self.bot.hand[0]].playWorthless)
        card = self.game.deck[self.bot.hand[0]]
        self.connection.assert_card_discarded_hand(0)

    def test_turn_35(self):
        # Deck size 14, Donald, Clues 1, Score 12
        self.load_game(r'games\13516.json', position=3, turn=35, botcls=Bot)
        self.send_action()
        self.connection.assert_clue_value(0, Value.V3)

    def test_turn_35_alternate(self):
        # Deck size 14, Donald, Clues 1, Score 12
        self.load_game(r'games\13516.json', position=3, turn=33, botcls=Bot)
        self.send_value_clue(3, Value.V3)
        self.send_discard_card(3, Color.Blue, Value.V2)
        self.send_action()
        self.connection.assert_clue_color(0, Color.Red)

    def test_turn_39(self):
        # Deck size 12, Donald, Clues 0, Score 13
        self.load_game(r'games\13516.json', position=3, turn=39, botcls=Bot)
        self.send_action()
        self.connection.assert_card_played_hand(2)

    def test_turn_43(self):
        # Deck size 8, Donald, Clues 0, Score 17
        self.load_game(r'games\13516.json', position=3, turn=43, botcls=Bot)
        self.send_action()
        self.connection.assert_card_discarded_hand(0)

    def test_turn_47(self):
        # Deck size 6, Donald, Clues 0, Score 17
        self.load_game(r'games\13516.json', position=3, turn=47, botcls=Bot)
        self.send_action()
        self.connection.assert_card_played_hand(0)

    def test_turn_51(self):
        # Deck size 4, Donald, Clues 0, Score 18
        self.load_game(r'games\13516.json', position=3, turn=51, botcls=Bot)
        self.send_action()
        self.connection.assert_card_discarded_hand(0)

    def test_turn_55(self):
        # Deck size 1, Donald, Clues 2, Score 20
        self.load_game(r'games\13516.json', position=3, turn=55, botcls=Bot)
        self.send_action()
        self.connection.assert_card_played_hand(2)

    def test_turn_59(self):
        # Deck size 0, Donald, Clues 3, Score 23
        self.load_game(r'games\13516.json', position=3, turn=59, botcls=Bot)
        self.send_action()
        #self.connection.assert_card_discarded_hand(1)
        #self.connection.assert_card_discarded_hand(3)
        self.connection.assert_clue_value(2, Value.V2)
