from starlette.exceptions import HTTPException
from starlette.status import (
    HTTP_422_UNPROCESSABLE_ENTITY,
    HTTP_404_NOT_FOUND,
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
    HTTP_403_FORBIDDEN,
    HTTP_500_INTERNAL_SERVER_ERROR,
)

from app.core.errors import (
    HttpError,
    NoUserError,
    RegisterExternalSystemFailed,
    NoRiskError,
    StockDoesNotExist,
    RiskNotConfirmed,
    StockDoesNotSell,
    NoneStkAsset,
    NoConfigError,
    HasResolvingRisk,
    PortfolioTooMany,
    ActivityAlreadyJoined,
    OrderAuthError,
    StockPoolEmpty,
    FundAssetError,
    LatestFundAssetInDatabaseError,
    ParamsError,
    NoPortfolioError,
    DiscuzqCustomError,
    AccountAssetError,
    DataBaseError,
    LoginError, PortfolioCanNotBeSubscribed, NoEquipError, EquipCanNotBeSubscribed, NoRobotError,
    RobotCanNotBeSubscribed, HQDataError, DBConnectionError, CRUDError, NotInTradingHour, TokenValidationError,
    TokenAcquisitionError, EquipNoPermissionToUse, HasNoAvailableEquip, RobotNoPermissionToUse, HasNoAvailableRobot,
    ClientPermissionDenied, ClientHasNoConfig, EquipAlreadyExist, PermissionDenied, VIPCodeError, UpgradeVIPError,
    EquipStatusError, RobotStatusError, RobotCreateError, RobotAlreadyExist, FileDownloadError, FileUploadError,
    OrderDoesNotExist, RobotUpdateError, PermissionAlreadyExist, RoleAlreadyExist, PermissionDoesNotExist,
    UserAlreadyExist, NoPostError, EquipTooMany, NoFileError, NoActionError, CancelOrderError,
    TradeDateError, NoDataError, RobotTooMany, PortfolioCloseError, EquipVersionError, CRUDOperatorError,
    PortfolioSyncTypeError, TableFieldError, RecordDoesNotExist, StrategySignalError, StrategyDataError,
    CreateQuantityLimit, SMSSendError)
from app.core.status import HTTP_461_DISC_ERROR


