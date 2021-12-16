from time import sleep

import requests

from app import settings
from app.extentions import logger


class AirflowTools(object):
    def __init__(self):
        self.headers = {"content-type": "application/json", "cache-control": "no-cache"}
        self.json_data = {"conf": {"key": "value"}}

    def check_api(self):
        rsp = requests.get(settings.airflow.test_url, headers=self.headers, json=self.json_data)
        return rsp

    def get_dag(self, dag_id: str):
        """获取dag信息"""
        rsp = requests.get(f"{settings.airflow.dag_url}/{dag_id}/dag_runs", headers=self.headers, json=self.json_data)
        return rsp

    def run_dag(self, dag_id: str):
        """运行dag"""
        rsp = requests.post(f"{settings.airflow.dag_url}/{dag_id}/dag_runs", headers=self.headers, json=self.json_data)
        return rsp

    def unpause_dag(self, dag_id: str):
        """开启dag的开关"""
        response = requests.get(f"{settings.airflow.dag_url}/{dag_id}/paused/false", headers=self.headers, json=self.json_data, timeout=5)
        return response

    def wait_dag_run(self, dag_id: str):
        """运行一次 dag run: airflow更新回测评级数据时，会根据整体评级情况更新相关策略的状态和评级信息"""
        logger.info(f"wait run dag: {dag_id}")
        for _ in range(240):
            # 判断任务是否写入： airflow循环扫描beehive3数据库，发现新的机器人则生成对应的任务
            rsp = self.get_dag(dag_id)
            logger.info(f"get dag:{rsp.text}")
            if rsp.status_code == 200:
                unpause_rsp = self.unpause_dag(dag_id)
                logger.info(f"开启任务:{unpause_rsp.text}")
                if unpause_rsp.status_code == 200:
                    sleep(3)
                    logger.info("开启任务时，如果启动了一个dag则直接结束，否则手动调用运行dag的接口")
                    rsp = self.get_dag(dag_id)
                    if rsp.status_code == 200 and len(rsp.json()) > 0:
                        logger.info(f"already run and break")
                        break
                    # 运行任务：必须是开启状态的任务才可以运行
                    response = self.run_dag(dag_id)
                    logger.info(f"run:{response.text}")
                    if response.status_code == 200:
                        break
            sleep(30)
