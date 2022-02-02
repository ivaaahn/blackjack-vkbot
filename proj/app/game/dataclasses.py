from dataclasses import dataclass

from app.store.vk_api.accessor import VkApiAccessor
from app.store.players.accessor import PlayersAccessor
from app.store.game_settings.accessor import GameSettingsAccessor


@dataclass
class GAccessors:
    vk: VkApiAccessor
    players: PlayersAccessor
    settings: GameSettingsAccessor
