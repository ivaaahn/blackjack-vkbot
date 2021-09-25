from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional


@dataclass
class PlayerStats:
    max_cash: float
    number_of_games: int = 0
    number_of_wins: int = 0
    number_of_defeats: int = 0
    max_bet: Optional[float] = None
    average_bet: Optional[float] = None
    max_win: Optional[float] = None

    def to_dict(self) -> dict:
        return {
            'max_cash': self.max_cash,
            'number_of_games': self.number_of_games,
            'number_of_wins': self.number_of_wins,
            'number_of_defeats': self.number_of_defeats,
            'average_bet': self.average_bet,
            'max_bet': self.max_bet,
            'max_win': self.max_win,
        }

    @staticmethod
    def from_dict(raw: dict) -> 'PlayerStats':
        return PlayerStats(
            max_cash=raw['max_cash'],
            number_of_games=raw['number_of_games'],
            number_of_wins=raw['number_of_wins'],
            number_of_defeats=raw['number_of_defeats'],
            average_bet=raw['average_bet'],
            max_bet=raw['max_bet'],
            max_win=raw['max_win'],
        )

    def __str__(self) -> str:
        return f'''
        🔺 Сыграно игр: {self.number_of_games}%0A
        🔺 Выиграно игр: {self.number_of_wins} {f'({round(self.number_of_wins / self.number_of_games * 100, 2)}%)' if self.number_of_games else ''}%0A
        🔺 Проиграно игр: {self.number_of_defeats} {f'({round(self.number_of_defeats / self.number_of_games * 100, 2)}%)' if self.number_of_games else ''}%0A
        🔺 Средняя ставка: {round(self.average_bet, 2) if self.average_bet is not None else None}%0A
        🔺 Макс. ставка: {self.max_bet}%0A
        🔺 Макс. выигрыш: {self.max_win}%0A
        🔺 Макс. денег на счете: {self.max_cash}$%0A
        '''


@dataclass
class PlayerModel:
    vk_id: int
    chat_id: int
    cash: float
    first_name: str
    last_name: str
    stats: PlayerStats
    last_bonus_date: datetime
    registered_at: datetime
    city: Optional[str] = None
    birthday: Optional[datetime] = None

    def to_dict(self) -> dict:
        return {
            'vk_id': self.vk_id,
            'chat_id': self.chat_id,
            'cash': self.cash,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'registered_at': self.registered_at,
            'last_bonus_date': self.last_bonus_date,
            'birthday': self.birthday,
            'city': self.city,
            'stats': self.stats.to_dict(),
        }

    @staticmethod
    def from_dict(raw: dict) -> 'PlayerModel':
        return PlayerModel(
            vk_id=raw['vk_id'],
            chat_id=raw['chat_id'],
            cash=raw['cash'],
            first_name=raw['first_name'],
            last_name=raw['last_name'],
            registered_at=raw['registered_at'],
            last_bonus_date=raw['last_bonus_date'],
            birthday=raw['birthday'],
            city=raw['city'],
            stats=PlayerStats.from_dict(raw['stats']),
        )

    def check_bonus(self, minutes: int) -> bool:
        return datetime.now() - self.last_bonus_date > timedelta(minutes=minutes)

    # def personal_info(self, position: int) -> str:
    #     return f'''
    #     Статистика для [id{self.vk_id}|{self.first_name} {self.last_name}]%0A%0A%0A
    #     Позиция в рейтинге: {position}%0A%0A
    #     {self.stats}
    #     '''

    #  TODO еще добавить поля
    def __str__(self) -> str:
        return f'[id{self.vk_id}|{self.first_name} {self.last_name}] - {self.cash}$ '
