import random
from typing import Optional


class Card:
    sharp_photo = 'photo-202369435_457239076'
    joker_photo = 'photo-202369435_457239075'

    def __init__(self, rank: Optional[int] = None, suit: Optional[int] = None, d: Optional[dict] = None) -> None:
        self._ranks = ('2', '3', '4', '5', '6', '7', '8', '9', 't', '10', 'j', 'k', 'q')
        self._suits = ('c', 'd', 'h', 's')
        self._photos: dict[str, str] = {k: str(v) for k, v in zip([r + s for r in self._ranks for s in self._suits],
                                                                  range(457239077, 457239129))}

        if d is None:
            self._rank = self._ranks[rank]
            self._suit = self._suits[suit]
        else:
            self._rank = d['rank']
            self._suit = d['suit']

    def to_dict(self) -> dict:
        return {
            'rank': self._rank,
            'suit': self._suit,
        }

    @property
    def photo(self) -> str:
        return 'photo-202369435_' + self._photos[self.rank + self.suit]

    @property
    def rank(self) -> str:
        return self._rank

    @property
    def suit(self) -> str:
        return self._suit

    def bj_value(self, curr_sum: int) -> int:
        if self.rank in ('j', 'q', 'k', '10'):
            ans = 10
        elif self.rank in '23456789':
            ans = int(self.rank)
        elif self.rank == 't':
            ans = 11 if curr_sum + 11 <= 21 else 1
        else:
            ans = -1

        return ans

    def __str__(self) -> str:
        return f'{self.rank} {self.suit}%0a'

    def __repr__(self) -> str:
        return f'Card<rank: {self.rank}, suit: {self.suit}>'


class Deck:
    def __init__(self, number_of: int = 5, d: Optional[dict] = None) -> None:
        if d is None:
            self._cards = [Card(rank=r, suit=s) for r in range(13) for s in range(4) for i in range(number_of)]
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
