from enums import Color, Value
from testing.game_testing import GameSimulatorTesting
from multitagbot_v1_0.bot import Bot


class Game12825(GameSimulatorTesting):
    def test_turn_0(self):
        # Deck size 35, Bob, Clues 8, Score 0
        self.load_game(r'games\12825.json', position=2, turn=0, botcls=Bot)
        self.send_action()
        self.connection.assert_clue_value(1, Value.V1)

    def test_turn_1(self):
        # Deck size 35, Bob, Clues 7, Score 0
        self.load_game(r'games\12825.json', position=2, turn=1, botcls=Bot)
        self.assertCountEqual(
            self.game.deck[self.game.players[1].hand[0]].playColors,
            [Color.Blue, Color.Green, Color.Yellow, Color.Red, Color.Purple])
        self.assertIsNone(
            self.game.deck[self.game.players[1].hand[0]].playValue)
        self.assertCountEqual(
            self.game.deck[self.game.players[1].hand[3]].playColors,
            [Color.Blue, Color.Green, Color.Yellow, Color.Red, Color.Purple])
        self.assertCountEqual(
            self.game.deck[self.game.players[1].hand[4]].playColors,
            [Color.Blue, Color.Green, Color.Yellow, Color.Red, Color.Purple])

    def test_turn_1_1(self):
        # Deck size 35, Bob, Clues 7, Score 0
        self.load_game(r'games\12825.json', position=1, turn=1, botcls=Bot)
        self.assertCountEqual(self.game.deck[self.bot.hand[0]].playColors,
                              [Color.Blue, Color.Green, Color.Yellow, Color.Red, Color.Purple])
        self.assertIsNone(self.game.deck[self.bot.hand[0]].playValue)
        self.assertCountEqual(self.game.deck[self.bot.hand[0]].playColors,
                              [Color.Blue, Color.Green, Color.Yellow, Color.Red, Color.Purple])
        self.assertCountEqual(self.game.deck[self.bot.hand[0]].playColors,
                              [Color.Blue, Color.Green, Color.Yellow, Color.Red, Color.Purple])

    def test_turn_2_1(self):
        # Deck size 35, Bob, Clues 6, Score 0
        self.load_game(r'games\12825.json', position=1, turn=2, botcls=Bot)
        self.assertCountEqual(self.game.deck[self.bot.hand[0]].playColors,
                              [Color.Blue, Color.Yellow, Color.Red])
        self.assertIsNone(self.game.deck[self.bot.hand[0]].playValue)
        self.assertCountEqual(self.game.deck[self.bot.hand[3]].playColors,
                              [Color.Blue, Color.Yellow, Color.Red])
        self.assertCountEqual(self.game.deck[self.bot.hand[4]].playColors,
                              [Color.Blue, Color.Yellow, Color.Red])

    def test_turn_3_1(self):
        # Deck size 34, Bob, Clues 6, Score 1
        self.load_game(r'games\12825.json', position=1, turn=3, botcls=Bot)
        self.assertCountEqual(self.game.deck[self.bot.hand[0]].playColors,
                              [Color.Blue, Color.Red])
        self.assertCountEqual(self.game.deck[self.bot.hand[3]].playColors,
                              [Color.Blue, Color.Red])

    def test_turn_3(self):
        # Deck size 34, Bob, Clues 6, Score 1
        self.load_game(r'games\12825.json', position=2, turn=3, botcls=Bot)
        self.assertTrue(self.game.deck[self.bot.hand[1]].playWorthless)
        self.assertCountEqual(self.game.deck[self.bot.hand[2]].playColors,
                              [Color.Green, Color.Purple])
        self.assertCountEqual(self.game.deck[self.bot.hand[3]].playColors,
                              [Color.Green, Color.Purple])
        self.send_action()
        self.connection.assert_card_played_hand(3)

    def test_turn_5(self):
        # Deck size 33, Bob, Clues 5, Score 2
        self.load_game(r'games\12825.json', position=2, turn=5, botcls=Bot)
        self.assertTrue(self.game.deck[self.bot.hand[1]].playWorthless)
        self.assertCountEqual(self.game.deck[self.bot.hand[2]].playColors,
                              [Color.Purple])

    def test_turn_5_1(self):
        # Deck size 33, Bob, Clues 5, Score 2
        self.load_game(r'games\12825.json', position=1, turn=5, botcls=Bot)
        self.assertTrue(self.game.deck[self.bot.hand[1]])
        card = self.game.deck[self.bot.hand[0]]
        self.assertCountEqual(self.game.deck[self.bot.hand[0]].playColors,
                              [])
        self.assertCountEqual(self.game.deck[self.bot.hand[3]].playColors,
                              [Color.Blue])
        self.assertEqual(self.game.deck[self.bot.hand[0]].playColors,
                              [])
        self.assertEqual(self.game.deck[self.bot.hand[4]].playValue, 2)
        self.assertEqual(self.game.deck[self.bot.hand[1]].playValue, 3)
        self.send_action()
        self.connection.assert_card_played_hand(3)

    def test_turn_6(self):
        # Deck size 32, Bob, Clues 5, Score 3
        self.load_game(r'games\12825.json', position=2, turn=6, botcls=Bot)
        self.send_action()
        self.connection.assert_card_played_hand(2)