def register_exceptions(app):
    """注册http异常"""
    app.add_exception_handler(HTTPException, HttpError.http_error_handler)
    app.add_exception_handler(HTTP_400_BAD_REQUEST, HttpError.http_400_error_handler)
    app.add_exception_handler(HTTP_401_UNAUTHORIZED, HttpError.http_401_error_handler)
    app.add_exception_handler(HTTP_403_FORBIDDEN, HttpError.http_403_error_handler)
    app.add_exception_handler(HTTP_404_NOT_FOUND, HttpError.http_404_error_handler)
    app.add_exception_handler(HTTP_461_DISC_ERROR, HttpError.http_461_error_handler)
    app.add_exception_handler(HTTP_422_UNPROCESSABLE_ENTITY, HttpError.http_422_error_handler)
    app.add_exception_handler(HTTP_500_INTERNAL_SERVER_ERROR, HttpError.http_500_error_handler)
    # 自定义异常
    app.add_exception_handler(UserAlreadyExist, UserAlreadyExist.handler)
    app.add_exception_handler(NoUserError, NoUserError.handler)
    app.add_exception_handler(LoginError, LoginError.handler)
    app.add_exception_handler(TokenAcquisitionError, TokenAcquisitionError.handler)
    app.add_exception_handler(TokenValidationError, TokenValidationError.handler)
    app.add_exception_handler(PermissionDenied, PermissionDenied.handler)
    app.add_exception_handler(VIPCodeError, VIPCodeError.handler)
    app.add_exception_handler(UpgradeVIPError, UpgradeVIPError.handler)
    app.add_exception_handler(RegisterExternalSystemFailed, RegisterExternalSystemFailed.handler)
    app.add_exception_handler(NoRiskError, NoRiskError.handler)
    app.add_exception_handler(StockDoesNotExist, StockDoesNotExist.handler)
    app.add_exception_handler(RiskNotConfirmed, RiskNotConfirmed.handler)
    app.add_exception_handler(StockDoesNotSell, StockDoesNotSell.handler)
    app.add_exception_handler(NoneStkAsset, NoneStkAsset.handler)
    app.add_exception_handler(CancelOrderError, CancelOrderError.handler)
    app.add_exception_handler(TradeDateError, TradeDateError.handler)
    app.add_exception_handler(NoConfigError, NoConfigError.handler)
    app.add_exception_handler(HasResolvingRisk, HasResolvingRisk.handler)
    app.add_exception_handler(NoEquipError, NoEquipError.handler)
    app.add_exception_handler(EquipAlreadyExist, EquipAlreadyExist.handler)
    app.add_exception_handler(EquipCanNotBeSubscribed, EquipCanNotBeSubscribed.handler)
    app.add_exception_handler(EquipStatusError, EquipStatusError.handler)
    app.add_exception_handler(EquipTooMany, EquipTooMany.handler)
    app.add_exception_handler(EquipVersionError, EquipVersionError.handler)
    app.add_exception_handler(EquipNoPermissionToUse, EquipNoPermissionToUse.handler)
    app.add_exception_handler(HasNoAvailableEquip, HasNoAvailableEquip.handler)
    app.add_exception_handler(FileDownloadError, FileDownloadError.handler)
    app.add_exception_handler(FileUploadError, FileUploadError.handler)
    app.add_exception_handler(NoFileError, NoFileError.handler)
    app.add_exception_handler(PermissionAlreadyExist, PermissionAlreadyExist.handler)
    app.add_exception_handler(PermissionDoesNotExist, PermissionDoesNotExist.handler)
    app.add_exception_handler(CreateQuantityLimit, CreateQuantityLimit.handler)
    app.add_exception_handler(RoleAlreadyExist, RoleAlreadyExist.handler)
    app.add_exception_handler(NoRobotError, NoRobotError.handler)
    app.add_exception_handler(RobotAlreadyExist, RobotAlreadyExist.handler)
    app.add_exception_handler(RobotCanNotBeSubscribed, RobotCanNotBeSubscribed.handler)
    app.add_exception_handler(RobotStatusError, RobotStatusError.handler)
    app.add_exception_handler(RobotCreateError, RobotCreateError.handler)
    app.add_exception_handler(RobotUpdateError, RobotUpdateError.handler)
    app.add_exception_handler(RobotTooMany, RobotTooMany.handler)
    app.add_exception_handler(RobotNoPermissionToUse, RobotNoPermissionToUse.handler)
    app.add_exception_handler(ClientPermissionDenied, ClientPermissionDenied.handler)
    app.add_exception_handler(ClientHasNoConfig, ClientHasNoConfig.handler)
    app.add_exception_handler(HasNoAvailableRobot, HasNoAvailableRobot.handler)
    app.add_exception_handler(PortfolioTooMany, PortfolioTooMany.handler)
    app.add_exception_handler(ActivityAlreadyJoined, ActivityAlreadyJoined.handler)
    app.add_exception_handler(OrderAuthError, OrderAuthError.handler)
    app.add_exception_handler(OrderDoesNotExist, OrderDoesNotExist.handler)
    app.add_exception_handler(StockPoolEmpty, StockPoolEmpty.handler)
    app.add_exception_handler(HQDataError, HQDataError.handler)
    app.add_exception_handler(FundAssetError, FundAssetError.handler)
    app.add_exception_handler(LatestFundAssetInDatabaseError, LatestFundAssetInDatabaseError.handler)
    app.add_exception_handler(PortfolioCanNotBeSubscribed, PortfolioCanNotBeSubscribed.handler)
    app.add_exception_handler(PortfolioCloseError, PortfolioCloseError.handler)
    app.add_exception_handler(PortfolioSyncTypeError, PortfolioSyncTypeError.handler)
    app.add_exception_handler(ParamsError, ParamsError.handler)
    app.add_exception_handler(NoActionError, NoActionError.handler)
    app.add_exception_handler(NoDataError, NoDataError.handler)
    app.add_exception_handler(NoPortfolioError, NoPortfolioError.handler)
    app.add_exception_handler(StrategySignalError, StrategySignalError.handler)
    app.add_exception_handler(StrategyDataError, StrategyDataError.handler)
    app.add_exception_handler(DiscuzqCustomError, DiscuzqCustomError.handler)
    app.add_exception_handler(NoPostError, NoPostError.handler)
    app.add_exception_handler(AccountAssetError, AccountAssetError.handler)
    app.add_exception_handler(DataBaseError, DataBaseError.handler)
    app.add_exception_handler(DBConnectionError, DBConnectionError.handler)
    app.add_exception_handler(CRUDError, CRUDError.handler)
    app.add_exception_handler(CRUDOperatorError, CRUDOperatorError.handler)
    app.add_exception_handler(TableFieldError, TableFieldError.handler)
    app.add_exception_handler(RecordDoesNotExist, RecordDoesNotExist.handler)
    app.add_exception_handler(NotInTradingHour, NotInTradingHour.handler)
    app.add_exception_handler(SMSSendError, SMSSendError.handler)
