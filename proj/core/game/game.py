from typing import Optional

from .deck import Deck
from .player import Player

__all__ = ("BlackJackGame",)


class BlackJackGame:
    def __init__(
        self,
        chat_id: Optional[int] = None,
        players_qty: Optional[int] = None,
        decks_qty: int = 1,
        min_bet: Optional[float] = None,
        max_bet: Optional[float] = None,
        raw: Optional[dict] = None,
    ) -> None:

        if raw is not None:
            self.from_dict(raw)
        else:
            self._decks_qty = decks_qty
            self._planned_players_qty = players_qty
            self._deck = Deck(decks_qty)
            self._players: list[Player] = []
            self._min_bet = min_bet
            self._max_bet = max_bet
            self._current_player_idx: Optional[int] = 0
            self._dealer = Player("Дилер")
            self._chat_id: int = chat_id

    def drop_player(self, player: Player):
        if player.bet is not None:
            player.cash -= player.bet

        self._players.pop(self._players.index(player))

    @property
    def min_max_bet_info(self) -> str:
        return f" - Минимум: {self.min_bet}%0A - Максимум: {self.max_bet}%0A"

    @property
    def max_bet(self) -> float:
        return self._max_bet

    @property
    def min_bet(self) -> float:
        return self._min_bet

    def reset(self) -> None:
        for player in self.players_and_dealer:
            player.reset()

        # self._deck = Deck(self._num_of_decks)
        self._current_player_idx = 0

    @property
    def ratio_of_registered(self) -> str:
        registered, planned = len(self.players), self._planned_players_qty
        return f"{registered}/{planned}"

    def handle_player_blackjack(self, player: Player) -> None:
        d = self._dealer
        if d.has_potential_bj is True:
            if d.score == 10:
                player.set_bj_waiting_for_end_status()
            else:
                player.set_bj_need_to_clarify_status()
        else:
            player.set_bj_win32_status()

    def _define_results_with_dealer_bj(self) -> None:
        for p in self._players:
            if p.result_defined:
                continue

            if p.status_is_bj_waiting_for_end:
                p.set_draw_status()
            else:
                p.set_defeat_status()

            p.update_cash()

    def _define_results_without_dealer_bj(self) -> None:
        d = self._dealer
        for p in self._players:
            if p.result_defined:
                continue
            if p.status_is_bj_waiting_for_end:
                p.set_bj_win32_status()
            elif d.not_bust is False or p.score > d.score:
                p.set_win_status()
            elif p.score == d.score:
                p.set_draw_status()
            else:
                p.set_defeat_status()

    def define_results(self) -> None:
        d = self._dealer

        if d.has_blackjack:
            self._define_results_with_dealer_bj()
        else:
            self._define_results_without_dealer_bj()

    @property
    def dealer(self) -> Player:
        return self._dealer

    def handle_dealer(self):
        dealer = self.dealer
        while dealer.score < 17:
            dealer.add_card(self.deck.get_card())

    def deal_cards(self) -> None:
        for player in self.players:
            player.add_card(self.deck.get_card())
            player.add_card(self.deck.get_card())

        self._dealer.add_card(self.deck.get_card())

    @property
    def players_and_dealer(self) -> list[Player]:
        return self.players + [self.dealer]

    @property
    def players(self) -> list[Player]:
        return self._players

    @property
    def players_ids(self) -> list[int]:
        return [p._vk_id for p in self._players]

    @property
    def players_cashes_info(self) -> str:
        return "%0A".join([f"{p} - {p.cash}" for p in self.players])

    @property
    def table(self) -> int:
        return self._chat_id

    @property
    def current_player(self) -> Player:
        players = self.players
        return players[self._current_player_idx]

    @property
    def deck(self) -> Deck:
        return self._deck

    def next_player(self) -> bool:
        """:return: True если есть еще хотя бы один игрок"""
        self._current_player_idx += 1

        if self._current_player_idx >= len(self.players):
            self._current_player_idx = None
            return False

        return True

    @property
    def all_players_registered(self) -> bool:
        return len(self.players) == self._planned_players_qty

    @property
    def all_players_bet(self):
        return len(self.players) == len(self.players_who_bet)

    def add_player(self, player: Player) -> bool:
        if player in self._players:
            return False

        self._players.append(player)
        return True

    def get_player_by_id(self, vk_id: int) -> Optional[Player]:
        for player in self._players:
            if player.vk_id == vk_id:
                return player
        return None

    @property
    def players_who_bet(self) -> list[Player]:
        return [p for p in self._players if p.bet is not None]

    def from_dict(self, d: dict) -> None:
        self._decks_qty = d["decks_qty"]
        self._planned_players_qty = d["planned_players_qty"]
        self._deck = Deck(d=d["deck"])
        self._players = [Player(raw=player_info) for player_info in d["players"]]
        self._min_bet = d["min_bet"]
        self._max_bet = d["max_bet"]
        self._current_player_idx = d["current_player_idx"]
        self._dealer = Player(raw=d["dealer"])
        self._chat_id = d["chat_id"]

    def to_dict(self) -> dict:
        return {
            "decks_qty": self._decks_qty,
            "planned_players_qty": self._planned_players_qty,
            "deck": self._deck.to_dict(),
            "players": [p.to_dict() for p in self._players],
            "min_bet": self._min_bet,
            "max_bet": self._max_bet,
            "current_player_idx": self._current_player_idx,
            "dealer": self._dealer.to_dict(),
            "chat_id": self.table,
        }
