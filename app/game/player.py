from enum import Enum
from typing import Optional

from app.game.deck import Card


class PlayerStatus(str, Enum):
    DEFEAT = 'Проигрыш'
    DRAW = 'Ничья'
    WIN = 'Победа'
    IN_GAME = 'В игре'
    BUST = 'Перебор'
    BJ = 'Блэкджек'


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

    def update_cash(self):
        if self.status is PlayerStatus.WIN:
            self.cash += self.bet
        elif self.status in (PlayerStatus.DEFEAT, PlayerStatus.BUST):
            self.cash -= self.bet

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

    def set_bust(self):
        self.status = PlayerStatus.BUST
        self.update_cash()

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
        if self.is_dealer and len(self._cards) == 1:
            ans += f'%0A{Card.fake_card()}'
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
