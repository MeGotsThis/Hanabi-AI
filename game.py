import time

from enums import Clue, Suit

class Game:
    def __init__(self, connection, variant, names, botPosition, botCls,
                 **kwargs):
        self.connection = connection
        self.variant = variant
        self.numPlayers = len(names)
        self.botPosition = botPosition
        self.bot = botCls(self, botPosition, names[botPosition], **kwargs)
        self.players = [self.bot.create_player(p, names[p])
                        for p in range(self.numPlayers)]
        self.turnCount = 0
        self.deckCount = 0
        self.scoreCount = 0
        self.clueCount = 8
        self.strikeCount = 0
        self.currentPlayer = None
        self.deck = {}
        self.discards = []
        self.playedCards = {c: [] for c in variant.pile_colors}
        self.actionLog = []

    def send(self, type, resp):
        self.connection.emit('message', {'type': type, 'resp': resp})

    def received(self, type, resp):
        if type == 'message':
            self.message_received(resp['text'])
        elif type == 'init':
            raise Exception()
        elif type == 'advanced':
            # Fast UI Animations
            pass
        elif type == 'connected':
            # Players connected to the game
            pass
        elif type == 'notify':
            self.handle_notify(resp)
        elif type == 'action':
            self.decide_action(resp['can_clue'], resp['can_discard'])
        else:
            print(type, resp)
            raise Exception()

    def handle_notify(self, data):
        type = data['type']
        if type == 'draw':
            if 'suit' not in data:
                data['suit'] = None
            if 'rank' not in data:
                data['rank'] = None
            self.deck_draw(data['who'], data['order'], data['suit'],
                           data['rank'])
        elif type == 'draw_size':
            self.set_deck_size(data['size'])
        elif type == 'played':
            # data['index'] == ???
            self.card_played(data['which']['order'], data['which']['suit'],
                             data['which']['rank'])
        elif type == 'discard':
            # data['index'] == ???
            self.card_discarded(data['which']['order'], data['which']['suit'],
                             data['which']['rank'])
        elif type == 'reveal':
            # Shows the final cards when game is over
            self.card_revealed(data['order'], data['suit'], data['rank'])
        elif type == 'clue':
            if data['clue']['type'] == Clue.Suit.value:
                self.color_clue_sent(data['giver'], data['target'],
                                     data['clue']['value'], data['list'])
            elif data['clue']['type'] == Clue.Rank.value:
                self.value_clue_sent(data['giver'], data['target'],
                                     data['clue']['value'], data['list'])
            else:
                raise Exception()
        elif type == 'status':
            self.set_game_data(data['score'], data['clues'])
        elif type == 'strike':
            self.striked(data['num'])
        elif type == 'turn':
            self.change_turn(data['who'], data['num'])
        elif type == 'game_over':
            pass
        else:
            raise Exception()

    def message_received(self, message):
        self.actionLog.append(message)
        print(message)

    def decide_action(self, can_clue, can_discard):
        time.sleep(0.05)
        self.bot.decide_move(can_clue, can_discard)

    def deck_draw(self, player, deckidx, server_color, rank):
        if player == self.botPosition:
            card = self.bot.create_own_card(deckidx)
            self.deck[deckidx] = card
            self.bot.drew_card(deckidx)
        else:
            color = Suit(server_color).color(self.variant)
            card = self.bot.create_player_card(player, deckidx, color, rank)
            self.deck[deckidx] = card
            self.players[player].drew_card(deckidx)
            self.bot.someone_drew(player, deckidx)

    def set_deck_size(self, size):
        self.deckCount = size

    def _card_shown(self, deckidx, server_color, number):
        card = self.deck[deckidx]
        color = Suit(server_color).color(self.variant)
        card.suit = color
        card.rank = number

    def card_played(self, deckidx, server_color, number):
        self._card_shown(deckidx, server_color, number)
        color = Suit(server_color).color(self.variant)
        self.playedCards[color].append(self.deck[deckidx])

        player = self.players[self.currentPlayer]
        pos = player.hand.index(deckidx)
        if self.currentPlayer == self.botPosition:
            self.bot.card_played(deckidx, pos)
        else:
            self.bot.someone_played(self.currentPlayer, deckidx, pos)
        player.played_card(deckidx)

    def card_discarded(self, deckidx, server_color, number):
        self._card_shown(deckidx, server_color, number)
        self.discards.append(deckidx)

        player = self.players[self.currentPlayer]
        pos = player.hand.index(deckidx)
        if self.currentPlayer == self.botPosition:
            self.bot.card_discarded(deckidx, pos)
        else:
            self.bot.someone_discard(self.currentPlayer, deckidx, pos)
        player.discarded_card(deckidx)

    def card_revealed(self, deckidx, server_color, number):
        self._card_shown(deckidx, server_color, number)
        self.bot.card_revealed(deckidx)

    def color_clue_sent(self, from_, to, server_color, deckidxs):
        color = Suit(server_color).color(self.variant)
        positions = []
        for i, h in enumerate(self.players[to].hand):
            if h in deckidxs:
                self.deck[h].got_positive_color(color)
                positions.append(i)
            else:
                self.deck[h].got_negative_color(color)
        if to == self.botPosition:
            self.bot.got_color_clue(from_, color, positions)
        else:
            self.bot.someone_got_color(from_, to, color, positions)

    def value_clue_sent(self, from_, to, value, deckidxs):
        positions = []
        for i, h in enumerate(self.players[to].hand):
            if h in deckidxs:
                self.deck[h].got_positive_value(value)
                positions.append(i)
            else:
                self.deck[h].got_negative_value(value)
        if to == self.botPosition:
            self.bot.got_value_clue(from_, value, positions)
        else:
            self.bot.someone_got_value(from_, to, value, positions)

    def set_game_data(self, score, clues):
        self.clueCount = clues
        self.scoreCount = score

    def striked(self, strikes):
        self.strikeCount = strikes
        self.bot.striked(self.currentPlayer)

    def change_turn(self, player, turn_count):
        self.currentPlayer = player
        self.turnCount = turn_count
        self.bot.next_turn(player)
