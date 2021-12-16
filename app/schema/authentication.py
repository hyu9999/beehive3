from typing import Optional

from app.models.rwmodel import RWModel


class TencentSMSInResponse(RWModel):
    mobile: str
    sms_code: str
    serial_no: Optional[str]
    fee: Optional[int]
    session_context: Optional[str]
    code: Optional[str]
    message: Optional[str]
    iso_code: Optional[str]
