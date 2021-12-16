from app.outer_sys.message.adaptor.base import SendAdaptor


class MockSendSMS(SendAdaptor):
    def send(self, *args, **kwargs):
        pass

    def format_return_message(self, *args, **kwargs):
        pass

    def send_code(self, *, mobile: str):
        return {
            "serial_no": "",
            "mobile": f"+86{mobile}",
            "fee": 0,
            "session_context": "",
            "code": "Ok",
            "message": "send success",
            "iso_code": "CN",
            "sms_code": "222222",
        }


class MockSendMessage:
    """消息发送类"""

    def __init__(self, adaptor: SendAdaptor):
        self.adaptor = adaptor

    def send(self, **kwargs):
        self.adaptor.send(**kwargs)

    def send_code(self, **kwargs):
        return self.adaptor.send_code(**kwargs)
