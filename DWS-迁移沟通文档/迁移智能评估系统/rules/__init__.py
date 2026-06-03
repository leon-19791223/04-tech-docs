"""
规则包 - 导入所有子模块触发自动注册到规则注册表
Web UI 和 CLI 只需 import rules 即可发现所有迁移路径
"""
from . import gp_to_dws
from . import oracle_to_dws
from . import mysql_to_dws
from . import mssql_to_dws
from . import db2_to_dws
from . import teradata_to_dws
