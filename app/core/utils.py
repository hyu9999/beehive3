import pandas as pd
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from starlette.responses import UJSONResponse
from typing import Dict


def create_aliased_response(model: BaseModel) -> UJSONResponse:
    return UJSONResponse(content=jsonable_encoder(model, by_alias=True))


def validate_df(df: pd.DataFrame, model_of_row: BaseModel):
    """一个对DataFrame进行数据检验的类"""
    for row in df.iterrows():
        model_of_row(**row.to_dict())


def merge_two_dicts(dict1: Dict, dict2: Dict) -> Dict:
    """ 合并两个dict，对于同样的key的value进行汇总，注意两个dict的结构必须一致并且value必须是list"""
    return {key: list(set().union(value, dict1[key])) if key in dict1 and isinstance(value, list) else value for key, value in {**dict1, **dict2}.items()}
