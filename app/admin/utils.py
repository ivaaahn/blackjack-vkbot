import base64
from typing import Optional
import bcrypt
from .dataclasses import Admin


def is_password_valid(truth_password:str, password: str):
    hash_binary = base64.b64decode(truth_password.encode('utf-8'))
    return bcrypt.checkpw(password.encode('utf-8'), hash_binary)


def admin_from_session(session: Optional[dict]) -> Optional[Admin]:
    return Admin(id=session["admin"]["id"], email=session["admin"]["email"])
