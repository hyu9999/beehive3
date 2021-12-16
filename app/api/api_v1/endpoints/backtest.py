import copy
import logging
from datetime import datetime

from fastapi import APIRouter, Body, HTTPException, Security
from fastapi import Depends
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import ValidationError
from pymongo.errors import DuplicateKeyError
from starlette.websockets import WebSocket, WebSocketDisconnect

from app.core.jwt import get_current_user_authorizer
from app.crud.robot import get_robot, 创建机器人
from app.db.mongodb import get_database
from app.enums.robot import 机器人状态
from app.models.robot import Robot
from app.schema.robot import 机器人inCreate
from app.service.backtest import 初始化回测数据, 获取回测数据, get_user_config, get_robot_data, RobotMatchUp, format_回测数据, init_start
from app.service.datetime import get_early_morning
from app.service.robots.robot import 生成机器人标识符, 获取风控装备列表
from app.service.str.styles import to_underline_dict, to_hump_dict

router = APIRouter()


@router.websocket("/robot/start")
async def init_backtest_data(websocket: WebSocket):
    await websocket.accept()
    await 初始化回测数据(websocket)
    await websocket.close()


@router.websocket("/robot/next")
async def get_backtest_data(websocket: WebSocket, db: AsyncIOMotorClient = Depends(get_database)):
    await websocket.accept()
    await 获取回测数据(websocket, db)
    await websocket.close()


@router.websocket("/robot", name="机器人回测")
async def 机器人回测(websocket: WebSocket, db: AsyncIOMotorClient = Depends(get_database)):
    await websocket.accept()
    while True:
        try:
            data = await websocket.receive_json()
        except WebSocketDisconnect as e:
            logging.warning(f"[{e}]websocket服务等待超时， 自动断开链接")
            await websocket.close()
            break
        json_data = to_underline_dict(data)
        event = json_data["event"]
        data = json_data["data"]
        if event == "start":
            init_start(data, logging)
            ret_data = {"event": "start_callback", "data": to_hump_dict(data)}
            await websocket.send_json(ret_data)
        elif event == "next":
            user_config = data["user_config"]
            is_auto = data["is_auto"]
            robot = await get_robot(data["robot_id"], db)
            fundbal = int(user_config.pop("fund_available", 500000))
            mktval = int(user_config.pop("market_value", 0) or 0)
            asset = {"fundbal": fundbal, "mktval": mktval}
            stocks = user_config.pop("stocks", []) or []
            for stock in stocks:
                stock["stopup"] = 99999999
                stock["stopdown"] = 0
            userconfig_obj = get_user_config(robot, data["start"], data["end"])
            try:
                robot_data = get_robot_data(robot, data["start"], data["end"])
            except Exception as e:
                logging.warning(f"backtest_next[结束] {e}", exc_info=True)
                await websocket.send_json({"event": "end", "data": "获取机器人数据异常"})
                await websocket.close()
                break
            robot_match_up = RobotMatchUp(asset, stocks, userconfig_obj, robot_data)
            try:
                for item in robot_match_up.robot_yield_trader():
                    tmp = tuple(item.items())[0]
                    result = format_回测数据(tmp[0], copy.deepcopy(tmp[1]))
                    ret_data = {"event": "backtest_data", "data": result}
                    await websocket.send_json(ret_data)
                    if not is_auto:
                        if result["当日信号"]:
                            break
                else:
                    logging.warning(f"backtest_next[结束] success")
                    await websocket.send_json({"event": "end"})
                    await websocket.close()
                    break
            except Exception as e:
                logging.warning(f"backtest_next[结束] {e}", exc_info=True)
                await websocket.send_json({"event": "end", "data": "回测数据异常"})
                await websocket.close()
                break
        else:
            logging.warning(f"关闭websocket连接")
            await websocket.close()
            break


@router.post("/robots/new")
async def create_tmp_robot(
    机器人: 机器人inCreate = Body(..., embed=True), db: AsyncIOMotorClient = Depends(get_database), user=Security(get_current_user_authorizer(), scopes=["机器人:创建"]),
):
    机器人字典 = 机器人.dict()
    机器人字典["作者"] = user.username
    机器人字典["标识符"] = await 生成机器人标识符(db)
    机器人字典["状态"] = 机器人状态.临时回测
    机器人字典["风控装备列表"] = await 获取风控装备列表(机器人字典["风控包列表"], db)
    current_dt = datetime.utcnow()
    机器人字典["创建时间"] = current_dt
    机器人字典["上线时间"] = get_early_morning(current_dt)
    try:
        if 3 >= len(机器人.选股装备列表) >= 1 and len(机器人.择时装备列表) == 1 and 3 >= len(机器人.交易装备列表) >= 1:
            return await 创建机器人(db, Robot(**机器人字典), send_message=False)
        raise HTTPException(status_code=404, detail=f"不符合机器人装备设定原则，不允许提交编辑！")
    except DuplicateKeyError as e:
        raise HTTPException(status_code=404, detail=f"创建机器人失败，{e.details.get('keyValue')}已存在")
    except HTTPException as e:
        raise HTTPException(status_code=404, detail=f"创建机器人失败，错误信息: {e.detail}")
    except ValidationError as e:
        raise HTTPException(status_code=404, detail=f"创建机器人失败，请联系管理员。详细错误：{e.errors()}")
