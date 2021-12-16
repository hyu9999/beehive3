from collections.abc import Iterable

from fastapi.openapi.constants import REF_PREFIX
from fastapi.openapi.utils import validation_error_definition, validation_error_response_definition
from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.responses import UJSONResponse, JSONResponse
from starlette.status import (
    HTTP_422_UNPROCESSABLE_ENTITY,
    HTTP_404_NOT_FOUND,
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
    HTTP_403_FORBIDDEN,
    HTTP_500_INTERNAL_SERVER_ERROR,
)


class HttpError:
    @classmethod
    def get_error_msg(cls, request: Request, exc: HTTPException):
        errors = {"body": []}
        if hasattr(exc, "detail"):
            if isinstance(exc.detail, Iterable) and not isinstance(exc.detail, str):
                for error in exc.detail:
                    error_name = ".".join(error["loc"][1:])  # remove 'body' from path to invalid element
                    errors["body"].append({error_name: error["msg"]})
            else:
                errors["body"].append(exc.detail)
        return {"errors": errors}

    @classmethod
    def response(cls, content, status_code=HTTP_400_BAD_REQUEST):
        return UJSONResponse(content, status_code=status_code)

    @classmethod
    async def http_error_handler(cls, request: Request, exc: HTTPException) -> UJSONResponse:
        return cls.response(cls.get_error_msg(request, exc))

    @classmethod
    async def http_400_error_handler(cls, request: Request, exc: HTTPException) -> UJSONResponse:
        """Bad Request"""
        return cls.response(cls.get_error_msg(request, exc), status_code=HTTP_400_BAD_REQUEST)

    @classmethod
    async def http_401_error_handler(cls, request: Request, exc: HTTPException) -> UJSONResponse:
        """Unauthorized"""
        return cls.response(cls.get_error_msg(request, exc), status_code=HTTP_401_UNAUTHORIZED)

    @classmethod
    async def http_403_error_handler(cls, request: Request, exc: HTTPException) -> UJSONResponse:
        """Forbidden"""
        return cls.response(cls.get_error_msg(request, exc), status_code=HTTP_403_FORBIDDEN)

    @classmethod
    async def http_404_error_handler(cls, request: Request, exc: HTTPException) -> UJSONResponse:
        """Not Found"""
        return cls.response(cls.get_error_msg(request, exc), status_code=HTTP_404_NOT_FOUND)

    @classmethod
    async def http_422_error_handler(cls, request: Request, exc: HTTPException) -> UJSONResponse:
        """Unprocessable Entity"""
        return cls.response(cls.get_error_msg(request, exc), status_code=HTTP_422_UNPROCESSABLE_ENTITY)

    @classmethod
    async def http_500_error_handler(cls, request: Request, exc: HTTPException) -> UJSONResponse:
        """Unprocessable Entity"""
        return cls.response(cls.get_error_msg(request, exc), status_code=HTTP_500_INTERNAL_SERVER_ERROR)

    @classmethod
    async def http_461_error_handler(cls, request: Request, exc: HTTPException) -> UJSONResponse:
        """Unprocessable Entity"""
        return cls.response(cls.get_error_msg(request, exc), status_code=461)


validation_error_definition["properties"] = {"body": {"title": "Body", "type": "array", "items": {"type": "string"}}}

validation_error_response_definition["properties"] = {"errors": {"title": "Errors", "type": "array", "items": {"$ref": REF_PREFIX + "ValidationError"}}}


class BaseError(Exception):
    code = "100000"
    message = "自定义异常"

    def __init__(self, code: str = None, message: str = None):
        self.message = message or self.message
        self.code = code or self.code

    @classmethod
    def get_error_msg(cls, request: Request, exc: Exception):
        return {"code": cls.code, "message": exc.message}

    @classmethod
    async def handler(cls, request: Request, exc: Exception):
        return JSONResponse(status_code=HTTP_400_BAD_REQUEST, content=cls.get_error_msg(request, exc))


# ################## 自定义异常 ##################

# 系统内部异常 1xxxxx

# # 账户异常 100xxx
class UserAlreadyExist(BaseError):
    code = "100001"
    message = "用户已存在"


class NoUserError(BaseError):
    code = "100002"
    message = "用户不存在"


class LoginError(BaseError):
    code = "100003"
    message = "登录异常"


