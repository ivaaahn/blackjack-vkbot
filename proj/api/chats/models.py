from dataclasses import dataclass

from ..players.models import PlayerModel


@dataclass
class ChatModel:
    chat_id: int
    players: list[PlayerModel]
    number_of_players: int

    def to_dict(self) -> dict:
        return {
            "chat_id": self.chat_id,
            "players": [p.to_dict() for p in self.players],
            "number_of_players": self.number_of_players,
        }

    @staticmethod
    def from_dict(raw: dict) -> "ChatModel":
        return ChatModel(
            chat_id=raw["chat_id"],
            players=[PlayerModel.from_dict(p_raw) for p_raw in raw["players"]],
            number_of_players=raw["number_of_players"],
        )
