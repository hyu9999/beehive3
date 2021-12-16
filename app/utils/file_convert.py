import json
from copy import deepcopy
from typing import List

from motor.motor_asyncio import AsyncIOMotorClient
from ruamel.yaml import YAML, StringIO

from app.crud.base import get_equipment_collection

try:
    import xml.etree.cElementTree as xml
except ImportError:
    import xml.etree.ElementTree as xml


def format_line(parent_root: xml.Element) -> dict:
    pass


def format_robot(parent_root: xml.Element) -> dict:
    pass


def format_equipment(equipment_root: xml.Element) -> dict:
    """
    格式化装备输出

    Parameters
    ----------
    equipment_root

    Returns
    -------

    """
    for sec_obj in equipment_root.findall("Array"):
        as_name = sec_obj.attrib.pop("as")
        if as_name == "depends_on":  # 读取依赖项
            equipment_root.attrib["depends_on"] = [x.attrib["value"] for x in sec_obj.findall("add")]
        if as_name == "trigger_by":  # 读取触发器
            triggers = []
            for trigger in sec_obj.findall("Object"):
                triggers.append(trigger.attrib)
            equipment_root.attrib["trigger_by"] = triggers
    # 读取装备配置
    for sec_obj in equipment_root.findall("Object"):
        if sec_obj.attrib.pop("as") == "config":
            equipment_root.attrib["config"] = sec_obj.attrib
            for i in sec_obj.findall("Object"):
                equipment_root.attrib["config"][i.attrib["as"]] = [x.attrib for x in i.findall("Object")]
    equipment_root.attrib["别名"] = equipment_root.attrib.get("别名") or equipment_root.attrib["名称"]
    return equipment_root.attrib


async def format_package(conn: AsyncIOMotorClient, equipment_root: xml.Element) -> List[dict]:
    """
    格式化装备(包)输出

    Parameters
    ----------
    conn
    equipment_root

    Returns
    -------

    """
    for sec_obj in equipment_root.findall("Array"):
        as_name = sec_obj.attrib.pop("as")
        if as_name == "depends_on":  # 读取依赖项
            equipment_root.attrib["depends_on"] = [x.attrib["value"] for x in sec_obj.findall("add")]
        if as_name == "trigger_by":  # 读取触发器
            triggers = []
            for trigger in sec_obj.findall("Object"):
                triggers.append(trigger.attrib)
            equipment_root.attrib["trigger_by"] = triggers
    # 读取装备配置
    for sec_obj in equipment_root.findall("Object"):
        if sec_obj.attrib.pop("as") == "config":
            equipment_root.attrib["config"] = sec_obj.attrib
            for i in sec_obj.findall("Object"):
                equipment_root.attrib["config"][i.attrib["as"]] = [x.attrib for x in i.findall("Object")]
    equipment_root.attrib["别名"] = equipment_root.attrib.get("别名") or equipment_root.attrib["名称"]
    equipment_list = await get_equipment_collection(conn).find_one({"标识符": equipment_root.attrib["标识符"]})
    ret_data = []
    for sid in equipment_list["装备列表"]:
        equipment = await get_equipment_collection(conn).find_one({"标识符": sid})
        tmp_dict = deepcopy(equipment_root.attrib)
        tmp_dict["标识符"] = equipment["标识符"]
        tmp_dict["名称"] = tmp_dict["别名"] = equipment["名称"]
        tmp_dict["一级分类"] = equipment.get("一级分类", tmp_dict["一级分类"])
        tmp_dict["二级分类"] = equipment.get("二级分类", tmp_dict["二级分类"])
        ret_data.append(tmp_dict)
    return ret_data


async def format_robot_xml(conn: AsyncIOMotorClient, element: object, file_path: str = None, **kwargs) -> dict:
    """
    格式化xml文件

    Parameters
    ----------
    conn
    element
    file_path

    Returns
    -------

    """
    tree = xml.ElementTree(element=element, file=file_path)
    root = tree.getroot()
    ret_data = {}
    equipment_list = []
    for obj in root.iter("Object"):  # 获取全部Object元素
        attrib = obj.attrib
        if "as" not in attrib.keys():
            continue
        as_name = attrib.pop("as")
        if as_name == "robot":  # 机器人基本信息
            ret_data.update(attrib)
        elif as_name == "equipment":  # 装备信息
            if not attrib["标识符"].startswith("11"):
                equipment_list.append(format_equipment(obj))
            else:
                equipment_list.extend(await format_package(conn, obj))
    ret_data["equipment_list"] = equipment_list
    ret_data.update(kwargs)
    # 合并装备资源
    resource_list = [x.get("资源信息") for x in equipment_list if "资源信息" in x.keys()]
    if resource_list:
        resource = []
        ret_data["资源信息"] = list(set([resource.extend(x) for x in resource_list]))
    return ret_data


def load_yaml(fmt_xml: dict):
    """
    将xml格式转换为yaml格式

    Parameters
    ----------
    fmt_xml

    Returns
    -------

    """
    data = json.loads(json.dumps(fmt_xml))
    yaml = YAML()
    stream = StringIO()
    yaml.dump(data, stream)
    return stream.getvalue()
