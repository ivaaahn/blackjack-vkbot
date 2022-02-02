from dataclasses import dataclass
from typing import Optional
from uuid import UUID


@dataclass
class AdminModel:
    _id: UUID
    email: str
    password: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "_id": self._id,
            "email": self.email,
            "password": self.password,
        }

    @staticmethod
    def from_dict(raw: dict) -> "AdminModel":
        return AdminModel(_id=raw["_id"], email=raw["email"], password=raw["password"])
