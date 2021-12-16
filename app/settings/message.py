from pydantic import Field

from app.settings import OtherSettings


class SMSSettings(OtherSettings):
    secret_id: str = Field(..., env="sms_secret_id")
    secret_key: str = Field(..., env="sms_secret_key")
    endpoint: str = Field(..., env="sms_endpoint")
    sdk_app_id: str = Field(..., description="短信应用ID", env="sms_sdk_app_id")
    sign: str = Field(..., description="短信签名内容", env="sms_sign")
    template_id: str = Field(..., description="模板ID", env="sms_template_id")
    expire: int = Field(..., description="短信验证码过期时长", env="sms_expire")
    switch: bool = Field(..., description="短信开关", env="sms_switch")
    fixed_code: str = Field(..., description="固定的短信验证码", env="sms_fixed_code")


class EmailSettings(OtherSettings):
    address: str = Field(..., description="发送邮件地址", env="email_address")
    password: str = Field(..., description="发送邮件密码", env="email_password")
    smtp_server: str = Field(..., description="邮件服务器地址", env="smtp_server")
    smtp_server_port: int = Field(..., description="邮件服务器端口", env="smtp_server_port")


class WechatSettings(OtherSettings):
    app_id: str = Field(..., description="微信APP_ID", env="wechat_app_id")
    app_secret: str = Field(..., description="微信APP_SECRET", env="wechat_app_secret")
