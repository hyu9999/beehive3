from typing import Optional

from pydantic import AnyUrl

from app.models.rwmodel import RWModel, PyObjectId


class Profile(RWModel):
    id: PyObjectId
    username: str
    introduction: Optional[str] = ""
    avatar: Optional[str] = None
    mobile: Optional[str]
