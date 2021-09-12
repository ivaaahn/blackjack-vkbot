from dataclasses import dataclass
from typing import Optional


@dataclass
class Admin:
    id: int
    email: str
    password: Optional[str] = None
