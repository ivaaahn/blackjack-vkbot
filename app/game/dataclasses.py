from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.store.vk_api.accessor import VkApiAccessor
    from app.store import PlayersAccessor


@dataclass
class GAccessors:
    vk: 'VkApiAccessor'
    players: 'PlayersAccessor'
