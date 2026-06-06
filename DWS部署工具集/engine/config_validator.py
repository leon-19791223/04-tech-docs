"""
DWS 配置参数校验器 — 输入防错

校验规则:
  - IP 地址格式
  - 端口号范围 (1024-65535)
  - 集群名命名规范 (字母开头, 字母数字下划线)
  - 数字范围校验
"""

import re
from typing import Optional


class ValidationError:
    """单个校验错误"""
    def __init__(self, field: str, message: str):
        self.field = field
        self.message = message

    def to_dict(self) -> dict:
        return {"field": self.field, "message": self.message}


class ConfigValidator:
    """配置参数校验器"""

    RULES = {
        # 基础信息
        "cluster_name": {
            "type": "regex",
            "pattern": r'^[a-zA-Z][a-zA-Z0-9_-]{1,31}$',
            "message": "集群名: 字母开头, 2-32位字母/数字/下划线/连字符",
            "required": True,
        },
        "environment": {
            "type": "choice",
            "choices": ["DEV", "SIT", "UAT", "PREPROD"],
            "message": "环境: 必须为 DEV/SIT/UAT/PREPROD",
            "required": True,
        },
        # 网络
        "master_node1_ip": {
            "type": "ip",
            "message": "节点1 IP: 格式错误 (示例: 10.134.21.190)",
            "required": True,
        },
        "master_node2_ip": {
            "type": "ip",
            "message": "节点2 IP: 格式错误 (示例: 10.134.21.191)",
            "required": False,
        },
        # 端口
        "db_port": {
            "type": "port",
            "message": "数据库端口: 范围 1024-65535 (默认 40080)",
            "required": False,
            "default": 40080,
        },
        "pooler_port": {
            "type": "port",
            "message": "连接池端口: 范围 1024-65535",
            "required": False,
            "default": 25309,
        },
        # 节点数量
        "cn_num": {
            "type": "range",
            "min": 1, "max": 64,
            "message": "CN 数量: 范围 1-64",
            "required": False,
            "default": 3,
        },
        "dn_num": {
            "type": "range",
            "min": 1, "max": 256,
            "message": "DN 数量: 范围 1-256",
            "required": False,
            "default": 3,
        },
    }

    def validate(self, config: dict) -> list:
        """校验配置参数

        Args:
            config: 待校验的配置字典

        Returns:
            错误列表，空列表表示全部通过
        """
        errors = []

        for field, rule in self.RULES.items():
            value = config.get(field)
            rule_type = rule["type"]

            # 检查必填
            if rule.get("required") and not value:
                errors.append(ValidationError(field, rule["message"]))
                continue

            # 跳过空值（非必填字段）
            if not value:
                continue

            # 按类型校验
            if rule_type == "regex":
                if not re.match(rule["pattern"], str(value)):
                    errors.append(ValidationError(field, rule["message"]))

            elif rule_type == "ip":
                if not self._is_valid_ip(str(value)):
                    errors.append(ValidationError(field, rule["message"]))

            elif rule_type == "port":
                try:
                    port = int(value)
                    if port < 1024 or port > 65535:
                        errors.append(ValidationError(field, rule["message"]))
                except (ValueError, TypeError):
                    errors.append(ValidationError(field, rule["message"]))

            elif rule_type == "range":
                try:
                    val = int(value)
                    if val < rule["min"] or val > rule["max"]:
                        errors.append(ValidationError(field, rule["message"]))
                except (ValueError, TypeError):
                    errors.append(ValidationError(field, rule["message"]))

            elif rule_type == "choice":
                if value not in rule["choices"]:
                    errors.append(ValidationError(field, rule["message"]))

        return errors

    def _is_valid_ip(self, ip: str) -> bool:
        """验证 IPv4 地址"""
        pattern = r'^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$'
        m = re.match(pattern, ip)
        if not m:
            return False
        return all(0 <= int(g) <= 255 for g in m.groups())

    def get_defaults(self) -> dict:
        """获取默认值"""
        return {
            field: rule.get("default")
            for field, rule in self.RULES.items()
            if rule.get("default") is not None
        }


# 全局单例
_validator: Optional[ConfigValidator] = None


def get_validator() -> ConfigValidator:
    global _validator
    if _validator is None:
        _validator = ConfigValidator()
    return _validator
