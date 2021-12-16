from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, Union

from bson import ObjectId, Decimal128
from pandas import Timestamp
from pydantic import BaseConfig, BaseModel


class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(pattern="^[0-9a-fA-F]{24}$", examples=["5f365bedcf31136279a97d19", "5d883e0bedcac5082ecf3afa"])

    @classmethod
    def validate(cls, v):
        if not isinstance(v, cls):
            if not cls.is_valid(v):
                raise TypeError("ObjectId required")
            return cls(v)
        return cls(v)


class PyDecimal(Decimal128):
    @classmethod
    def __get_validators__(cls) -> "CallableGenerator":
        yield cls.validate

    @classmethod
    def __modify_schema__(cls, field_schema: Dict[str, Any]) -> None:
        field_schema.update(type="number", format="json-number")

    @classmethod
    def validate(cls, v: Union[float, int, Decimal]) -> Any:
        """转化float为Decimal128.

        先将python的二进制浮点数用str方法显式的转化为10进制浮点数，再把10进制浮点数字符串转化为Decimal128.
        """
        return cls(str(v))

    def __add__(self, other, context=None):
        """Return self + other"""
        result = self.to_decimal().__add__(other.to_decimal() if isinstance(other, PyDecimal) else other)
        return PyDecimal(result)

    def __sub__(self, other, context=None):
        """Return self - other"""
        result = self.to_decimal().__sub__(other.to_decimal() if isinstance(other, PyDecimal) else other)
        return PyDecimal(result)


class RWModel(BaseModel):
    class Config(BaseConfig):
        allow_population_by_field_name = True
        json_encoders = {
            datetime: lambda dt: dt.replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z"),
            Timestamp: lambda x: x.date(),
            ObjectId: lambda x: x.__str__(),
            PyObjectId: lambda x: x.__str__(),
            PyDecimal: lambda x: float(x.__str__()),
        }


class EmbeddedDocument(RWModel):
    ...
