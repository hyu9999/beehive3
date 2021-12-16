from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Security
from pydantic import ValidationError

from app.core.jwt import get_current_user_authorizer
from app.crud.base import get_equipment_collection, get_robots_collection
from app.db.mongodb import AsyncIOMotorClient, get_database
from app.service.datetime import get_early_morning

router = APIRouter()


@router.get("/header", description="dashboard表头")
async def get_header(
    db: AsyncIOMotorClient = Depends(get_database), user=Security(get_current_user_authorizer(), scopes=["装备:查看"]),
):
    try:
        end_time = get_early_morning() + timedelta(days=1)
        start_time = end_time - timedelta(days=30)
        # equipment
        所有装备 = await get_equipment_collection(db).count_documents({"状态": {"$in": ["已上线", "已下线"]}, "分类": {"$in": ["交易", "选股", "择时", "风控包"]}})
        近期上线装备 = await get_equipment_collection(db).count_documents({"状态": "已上线", "上线时间": {"$gte": start_time, "$lte": end_time}})
        近期下线装备 = await get_equipment_collection(db).count_documents({"状态": "已下线", "下线时间": {"$gte": start_time, "$lte": end_time}})
        # robot
        所有机器人 = await get_robots_collection(db).count_documents({"状态": {"$in": ["已上线", "已下线"]}})
        近期上线机器人 = await get_robots_collection(db).count_documents({"状态": "已上线", "上线时间": {"$gte": start_time, "$lte": end_time}})
        近期下线机器人 = await get_robots_collection(db).count_documents({"状态": "已下线", "下线时间": {"$gte": start_time, "$lte": end_time}})
        ret_data = {
            "所有装备": 所有装备,
            "近期上线装备": 近期上线装备,
            "近期下线装备": 近期下线装备,
            "所有机器人": 所有机器人,
            "近期上线机器人": 近期上线机器人,
            "近期下线机器人": 近期下线机器人,
        }
        return ret_data
    except HTTPException as e:
        raise HTTPException(status_code=400, detail=f"获取表头数据发生错误，错误信息: {e.detail}")
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=f"获取表头数据发生数据错误，请联系管理员。详细错误：{e.errors()}")
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=f"获取表头数据发生数据错误，请联系管理员。详细错误：{e.args[0]}")
