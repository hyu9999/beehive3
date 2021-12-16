from pydantic import Field

from app.models.rwmodel import EmbeddedDocument


class 指标配置基本信息(EmbeddedDocument):
    name: str = Field(..., title="名称")
    code: str = Field(..., title="编码")
