import json
from typing import List

from tencentcloud.common import credential
from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile
from tencentcloud.sms.v20190711 import sms_client, models

from app import settings
from app.core.errors import SMSSendError
from app.extentions import logger
from app.outer_sys.message.adaptor.base import SendAdaptor
from app.outer_sys.message.utils import verification_code


class SendSMS(SendAdaptor):
    """
    发送短信

    docs: https://cloud.tencent.com/document/product/382/43196
    """

    def __init__(self):
        self.secret_id = settings.sms.secret_id
        self.secret_key = settings.sms.secret_key
        self.endpoint = settings.sms.endpoint
        self.client = self._client()

    def _client(self):
        """
        sms client

        Returns
        -------

        """
        cred = credential.Credential(self.secret_id, self.secret_key)
        http_profile = HttpProfile()
        http_profile.endpoint = self.endpoint

        client_profile = ClientProfile()
        client_profile.httpProfile = http_profile
        client = sms_client.SmsClient(cred, "", client_profile)
        return client

    def send(self, *, template_id: str, phone_number_set: List[str], **kwargs):
        """

        Parameters
        ----------
        template_id : 模板id
        phone_number_set : 接收短信的手机列表

        Returns
        -------

        """
        params = {
            "SmsSdkAppid": settings.sms.sdk_app_id,
            "Sign": settings.sms.sign,
            "TemplateID": template_id,
            "PhoneNumberSet": [f"+86{x}" for x in phone_number_set],
        }
        params.update(**kwargs)
        try:
            req = models.SendSmsRequest()
            req.from_json_string(json.dumps(params))
            resp = self.client.SendSms(req)
        except TencentCloudSDKException as err:
            logger.error(err)
            raise SMSSendError(message=f"短消息发送错误, 错误原因：{err}")
        else:
            return self.format_return_message(json.loads(resp.to_json_string()))

    def format_return_message(self, data):
        ret_data = []
        for i in data["SendStatusSet"]:
            ret_data.append(
                {
                    "serial_no": i["SerialNo"],
                    "mobile": i["PhoneNumber"],
                    "fee": i["Fee"],
                    "session_context": i["SessionContext"],
                    "code": i["Code"],
                    "message": i["Message"],
                    "iso_code": i["IsoCode"],
                }
            )
        return ret_data

    def send_code(self, *, mobile: str):
        """
        发送短信验证码

        Parameters
        ----------
        mobile

        Returns
        -------

        """
        sms_code = verification_code()
        kwargs = {
            "template_id": settings.sms.template_id,
            "phone_number_set": [mobile],
            "TemplateParamSet": [str(sms_code), str(settings.sms.expire)],
        }
        data = self.send(**kwargs)[0]
        if data["code"] != "Ok":
            raise SMSSendError(message=f"短消息发送错误, 错误原因：{data['message']}")
        data["sms_code"] = sms_code
        return data
