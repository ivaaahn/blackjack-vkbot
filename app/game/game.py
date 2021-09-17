from dataclasses import dataclass
from enum import Enum
from typing import Optional, Iterator

from app.base.base_game import Game
from app.base.base_game_accessor import BaseGameAccessor
from app.game.deck import Deck, Card
from app.game.player import Player
from app.game.states import BJStates, State, StateResolver


class GameResult(str, Enum):
    DEFEAT = 'Проигрыш'
    DRAW = 'Ничья'
    WIN = 'Победа'


class BlackJackGame(Game):
    def __init__(self,
                 chat_id: Optional[int] = None,
                 num_of_players: Optional[int] = None,
                 num_of_decks: int = 1,
                 min_bet: int = 1,
                 max_bet: int = 10000,
                 raw: Optional[dict] = None,
                 ) -> None:

        if raw is not None:
            self.from_dict(raw)
            return

        self._planned_num_of_players = num_of_players
        self._deck = Deck(num_of_decks)
        self._players: list[Player] = []
        self._min_bet = min_bet
        self._max_bet = max_bet
        self._current_player_idx: Optional[int] = 0
        self._dealer = Player('Дилер', -1)
        self._chat_id: int = chat_id

    @property
    def ratio_of_registered(self) -> str:
        registered, planned = len(self.players), self._planned_num_of_players
        return f'{registered}/{planned}'

    def define_result(self, player: Player) -> GameResult:
        if player.in_game is False:
            return GameResult.DEFEAT

        if (player.score > self.dealer.score) or (not self.dealer.in_game):
            return GameResult.WIN

        if self.dealer.score == player.score:
            return GameResult.DRAW

    @property
    def dealer(self) -> Player:
        return self._dealer

    def handle_dealer(self):
        dealer = self.dealer
        while dealer.score < 17:
            dealer.add_card(self.deck.get_card())

    def deal_cards(self) -> None:
        for player in self._players:
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
    def table(self) -> int:
        return self._chat_id

    @property
    def current_player(self) -> Player:
        return self._players[self._current_player_idx]

    @property
    def deck(self) -> Deck:
        return self._deck

    def next_player(self) -> bool:
        self._current_player_idx += 1

        if self._current_player_idx >= len(self._players):
            self._current_player_idx = None
            return False

        return True

    @property
    def all_players_registered(self) -> bool:
        return len(self._players) == self._planned_num_of_players

    @property
    def all_players_bet(self):
        return len(self._players) == len(self.players_who_bet())

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

    def players_who_bet(self) -> list[Player]:
        return [p for p in self._players if p.bet is not None]

    def from_dict(self, d: dict) -> None:
        self._planned_num_of_players = d['planned_num_of_players']
        self._deck = Deck(d=d['deck'])
        self._players = [Player(d=player_info) for player_info in d['players']]
        self._min_bet = d['min_bet']
        self._max_bet = d['max_bet']
        self._current_player_idx = d['current_player_idx']
        self._dealer = Player(d=d['dealer'])
        self._chat_id = d['chat_id']

    def to_dict(self) -> dict:
        return {
            'planned_num_of_players': self._planned_num_of_players,
            'deck': self._deck.to_dict(),
            'players': [p.to_dict() for p in self._players],
            'min_bet': self._min_bet,
            'max_bet': self._max_bet,
            'current_player_idx': self._current_player_idx,
            'dealer': self._dealer.to_dict(),
            'chat_id': self.table,
        }


class GameCtx:
    def __init__(self, game_accessor: BaseGameAccessor, chat: int) -> None:
        self.accessor = game_accessor
        self.chat = chat

    def proxy(self) -> 'GameCtxProxy':
        return GameCtxProxy(self)

    async def get_state(self, default: Optional[int] = None) -> Optional[State]:
        state_id = await self.accessor.get_state(chat=self.chat, default=default)
        return default if state_id is None else StateResolver.get_state(state_id)

    async def get_game(self, default: Optional[dict] = None) -> Optional[BlackJackGame]:
        raw_game = await self.accessor.get_data(chat=self.chat, default=default)
        return default if raw_game is None else BlackJackGame(raw=raw_game)

    async def set_state(self, state: State) -> None:
        if state is None:
            await self.reset_state()
        else:
            await self.accessor.set_state(chat=self.chat, state=state.state_id)

    async def save_game(self, game: Optional[BlackJackGame]) -> None:
        if game is None:
            await self.reset_game()
        else:
            await self.accessor.set_data(chat=self.chat, data=game.to_dict())

    async def reset_game(self) -> None:
        await self.accessor.reset_data(chat=self.chat)

    async def reset_state(self) -> None:
        await self.accessor.reset_state(chat=self.chat)


class GameCtxProxy:
    def __init__(self, game_ctx: GameCtx) -> None:
        self.game_ctx = game_ctx
        self._game: Optional[BlackJackGame] = None
        self._state: Optional[State] = None
        self._last_state: Optional[State] = None

        self._state_is_dirty = False

        self._closed = True

    async def __aenter__(self):
        await self.load()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            await self.save()

        # TODO: raise exception

        self._closed = True

    async def load(self) -> None:
        self._closed = False
        self._state = await self.game_ctx.get_state()
        self._game = await self.game_ctx.get_game()
        self._state_is_dirty = False

    async def save(self, force: bool = False) -> None:
        # TODO check usage of game
        # if self.game is not None:
        await self.game_ctx.save_game(game=self._game)

        if self._state_is_dirty or force:
            await self.game_ctx.set_state(state=self._state)

        self._state_is_dirty = False

    def rollback_state(self) -> None:
        self._state = self._last_state
        self._last_state = None

    @property
    def state(self) -> State:
        return self._state

    @state.setter
    def state(self, value: State) -> None:
        self._last_state = self.state
        self._state_is_dirty = True
        self._state = value

    @property
    def last_state(self) -> State:
        return self._last_state

    @state.deleter
    def state(self) -> None:
        self._state_is_dirty = True
        self._state = None

    @property
    def game(self) -> BlackJackGame:
        return self._game

    @game.setter
    def game(self, value: BlackJackGame) -> None:
        self._game = value

    @game.deleter
    def game(self) -> None:
        self._game = None

    # @classmethod
    # async def create(cls, game_ctx: GameCtx) -> 'GameCtxProxy':
    #     proxy = cls(game_ctx)
    #     await proxy.load()
    #     return proxy
