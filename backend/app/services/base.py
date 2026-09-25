"""模块业务规则的公共基类。

各模块统计卡片都通过这里的 ``stats`` 取数，底层与运营概览共用
``store.module_summary`` 的同一份口径，保证看板与列表页数字一致。
"""
from __future__ import annotations

from app.store import store


class ModuleService:
    MODULE: str = ""

    def stats(self) -> dict[str, int]:
        return store.module_summary(self.MODULE)
