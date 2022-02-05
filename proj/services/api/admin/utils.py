import base64
from typing import Optional
import bcrypt
from .models import AdminModel


def is_password_valid(truth_password: str, password: str) -> bool:
    hash_binary = base64.b64decode(truth_password.encode("utf-8"))
    return bcrypt.checkpw(password.encode("utf-8"), hash_binary)


def admin_from_session(session: Optional[dict]) -> AdminModel:
    try:
        _id = session["admin"]["_id"]
        email = session["admin"]["email"]
    except:
        pass
    else:
        return AdminModel(_id=_id, email=email, password=None)


def hash_pwd(raw_password: str) -> str:
    hash_binary = bcrypt.hashpw(raw_password.encode("utf-8"), bcrypt.gensalt())
    encoded = base64.b64encode(hash_binary)
    return encoded.decode("utf-8")
