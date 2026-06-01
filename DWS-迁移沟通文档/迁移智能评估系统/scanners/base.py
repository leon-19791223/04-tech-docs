"""源端扫描器抽象基类"""

from abc import ABC, abstractmethod
from core.models import MigrationMetadata


class BaseScanner(ABC):
    """所有源端扫描器的基类

    子类实现 scan() 方法，返回 MigrationMetadata
    """

    def __init__(self, source_type: str = "unknown"):
        self.source_type = source_type

    @abstractmethod
    def scan(self) -> MigrationMetadata:
        """采集源端元数据"""
        ...

    def get_metadata(self) -> MigrationMetadata:
        """获取元数据（带日志包装）"""
        meta = self.scan()
        return meta
