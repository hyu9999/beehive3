from bson import ObjectId

from app.enums.portfolio import 风险点状态, 风险类型

risks_const = [
        {
            "id": ObjectId(),
            "status": 风险点状态.confirmed,
            "risk_type": 风险类型.adjustment_cycle,
            "symbol": "600200",
            "exchange": "1",
        },
        {
            "id": ObjectId(),
            "status": 风险点状态.confirmed,
            "risk_type": 风险类型.overweight,
        },
        {
            "id": ObjectId(),
            "status": 风险点状态.confirmed,
            "risk_type": 风险类型.clearance_line,
        },
    ]
