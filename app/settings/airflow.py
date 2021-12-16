from pydantic import Field, EmailStr
from typing import List

from app.settings import OtherSettings


class AirflowSettings(OtherSettings):
    base_url: str = Field(..., env="airflow_base_url")
    api_url: str = Field(..., env="airflow_api_url")
    dag_url: str = Field(..., env="airflow_dag_url")
    test_url: str = Field(..., env="airflow_test_url")
    emails: List[EmailStr] = Field(..., env="airflow_user_email")
