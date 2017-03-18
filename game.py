from typing import Any, Dict, List, Optional, Type

from bot import bot
from bot.card import Card
from bot.player import Player
from enums import Clue, Color, Suit, Rank, Value, Variant


class Game:
    def __init__(self,
                 connection: Any,
                 variant: Variant,
                 names: List[str],
                 botPosition: int,
                 botCls: Type['bot.Bot'],
                 **kwargs) -> None:
        self.connection: Any = connection
        self.variant: Variant  = variant
        self.numPlayers: int = len(names)
        self.botPosition: int = botPosition
        self.bot: bot.Bot
        self.bot = botCls(self, botPosition, names[botPosition], **kwargs)
        self.players: List[Player] = [self.bot.create_player(p, names[p])
                                      for p in range(self.numPlayers)]
        self.turnCount: int = -1
        self.deckCount: int = -1
        self.scoreCount: int = 0
        self.clueCount: int = 8
        self.strikeCount: int = 0
        self.currentPlayer: int = -1
        self.deck: Dict[int, Card] = {}
        self.discards: List[Card] = []
        self.playedCards: Dict[Color, List[Card]]
        self.playedCards = {c: [] for c in variant.pile_colors}
        self.actionLog: List[str] = []

    def send(self, type: str, resp: Dict[str, Any]) -> None:
        self.connection.emit('message', {'type': type, 'resp': resp})

    def received(self, type: str, resp: Dict[str, Any]) -> None:
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

    def handle_notify(self, data: Dict[str, Any]) -> None:
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
            self.card_played(data['which']['order'], data['which']['suit'],
                             data['which']['rank'])
        elif type == 'discard':
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
            self.game_ended()
        else:
            raise Exception()

    def message_received(self, message: str) -> None:
        self.actionLog.append(message)
        print(message)

    def decide_action(self, can_clue: bool, can_discard: bool) -> None:
        self.bot.decide_move(can_clue, can_discard)

    def deck_draw(self,
                  player: int,
                  deckidx: int,
                  color: Optional[Color],
                  value: Optional[Value]) -> None:
        if player == self.botPosition:
            card = self.bot.create_own_card(deckidx)
            self.deck[deckidx] = card
            self.bot.drew_card(deckidx)
        else:
            color = Suit(color).color(self.variant)
            value = Rank(value).value_()
            card = self.bot.create_player_card(player, deckidx, color, value)
            self.deck[deckidx] = card
            self.players[player].drew_card(deckidx)
            self.bot.someone_drew(player, deckidx)

    def set_deck_size(self, size: int) -> None:
        self.deckCount = size

    def _card_shown(self, deckidx: int, suit: int, rank: int) -> None:
        card: Card = self.deck[deckidx]
        color: Color = Suit(suit).color(self.variant)
        value: Value = Rank(rank).value_()
        card.suit = color
        card.rank = value

    def card_played(self, deckidx: int, suit: int, rank: int) -> None:
        self._card_shown(deckidx, suit, rank)
        color = Suit(suit).color(self.variant)
        self.playedCards[color].append(self.deck[deckidx])

        player: Player = self.players[self.currentPlayer]
        pos: int = player.hand.index(deckidx)
        if self.currentPlayer == self.botPosition:
            self.bot.card_played(deckidx, pos)
        else:
            self.bot.someone_played(self.currentPlayer, deckidx, pos)
        player.played_card(deckidx)

    def card_discarded(self, deckidx: int, suit: int, rank: int) -> None:
        self._card_shown(deckidx, suit, rank)
        self.discards.append(deckidx)

        player: Player = self.players[self.currentPlayer]
        pos: int = player.hand.index(deckidx)
        if self.currentPlayer == self.botPosition:
            self.bot.card_discarded(deckidx, pos)
        else:
            self.bot.someone_discard(self.currentPlayer, deckidx, pos)
        player.discarded_card(deckidx)

    def card_revealed(self, deckidx: int, suit: int, rank: int) -> None:
        self._card_shown(deckidx, suit, rank)
        self.bot.card_revealed(deckidx)

    def color_clue_sent(self,
                        from_: int,
                        to: int,
                        suit: int,
                        deckidxs: List[int]) -> None:
        color: Color = Suit(suit).color(self.variant)
        positions: List[int] = []
        i: int
        h: int
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

    def value_clue_sent(self,
                        from_: int,
                        to: int,
                        rank: int,
                        deckidxs: List[int]) -> None:
        value: Value = Rank(rank).value_()
        positions: List[int] = []
        i: int
        h: int
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

    def set_game_data(self, score: int, clues: int) -> None:
        self.clueCount = clues
        self.scoreCount = score

    def striked(self, strikes: int) -> None:
        self.strikeCount = strikes
        self.bot.striked(self.currentPlayer)

    def change_turn(self, player: int, turn_count: int) -> None:
        self.currentPlayer = player
        self.turnCount = turn_count
        self.bot.next_turn(player)

    def game_ended(self) -> None:
        self.bot.game_ended()
