from enum import Enum
from typing import Optional

from app.game.deck import Card


class PlayerStatus(str, Enum):
    DEFEAT = 'Проигрыш'
    DRAW = 'Ничья'
    WIN = 'Победа'
    IN_GAME = 'В игре'
    BUST = 'Перебор'
    BJ_NEED_TO_CLARIFY = 'Надо уточнять'
    BJ_WIN32 = 'Выиграл блэк-джек (3:2)'
    BJ_WIN11 = 'Выиграл блэк-джек (1:1)'
    BJ_WAITING_FOR_END = 'Блэк-джек (ожидает конца игры)'


class Player:
    def __init__(self,
                 name: Optional[str] = None,
                 vk_id: Optional[int] = None,
                 cash: Optional[float] = None,
                 raw: Optional[dict] = None) -> None:

        if raw is not None:
            self.from_dict(raw)
        else:
            self._name = name
            self._vk_id = vk_id
            self._cash = cash
            self._bet: Optional[float] = None
            self._cards: list[Card] = []
            self._score: int = 0
            self._status = PlayerStatus.IN_GAME

    def from_dict(self, raw: dict) -> None:
        self._name = raw['name']
        self._vk_id = raw['vk_id']
        self._cash = raw['cash']
        self._bet = raw['bet']
        self._cards = [Card(d=card_info) for card_info in raw['cards']]
        self._score = raw['score']
        self._status = PlayerStatus(raw['status'])

    def to_dict(self) -> dict:
        return {
            'name': self.name,
            'vk_id': self.vk_id,
            'bet': self.bet,
            'cash': self.cash,
            'cards': [c.to_dict() for c in self._cards],
            'score': self.score,
            'status': self._status
        }

    def calc_win(self) -> float:
        if self.status_is_win or self.status_is_bj_win11:
            return self._bet
        elif self.status_is_bj_win32:
            return 1.5 * self._bet
        elif self.status_is_defeat or self.status_is_bust:
            return -self._bet

        return 0

    def update_cash(self) -> None:
        if self._status is not PlayerStatus.IN_GAME:
            self._cash += self.calc_win()

    @property
    def result_defined(self):
        return self._status not in (
            PlayerStatus.IN_GAME, PlayerStatus.BJ_WAITING_FOR_END, PlayerStatus.BJ_NEED_TO_CLARIFY)

    @property
    def status_is_bj_need_to_clarify(self) -> bool:
        return self._status is PlayerStatus.BJ_NEED_TO_CLARIFY

    @property
    def status_is_bj_win11(self) -> bool:
        return self._status is PlayerStatus.BJ_WIN11

    @property
    def status_is_bj_win32(self) -> bool:
        return self._status is PlayerStatus.BJ_WIN32

    @property
    def status_is_bj_waiting_for_end(self) -> bool:
        return self._status is PlayerStatus.BJ_WAITING_FOR_END

    @property
    def status_is_win(self):
        return self._status is PlayerStatus.WIN

    @property
    def status_is_defeat(self):
        return self._status is PlayerStatus.DEFEAT

    @property
    def status_is_draw(self):
        return self._status is PlayerStatus.DRAW

    @property
    def status_is_bust(self):
        return self._status is PlayerStatus.BUST

    @property
    def has_blackjack(self) -> int:
        return self.cards_qty == 2 and self.score == 21

    @property
    def has_potential_bj(self) -> Optional[bool]:
        """
        ONLY FOR DEALER
        Check after the cards are dealt whether the dealer can have blackjack.
        :return: None if player is not dealer, else True/False
        """

        if not self.is_dealer:
            return None

        return self._score >= 10 and self.cards_qty == 1

    @property
    def cards_qty(self) -> int:
        return len(self._cards)

    @property
    def status(self) -> PlayerStatus:
        return self._status

    @status.setter
    def status(self, value: PlayerStatus) -> None:
        self._status = value

    @property
    def is_dealer(self) -> bool:
        return self._vk_id is None

    @property
    def cash(self) -> float:
        return self._cash

    @cash.setter
    def cash(self, value: float) -> None:
        self._cash = value

    def reset(self) -> None:
        self._bet = None
        self._score = 0
        self._cards.clear()
        self.set_in_game_status()

    @property
    def is_winner(self) -> bool:
        return self._status in (
            PlayerStatus.WIN,
            PlayerStatus.BJ_WIN11,
            PlayerStatus.BJ_WIN32,
        )

    @property
    def is_loser(self) -> bool:
        return self._status in (
            PlayerStatus.DEFEAT,
            PlayerStatus.BUST,
        )

    def set_in_game_status(self) -> None:
        self._status = PlayerStatus.IN_GAME

    def set_bust_status(self):
        self._status = PlayerStatus.BUST
        self.update_cash()

    def set_win_status(self) -> None:
        self._status = PlayerStatus.WIN
        self.update_cash()

    def set_draw_status(self) -> None:
        self._status = PlayerStatus.DRAW
        self.update_cash()

    def set_defeat_status(self) -> None:
        self._status = PlayerStatus.DEFEAT
        self.update_cash()

    def set_bj_win11_status(self) -> None:
        self._status = PlayerStatus.BJ_WIN11
        self.update_cash()

    def set_bj_win32_status(self) -> None:
        self._status = PlayerStatus.BJ_WIN32
        self.update_cash()

    def set_bj_waiting_for_end_status(self) -> None:
        self._status = PlayerStatus.BJ_WAITING_FOR_END

    def set_bj_need_to_clarify_status(self) -> None:
        self._status = PlayerStatus.BJ_NEED_TO_CLARIFY

    @property
    def not_bust(self) -> bool:
        return self.score <= 21

    def add_card(self, card: Card) -> None:
        self._cards.append(card)
        self._score += card.bj_value(self._score)

    # @property
    # def cards_photos(self) -> str:
    #     res = ','.join([card.photo for card in self._cards])
    #
    #     if self.is_dealer and len(self._cards) == 1:
    #         res += f',{Card.sharp_photo}'
    #
    #     return res

    # deprecated
    @property
    def cards_info(self) -> str:
        ans = '%0A'.join([c.card_txt for c in self._cards])
        # if self.is_dealer and len(self._cards) == 1:
        #     ans += f'%0A{Card.fake_card()}'
        return ans

    def place_bet(self, value: int) -> None:
        self._bet = value

    @property
    def score(self) -> int:
        return self._score

    @property
    def bet(self) -> Optional[float]:
        return self._bet

    @property
    def name(self) -> str:
        return self._name

    @property
    def vk_id(self) -> int:
        return self._vk_id

    def __eq__(self, other: 'Player') -> bool:
        return self.vk_id == other.vk_id

    def __str__(self) -> str:
        if self.is_dealer:
            return 'Дилер'

        return f'[id{self.vk_id}|{self.name}]'

    def __repr__(self) -> str:
        return f'Player<name: {self.name}, vk_id: {self._vk_id}>'
