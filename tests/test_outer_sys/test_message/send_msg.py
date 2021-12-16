from copy import deepcopy

from app.outer_sys.message.adaptor.mail import SendEmail
from app.outer_sys.message.adaptor.sms import SendSMS
from app.outer_sys.message.adaptor.wechat import SendWechatMessage
from app.outer_sys.message.send_msg import SendMessage
from tests.consts.message import email_input, sms_input, wechat_input


def test_send_mail():
    s = SendEmail()
    email_input_copy = deepcopy(email_input)
    data = s.send(**email_input_copy)
    assert data["code"] == 0
    email_input_copy["to_addr"] = ["aaa", "757147959@qq.com"]
    data = s.send(**email_input_copy)
    assert data["code"] == 1
    s.quit()


def test_send_sms():
    sms = SendSMS()
    sms_input_copy = deepcopy(sms_input)
    data = sms.send(**sms_input_copy)
    assert data["code"] == 0
    sms_input_copy["template_id"] = "123"
    data = sms.send(**sms_input_copy)
    assert data["code"] == 1


def test_send_wechat():
    swm = SendWechatMessage()
    wechat_input_copy = deepcopy(wechat_input)
    data = swm.send(**wechat_input_copy)
    assert data["code"] == 0
    wechat_input_copy["open_id"] = "123"
    data = swm.send(**wechat_input_copy)
    assert data["code"] == 40003


def test_send_msg():
    email_input_copy = deepcopy(email_input)
    adapt = SendEmail()
    sm = SendMessage(adapt)
    sm.send(**email_input_copy)

    sms_input_copy = deepcopy(sms_input)
    adapt = SendSMS()
    sm = SendMessage(adapt)
    sm.send(**sms_input_copy)

    wechat_input_copy = deepcopy(wechat_input)
    adapt = SendWechatMessage()
    sm = SendMessage(adapt)
    sm.send(**wechat_input_copy)
