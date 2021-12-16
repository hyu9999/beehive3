import smtplib
from email.header import Header
from email.mime.text import MIMEText
from email.utils import formataddr, parseaddr
from typing import List, Union

from app import settings
from app.outer_sys.message.adaptor.base import SendAdaptor
from app.outer_sys.message.html_template import generate_html_page


class SendEmail(SendAdaptor):
    """发送邮件"""

    def send_code(self, *args, **kwargs):
        pass

    def __init__(self):
        self.email_address = settings.email.address
        self.email_password = settings.email.password
        self.smtp_server = settings.email.smtp_server
        self.smtp_server_port = settings.email.smtp_server_port

        self.client = self._client()
        # 登陆服务器
        self.client.login(self.email_address, self.email_password)

    def _client(self):
        # 服务端配置，账密登陆
        client = smtplib.SMTP(self.smtp_server, self.smtp_server_port)
        return client

    def _send_email(self, to_addr: List[str], message: MIMEText):
        return self.client.sendmail(self.email_address, to_addr, message.as_string())  # 发送地址需与登陆的邮箱一致

    @staticmethod
    def _format_addr(address, coding="utf-8"):
        name, addr = parseaddr(address)
        return formataddr((Header(name, coding).encode(), addr))

    def _generate_message(self, to_addr, title, content, send_type, coding):
        if send_type == "html":
            content = generate_html_page(title, content)
        # 内容初始化，定义内容格式（普通文本，html）
        msg = MIMEText(content, send_type, coding)
        # 邮件标题
        msg["Subject"] = Header(title, coding).encode()  # 腾讯邮箱略过会导致邮件被屏蔽

        # 传入昵称和邮件地址
        msg["From"] = self._format_addr(self.email_address)  # 腾讯邮箱可略
        msg["To"] = self._format_addr(to_addr)  # 腾讯邮箱可略
        return msg

    def _send(self, to_addr: List[str], title: str, content: str, send_type: str = "plain", coding: str = "utf-8"):
        # 构建邮件MIME对象
        msg = self._generate_message(to_addr, title, content, send_type, coding)
        # 发送邮件及退出
        return self._send_email(to_addr, msg)

    def quit(self):
        self.client.quit()

    def send(self, *, to_addr: Union[List[str], str], title: str, content: str, send_type: str = "plain", coding: str = "utf-8"):
        """


        Parameters
        ----------
        to_addr     接收邮件邮箱地址
        title       邮件标题
        content     邮件内容
        send_type   邮件类型
        coding      编码格式

        Returns
        -------

        """
        if isinstance(to_addr, str):
            to_addr = [to_addr]
        senders = self._send(to_addr, title, content, send_type, coding)
        return self.format_return_message(senders)

    def format_return_message(self, data):
        if data:
            return {"code": 1, "error_message": data}
        else:
            return {"code": 0, "message": "success"}
