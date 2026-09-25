"""内存数据仓库：给每个业务模块准备一份可筛选、可流转的示例数据。

真实项目里这里会换成数据库访问层；当前实现只依赖标准库，保证克隆下来就能起。
"""
from __future__ import annotations

from typing import Any

from app.metrics import MODULES, MODULE_LABELS, module_stats, sync_flags
from app.seed import SEED_ROWS


class Store:
    def __init__(self) -> None:
        self._tables: dict[str, list[dict[str, Any]]] = {
            name: [sync_flags(name, dict(row)) for row in rows]
            for name, rows in SEED_ROWS.items()
        }

    def module_names(self) -> list[str]:
        """按侧边栏入口顺序返回模块键。"""
        return [key for key, _label in MODULES]

    def rows(self, module: str) -> list[dict[str, Any]]:
        return self._tables.setdefault(module, [])

    def find(self, module: str, entry_id: int) -> dict[str, Any] | None:
        for row in self.rows(module):
            if int(row.get("id", 0)) == entry_id:
                return row
        return None

    def stats(self, module: str) -> dict[str, int]:
        """单个模块的统一口径指标，供模块列表接口直接返回。"""
        return module_stats(module, self.rows(module))

    def overview(self) -> dict[str, object]:
        modules: list[dict[str, object]] = []
        for name in self.module_names():
            stats = self.stats(name)
            modules.append({
                "key": name,
                "name": MODULE_LABELS[name],
                **stats,
            })
        cards = [
            {"label": "业务模块", "value": len(modules)},
            {"label": "今日新增", "value": sum(int(item["created"]) for item in modules)},
            {"label": "待处理", "value": sum(int(item["pending"]) for item in modules)},
            {"label": "异常量", "value": sum(int(item["abnormal"]) for item in modules)},
        ]
        return {"cards": cards, "modules": modules}


store = Store()