class TokenAcquisitionError(BaseError):
    code = "100004"
    message = "Token获取失败"


class TokenValidationError(BaseError):
    code = "100005"
    message = "Token验证失败"


class PermissionDenied(BaseError):
    code = "100006"
    message = "权限不足，请联系客服或者管理员"


class VIPCodeError(BaseError):
    code = "100007"
    message = "邀请码错误"


class UpgradeVIPError(BaseError):
    code = "100008"
    message = "非免费用户无法升级vip"


# # 组合异常 101xxx


class NoPortfolioError(BaseError):
    code = "101001"
    message = "组合不存在"


class PortfolioTooMany(BaseError):
    code = "101002"
    message = "创建组合数达到上限"


class LatestFundAssetInDatabaseError(BaseError):
    code = "101003"
    message = "最新的账户资产数据还未写入数据库！"


class PortfolioCanNotBeSubscribed(BaseError):
    code = "101004"
    message = "组合无法被订阅"


class PortfolioCloseError(BaseError):
    code = "101005"
    message = "关闭组合异常"


class PortfolioSyncTypeError(BaseError):
    code = "101006"
    message = "组合同步方式不允许该操作"


# # 组合风险异常 102xxx
class NoRiskError(BaseError):
    code = "102001"
    message = "风险点不存在"


class RiskNotConfirmed(BaseError):
    code = "102002"
    message = "存在未处理的风险点"


class HasResolvingRisk(BaseError):
    code = "102003"
    message = "存在解决中的风险点"


# # 装备异常 103xxx
class NoEquipError(BaseError):
    code = "103001"
    message = "装备不存在"


class EquipAlreadyExist(BaseError):
    code = "103002"
    message = "装备已存在"


class EquipCanNotBeSubscribed(BaseError):
    code = "103003"
    message = "装备无法被订阅"


class EquipStatusError(BaseError):
    code = "103004"
    message = "装备状态错误"


class EquipTooMany(BaseError):
    code = "103005"
    message = "创建装备数达到上限"


class EquipVersionError(BaseError):
    code = "103006"
    message = "装备版本错误"


class EquipNameExistError(BaseError):
    code = "103007"
    message = "该装备名称已存在"


class EquipCreateNotAllowed(BaseError):
    code = "103008"
    message = "不允许厂商创建装备"


class EquipmentDeleteNotAllowed(BaseError):
    code = "103009"
    message = "不允许厂商删除装备"


# # 机器人异常 104xxx
class NoRobotError(BaseError):
    code = "104001"
    message = "机器人不存在"


class RobotAlreadyExist(BaseError):
    code = "104002"
    message = "机器人已存在"


class RobotCanNotBeSubscribed(BaseError):
    code = "104003"
    message = "机器人无法被订阅"


class RobotStatusError(BaseError):
    code = "104004"
    message = "机器人状态错误"


class RobotCreateError(BaseError):
    code = "104005"
    message = "机器人创建错误"


class RobotUpdateError(BaseError):
    code = "104006"
    message = "机器人修改错误"


class RobotTooMany(BaseError):
    code = "104006"
    message = "创建机器人达到上限"


# # 活动异常 105xxx
class ActivityAlreadyJoined(BaseError):
    code = "105001"
    message = "您已经参加过该活动，不能重复参加"


# # 订单异常 106xxx
class OrderAuthError(BaseError):
    code = "106001"
    message = "不允许对他人组合进行订单买卖！"


class OrderDoesNotExist(BaseError):
    code = "106002"
    message = "订单不存在"


# # 股票异常 107xxx
class StockDoesNotExist(BaseError):
    code = "107001"
    message = "未持有该股票"


class StockDoesNotSell(BaseError):
    code = "107002"
    message = "今日买入的股票不能卖出"


class StockPoolEmpty(BaseError):
    code = "107003"
    message = "股票信息为空，请检查redis股票信息！"


# # 股票行情异常 108xxx
class HQDataError(BaseError):
    code = "108001"
    message = "获取行情数据错误！"


# # 计算战斗力异常
class CalculateAbilityError(BaseError):
    code = "109001"
    message = "获取行情数据错误！"


# # 消息异常 109xxx
# # 运营数据异常 110xxx
# # 标签异常 111xxx
# # 解决方案异常 112xxx


