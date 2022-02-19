from enum import Enum


class MainActionChoiceType(str, Enum):
    hit = "hit"
    stand = "stand"
    blackjack_pickup11 = "pick up 11"
    blackjack_pickup32 = "pick up 32"
    blackjack_wait_for = "wait"


class StartActionChoiceType(str, Enum):
    new_game = "new_game"
    get_bonus = "bonus"
    show_balance = "balance"
    common_statistic = "stat"
    personal_statistic = "pers_stat"
    cancel = "cancel"


class LastActionChoiceType(str, Enum):
    end_game = "stop"
    repeat_game = "again"
