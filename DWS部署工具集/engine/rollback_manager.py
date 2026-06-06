"""
部署回滚管理器 — 在执行破坏性操作前自动备份

设计原则:
  - 不改 core_engine.py 一行，在 app.py 层包装
  - 只备份受影响的配置文件，不备份整个系统
  - 每个回滚点独立，支持按步骤回滚
"""

import os
import time
import json
from datetime import datetime
from typing import Optional
from dataclasses import dataclass, field


# 定义哪些步骤需要回滚保护
ROLLBACK_STEPS = {
    # 阶段1: 环境准备
    "chrony": {"phase": 1, "files": ["/etc/chrony.conf"]},
    # 阶段2: OS 调优
    "disable_audit": {"phase": 2, "files": [], "cmd_undo": "systemctl start auditd && systemctl enable auditd"},
    "disable_firewall": {"phase": 2, "files": [], "cmd_undo": "systemctl start firewalld && systemctl enable firewalld"},
    "selinux": {"phase": 2, "files": ["/etc/selinux/config"]},
    "disable_thp": {"phase": 2, "files": ["/etc/default/grub", "/boot/efi/EFI/kylin/grub.cfg"]},
    "watermark": {"phase": 2, "files": ["/etc/sysctl.conf"]},
    "swap_ipv6": {"phase": 2, "files": ["/etc/fstab"]},
    # 阶段4: 磁盘规划
    "fstab": {"phase": 4, "files": ["/etc/fstab"]},
}


@dataclass
class RollbackPoint:
    """单个回滚点"""
    phase_id: int
    step_id: str
    backups: dict = field(default_factory=dict)  # {filepath: content}
    cmd_undo: str = ""                           # 逆操作命令
    created_at: str = ""
    executed: bool = False


class RollbackManager:
    """回滚管理器 — 按栈顺序回滚"""

    def __init__(self):
        self._points: list[RollbackPoint] = []
        self._backup_dir = ""

    def set_backup_dir(self, path: str):
        """设置备份目录"""
        self._backup_dir = path
        os.makedirs(path, exist_ok=True)

    def create_point(self, phase_id: int, step_id: str) -> Optional[RollbackPoint]:
        """在执行步骤前创建回滚点

        Args:
            phase_id: 阶段 ID
            step_id: 步骤 ID

        Returns:
            RollbackPoint 或 None（无需回滚的步骤）
        """
        if step_id not in ROLLBACK_STEPS:
            return None

        rule = ROLLBACK_STEPS[step_id]
        point = RollbackPoint(
            phase_id=phase_id,
            step_id=step_id,
            created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            cmd_undo=rule.get("cmd_undo", ""),
        )

        # 备份受影响文件
        for fp in rule.get("files", []):
            content = self._backup_file(fp)
            if content is not None:
                point.backups[fp] = content

        self._points.append(point)
        return point

    def _backup_file(self, filepath: str) -> Optional[str]:
        """备份文件内容，返回内容或 None"""
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return f.read()
        except (FileNotFoundError, IOError, OSError):
            return None

    def rollback_last(self) -> Optional[dict]:
        """回滚最近一个步骤

        Returns:
            {"step_id": ..., "files_restored": N, "cmd_undo": "..."}
        """
        if not self._points:
            return None
        point = self._points.pop()
        return self._execute_rollback(point)

    def rollback_to(self, phase_id: int, step_id: str) -> list:
        """回滚到指定步骤（含该步骤之后的所有步骤）

        Args:
            phase_id: 阶段 ID
            step_id: 步骤 ID

        Returns:
            已回滚的步骤列表
        """
        rolled_back = []
        while self._points:
            last = self._points[-1]
            self._points.pop()
            result = self._execute_rollback(last)
            if result:
                rolled_back.append(result)
            # 检查是否已回滚到目标
            if last.phase_id == phase_id and last.step_id == step_id:
                break
        return rolled_back

    def _execute_rollback(self, point: RollbackPoint) -> dict:
        """执行单个回滚点"""
        files_restored = 0
        for fp, content in point.backups.items():
            try:
                with open(fp, "w", encoding="utf-8") as f:
                    f.write(content)
                files_restored += 1
            except (IOError, OSError):
                pass
        point.executed = True
        return {
            "step_id": point.step_id,
            "phase_id": point.phase_id,
            "files_restored": files_restored,
            "cmd_undo": point.cmd_undo,
            "created_at": point.created_at,
        }

    def list_points(self) -> list:
        """列出当前所有回滚点"""
        return [
            {
                "phase_id": p.phase_id,
                "step_id": p.step_id,
                "files": list(p.backups.keys()),
                "created_at": p.created_at,
                "executed": p.executed,
            }
            for p in self._points
        ]

    @property
    def has_points(self) -> bool:
        return len(self._points) > 0


# 全局单例
_manager: Optional[RollbackManager] = None


def get_rollback_manager() -> RollbackManager:
    global _manager
    if _manager is None:
        _manager = RollbackManager()
    return _manager
