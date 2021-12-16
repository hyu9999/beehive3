from enum import Enum, unique


@unique
class TagType(str, Enum):
    机器人 = "机器人"
    装备 = "装备"
    组合 = "组合"
