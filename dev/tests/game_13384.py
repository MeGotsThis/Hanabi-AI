from color import BLUE, GREEN, YELLOW, RED, PURPLE
from testing.game_testing import GameSimulatorTesting
from dev.bot import Bot


class Game13384(GameSimulatorTesting):
    '''
    Turn 22 - Play R3, the other 3 should be known as possible Yellow, Green,
    Purple
    '''
    def test_turn_2(self):
        # Deck size 34, Donald, Clues 6, Score 0
        self.load_game(r'games\13384.json', position=3, turn=2, botcls=Bot)
        self.send_action()
        self.connection.assert_card_played_hand(3)

    def test_turn_6(self):
        # Deck size 31, Donald, Clues 5, Score 3
        self.load_game(r'games\13384.json', position=3, turn=6, botcls=Bot)
        self.send_action()
        self.connection.assert_clue_value(0, 2)

    def test_turn_10(self):
        # Deck size 31, Donald, Clues 1, Score 3
        self.load_game(r'games\13384.json', position=3, turn=10, botcls=Bot)
        self.send_action()
        self.connection.assert_card_played_hand(2)

    def test_turn_14(self):
        # Deck size 27, Donald, Clues 3, Score 5
        self.load_game(r'games\13384.json', position=3, turn=14, botcls=Bot)
        self.send_action()
        self.connection.assert_card_played_hand(2)

    def test_turn_18(self):
        # Deck size 24, Donald, Clues 4, Score 6
        self.load_game(r'games\13384.json', position=3, turn=18, botcls=Bot)
        self.send_action()
        #self.connection.assert_clue_color(2, GREEN)
        self.connection.assert_card_played_hand(0)

    def test_turn_22(self):
        # Deck size 22, Donald, Clues 2, Score 8
        self.load_game(r'games\13384.json', position=3, turn=22, botcls=Bot)
        self.send_action()
        card = self.game.deck[self.bot.hand[2]]
        self.assertCountEqual(card.playColors, [GREEN, YELLOW, PURPLE])
        self.connection.assert_card_played_hand(0)

    def test_turn_26(self):
        # Deck size 20, Donald, Clues 0, Score 9
        self.load_game(r'games\13384.json', position=3, turn=26, botcls=Bot)
        self.send_action()
        self.connection.assert_card_played_hand(0)

    def test_turn_30(self):
        # Deck size 17, Donald, Clues 0, Score 11
        self.load_game(r'games\13384.json', position=3, turn=30, botcls=Bot)
        self.send_action()
        self.connection.assert_card_discarded_hand(0)

    def test_turn_34(self):
        # Deck size 14, Donald, Clues 1, Score 12
        self.load_game(r'games\13384.json', position=3, turn=34, botcls=Bot)
        self.send_action()
        self.connection.assert_clue_color(2, RED)

    def test_turn_38(self):
        # Deck size 12, Donald, Clues 0, Score 13
        self.load_game(r'games\13384.json', position=3, turn=38, botcls=Bot)
        self.send_action()
        self.connection.assert_card_discarded_hand(1)

    def test_turn_42(self):
        # Deck size 9, Donald, Clues 1, Score 14
        self.load_game(r'games\13384.json', position=3, turn=42, botcls=Bot)
        self.send_action()
        self.connection.assert_card_discarded_hand(1)

    def test_turn_46(self):
        # Deck size 6, Donald, Clues 2, Score 15
        self.load_game(r'games\13384.json', position=3, turn=46, botcls=Bot)
        self.send_action()
        self.connection.assert_clue_color(1, PURPLE)

    def test_turn_50(self):
        # Deck size 4, Donald, Clues 0, Score 17
        self.load_game(r'games\13384.json', position=3, turn=50, botcls=Bot)
        self.send_action()
        self.connection.assert_card_discarded_hand(1)

    def test_turn_54(self):
        # Deck size 1, Donald, Clues 1, Score 19
        self.load_game(r'games\13384.json', position=3, turn=54, botcls=Bot)
        self.send_action()
        self.connection.assert_card_played_hand(0)

    def test_turn_58(self):
        # Deck size 0, Donald, Clues 2, Score 22
        self.load_game(r'games\13384.json', position=3, turn=58, botcls=Bot)
        self.send_action()
        self.connection.assert_clue_color(0, GREEN)

