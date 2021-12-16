from app.models.base.zvt_data_log import ZvtDataLog, ZvtDataLogType
from app.models.dbmodel import DBModelMixin


class ZvtDataLogInDB(DBModelMixin, ZvtDataLog):
    """Zvt数据详情."""


class ZvtDataLogTypeInDB(DBModelMixin, ZvtDataLogType):
    """Zvt数据类型."""
