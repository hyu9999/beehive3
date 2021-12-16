from app.schedulers.base.job_utils import JobTools, JobAbs
from app.schedulers.message.config import send_equipment_signal_message_config


class MessageJobs(JobAbs):
    @classmethod
    def common(cls, *args):
        pass

    @classmethod
    def master(cls, app):
        JobTools.add_base(app, send_equipment_signal_message_config)

    @classmethod
    def mfrs(cls, *args):
        pass
