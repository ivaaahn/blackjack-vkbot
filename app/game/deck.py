import random
from typing import Optional


class Card:
    sharp_photo = 'photo-202369435_457239076'
    joker_photo = 'photo-202369435_457239075'
    _SUIT_MAP = {
        'c': '♣',
        'd': '♦',
        'h': '♥',
        's': '♠'
    }

    _RANK_MAP = {
        't': '10',
        'j': 'Валет',
        'k': 'Король',
        'q': 'Дама',
        'a': 'Туз'
    }

    _RANKS = '23456789tjkqa'
    _SUITS = 'cdhs'

    def __init__(self, rank: Optional[int] = None, suit: Optional[int] = None, d: Optional[dict] = None) -> None:
        if d is None:
            self._rank = self._RANKS[rank]
            self._suit = self._SUITS[suit]
        else:
            self._rank = d['rank']
            self._suit = d['suit']

    def to_dict(self) -> dict:
        return {
            'rank': self._rank,
            'suit': self._suit,
        }

    @staticmethod
    def fake_card() -> str:
        return '🔻 ❓'

    @property
    def card_txt(self) -> str:
        rank_info = self._RANK_MAP[self._rank] if self._rank.isalpha() else self._rank

        return f'🔻 {rank_info} {self._SUIT_MAP[self._suit]}'

    @property
    def rank(self) -> str:
        return self._rank

    @property
    def suit(self) -> str:
        return self._suit

    def bj_value(self, curr_sum: int) -> int:
        if self.rank in 'jqkt':
            ans = 10
        elif self.rank in '23456789':
            ans = int(self.rank)
        else:  # Ace
            ans = 11 if curr_sum + 11 <= 21 else 1

        return ans

    def __str__(self) -> str:
        return f'{self.rank} {self.suit}%0a'

    def __repr__(self) -> str:
        return f'Card<rank: {self.rank}, suit: {self.suit}>'


class Deck:
    def __init__(self, qty: int = 5, d: Optional[dict] = None) -> None:
        if d is None:
            self._cards = [Card(rank=r, suit=s) for r in range(13) for s in range(4) for _ in range(qty)]
            self.shuffle()
            self._last_card: Optional[Card] = None
        else:
            self._from_dict(d)

    def to_dict(self) -> dict:
        return {
            'cards': [c.to_dict() for c in self._cards],
            'last_card': self._last_card.to_dict() if self._last_card else None
        }

    def _from_dict(self, d: dict) -> None:
        self._cards = [Card(d=card_info) for card_info in d['cards']]
        self._last_card = Card(d=d['last_card']) if d['last_card'] is not None else None

    def shuffle(self) -> None:
        random.shuffle(self._cards)

    @property
    def last_card(self) -> Card:
        return self._last_card

    @last_card.setter
    def last_card(self, value: Card) -> None:
        self._last_card = value

    def get_card(self) -> Card:
        self._last_card = self._cards.pop()
        return self.last_card
