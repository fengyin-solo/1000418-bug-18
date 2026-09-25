"""运营指标的统一口径：模块顺序、展示名与状态判定都只在这里定义一次。

概览看板和各业务模块列表页都走这份口径，保证「今日新增 / 待处理 / 异常量」
在任何页面、刷新后都对得上：

- 今日新增（created）：模块下的全部记录条数；
- 待处理（pending）：记录当前状态位于流程前两段（待办、办理中），即还没流转到结论态；
- 异常量（abnormal）：记录落在该模块的负向结论状态上，例如标记超标、登记故障、
  退回污泥、判定不合格、下发整改这类结果。
"""
from __future__ import annotations

from typing import Any

# 模块顺序与侧边栏入口保持一致：(模块键, 入口展示名)
MODULES: tuple[tuple[str, str], ...] = (
    ("plant", "厂区单元"),
    ("inflow", "进水监测"),
    ("effluent", "出水监测"),
    ("aeration", "曝气控制"),
    ("dosing", "加药管理"),
    ("sludge", "污泥处置"),
    ("dewater", "脱水运行"),
    ("pump", "泵站运行"),
    ("blower", "鼓风机组"),
    ("membrane", "膜组件"),
    ("online", "在线仪表"),
    ("sample", "取样检测"),
    ("chemical", "药剂出入"),
    ("energy", "能耗管理"),
    ("alarm", "报警中心"),
    ("maint", "设备检修"),
    ("permit", "受限空间作业"),
    ("audit", "达标审核"),
)

MODULE_LABELS: dict[str, str] = dict(MODULES)

# 各模块的完整状态流转顺序，与各自 service 的 ACTION_RULES 保持一致。
STATUS_FLOW: dict[str, list[str]] = {
    "plant": ["待调试", "正常运行", "减量运行", "已停用"],
    "inflow": ["待检测", "检测中", "已记录", "已作废"],
    "effluent": ["待检测", "检测中", "已达标", "已超标"],
    "aeration": ["待调节", "已调节", "待复核", "已锁定"],
    "dosing": ["待投加", "投加中", "已投加", "已撤销"],
    "sludge": ["待外运", "运输中", "已接收", "已退回"],
    "dewater": ["待开机", "运行中", "已停机", "故障停机"],
    "pump": ["待启泵", "运行中", "待检修", "已停泵"],
    "blower": ["待启用", "运行中", "维护中", "已停用"],
    "membrane": ["待投用", "运行中", "待清洗", "已更换"],
    "online": ["待校准", "在运正常", "数据异常", "已停用"],
    "sample": ["待取样", "检测中", "合格", "不合格"],
    "chemical": ["待审核", "已审核", "已出入库", "已作废"],
    "energy": ["待填报", "已填报", "已复核", "有争议"],
    "alarm": ["待确认", "已确认", "已处置", "已忽略"],
    "maint": ["待受理", "检修中", "待验收", "已验收"],
    "permit": ["待申请", "已受理", "已许可", "已驳回", "已过期"],
    "audit": ["待审核", "审核中", "已通过", "需整改"],
}

# 各模块的负向结论状态：标记超标、登记故障、退回污泥等都要计入异常量。
ABNORMAL_STATUSES: dict[str, frozenset[str]] = {
    "plant": frozenset({"已停用"}),
    "inflow": frozenset({"已作废"}),
    "effluent": frozenset({"已超标"}),
    "aeration": frozenset(),
    "dosing": frozenset({"已撤销"}),
    "sludge": frozenset({"已退回"}),
    "dewater": frozenset({"故障停机"}),
    "pump": frozenset(),
    "blower": frozenset({"已停用"}),
    "membrane": frozenset(),
    "online": frozenset({"数据异常", "已停用"}),
    "sample": frozenset({"不合格"}),
    "chemical": frozenset({"已作废"}),
    "energy": frozenset({"有争议"}),
    "alarm": frozenset({"已忽略"}),
    "maint": frozenset(),
    "permit": frozenset({"已驳回", "已过期"}),
    "audit": frozenset({"需整改"}),
}

# 每个模块状态流的前两段（待办、办理中）算待处理。
PENDING_STATUSES: dict[str, frozenset[str]] = {
    module: frozenset(statuses[:2]) for module, statuses in STATUS_FLOW.items()
}


def is_pending(module: str, status: Any) -> bool:
    """记录是否还处于待处理状态。"""
    return status in PENDING_STATUSES.get(module, frozenset())


def is_abnormal(module: str, status: Any) -> bool:
    """记录是否落在负向结论状态，属于异常量统计范围。"""
    return status in ABNORMAL_STATUSES.get(module, frozenset())


def sync_flags(module: str, row: dict[str, Any]) -> dict[str, Any]:
    """按统一口径回写 pending / abnormal 标记，避免历史标记与状态不一致。"""
    status = row.get("status")
    row["pending"] = is_pending(module, status)
    row["abnormal"] = is_abnormal(module, status)
    return row


def module_stats(module: str, rows: list[dict[str, Any]]) -> dict[str, int]:
    """单个模块的三项指标，概览与模块列表页共用同一份计算结果。"""
    return {
        "created": len(rows),
        "pending": sum(1 for row in rows if is_pending(module, row.get("status"))),
        "abnormal": sum(1 for row in rows if is_abnormal(module, row.get("status"))),
    }