# # 配置异常 113xxx
class NoConfigError(BaseError):
    code = "113001"
    message = "该配置不存在"


# # 数据库异常 114xxx
class DataBaseError(BaseError):
    code = "114001"
    message = "数据库错误，请联系客服或者管理员"


class DBConnectionError(BaseError):
    code = "114002"
    message = "数据库连接错误，请联系客服或者管理员"


class CRUDError(BaseError):
    code = "114003"
    message = "数据库操作错误，请联系客服或者管理员"


class CRUDOperatorError(BaseError):
    code = "114004"
    message = "数据库操作符使用错误"


class TableFieldError(BaseError):
    code = "114005"
    message = "数据库表字段错误"


class EntityDoesNotExist(BaseError):
    code = "114006"
    message = "数据库未找到该实体"


class RecordDoesNotExist(BaseError):
    code = "114007"
    message = "未查询到记录信息"


# # 厂商数据异常 115xxx


class ClientPermissionDenied(BaseError):
    code = "115001"
    message = "厂商权限不足，请联系客服或者管理员"


class ClientHasNoConfig(BaseError):
    code = "115002"
    message = "厂商无该配置，请联系客服或者管理员"


class RobotNoPermissionToUse(BaseError):
    code = "115003"
    message = "没有该机器人的使用权限，请联系客服或者管理员"


class HasNoAvailableRobot(BaseError):
    code = "115004"
    message = "该厂商未配置可用机器人，请联系管理员"


class EquipNoPermissionToUse(BaseError):
    code = "115005"
    message = "没有该装备的使用权限，请联系客服或者管理员"


class HasNoAvailableEquip(BaseError):
    code = "115006"
    message = "该厂商未配置可用装备，请联系管理员"


# # 文件异常 116xxx
class FileDownloadError(BaseError):
    code = "116001"
    message = "文件下载失败"


class FileUploadError(BaseError):
    code = "116002"
    message = "文件上传失败"


class NoFileError(BaseError):
    code = "116003"
    message = "文件不存在"


# # 权限异常 117xxx
class PermissionAlreadyExist(BaseError):
    code = "117001"
    message = "权限已存在"


class PermissionDoesNotExist(BaseError):
    code = "117002"
    message = "权限不存在"


class CreateQuantityLimit(BaseError):
    code = "117003"
    message = "创建数达到上限"


# # 角色异常 118xxx
class RoleAlreadyExist(BaseError):
    code = "117001"
    message = "角色已存在"


# ################## 交易系统异常：2xxxxx ##################
class NotInTradingHour(BaseError):
    code = "200001"
    message = "当前不在交易时间！"


class RegisterExternalSystemFailed(BaseError):
    code = "200002"
    message = "注册外部交易系统失败，请联系客服或者管理员"


class AccountAssetError(BaseError):
    code = "200003"
    message = "查询持仓数据失败"


class FundAssetError(BaseError):
    code = "200004"
    message = "账户资产查询失败"


class NoneStkAsset(BaseError):
    code = "200005"
    message = "无历史持仓数据,不进行评估战斗力计算"


class CancelOrderError(BaseError):
    code = "200006"
    message = "撤单失败"


class TradeDateError(BaseError):
    code = "200007"
    message = "交易日期错误"


# ################## 策略数据异常： 3xxxxx ##################
# # 信号异常：301xxx
class StrategySignalError(BaseError):
    code = "301001"
    message = "策略信号异常"


class StrategyDataError(BaseError):
    code = "301002"
    message = "策略数据异常"


# # 流水异常：302xxx
# ################## 社区异常：4xxxxx ##################
class DiscuzqCustomError(BaseError):
    code = "400001"
    message = "社区错误"


# # 账户异常： 401xxx
# # 文章异常： 402xxx
class NoPostError(BaseError):
    code = "402001"
    message = "社区文章不存在"


# # 评论异常： 403xxx


# 接口
class ParamsError(BaseError):
    code = "500001"
    message = "参数错误，请按要求传参！"


class NoActionError(BaseError):
    code = "500002"
    message = "没有该动作，请重试"


class NoDataError(BaseError):
    code = "500003"
    message = "无数据"


class InvalidManufacturerAPIReq(BaseError):
    code = "500004"
    message = "数据源身份验证失败"

# 消息
class SMSSendError(BaseError):
    code = "600001"
    message = "短消息发送失败"