import re

EIGHT_NUMBERS_RE = re.compile(r"^\d{8}$")
SIX_NUMBERS_RE = re.compile(r"^\d{6}$")
MOBILE_RE = r"(13[0-9]|14[5-9]|15[0-3,5-9]|16[2,5,6,7]|17[0-8]|18[0-9]|19[0-3,5-9])[0-9]{8}$"
PASSWORD_RE = r"[A-Za-z0-9@#$%^&+=]{6,20}"
ROBOT_SID_RE = r"^10[\d]{6}[\w]{4}[\d]{2}$"
EQUIPMENT_SID_RE = r"^(01|02|03|04|05|06|07|08|09|11|12|13|15|16|17|18|20|21|22|23)[\d]{6}[\w]{4}[\d]{2}$"
STRATEGY_RE = r"^(01|02|03|04|05|06|07|08|09|11|12|13|15|16|17|18|20|21|22|23|10)[\d]{6}[\w]{4}[\d]{2}$"
NEW_SCREEN_SID_RE = r"^(02|08|09|12|23)[\d]{6}[\w]{4}[\d]{2}$"
SCREEN_SID_RE = r"^02[\d]{6}[\w]{4}[\d]{2}$"
TIMING_SID_RE = r"^03[\d]{6}[\w]{4}[\d]{2}$"
大类资产配置_SID_RE = r"^06[\d]{6}[\w]{4}[\d]{2}$"
基金定投_SID_RE = r"^07[\d]{6}[\w]{4}[\d]{2}$"
