from typing import NewType

from fastapi import APIRouter
from pydantic import BaseModel, Field


class RouterBaseModel(BaseModel):
    """这个类主要是给生成的schema增加操作"""

    @staticmethod
    def list(model, db):  # 对应get方法
        """methods=get，读取列表"""

        def res():
            return db.query(model).all()

        return res

    def write2route(self, ul, route: APIRouter, model, get_db):
        """注册到路由"""
        route.get(ul)(self.list(model, get_db))

    class Config:
        orm_mode = True

    @classmethod
    def get_basemodel(cls):

        """通过读取model的信息，创建schema"""
        model_name = cls.__name__
        # mappings为从model获取的相关配置
        __mappings__ = {}  # {'name':{'field':Field,'type':type,}}
        for filed in cls.__table__.c:
            filed_name = str(filed).split(".")[-1]
            if filed.default:
                default_value = filed.default
            elif filed.nullable:
                default_value = ...
            else:
                default_value = None
            # 生成的结构： id:int=Field(...,)大概这样的结构
            res_field = Field(default_value, description=filed.description)  # Field参数
            if isinstance(filed.type, int):
                tp = NewType(filed_name, int)
            else:
                tp = NewType(filed_name, str)
            __mappings__[filed_name] = {"tp": tp, "Field": res_field}
        res = type(model_name, (RouterBaseModel,), __mappings__)
        # 将schema绑定到model
        cls.__model__ = res()
        return cls
