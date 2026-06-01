"""
[DEPRECATED] 调研模板解析器 - 请使用 scanners/gp_scanner.py

保留此文件作为向后兼容的转发层。
"""

import warnings
warnings.warn(
    "template_parser.py 已废弃，请使用 scanners.gp_scanner",
    DeprecationWarning, stacklevel=2
)

from scanners.gp_scanner import GPScanner
from scanners.sample_scanner import SampleScanner
from core.models import MigrationMetadata as GPMetadata


def get_sample_metadata() -> GPMetadata:
    return SampleScanner().scan()


def parse_template_excel(filepath: str) -> GPMetadata:
    scanner = GPScanner(excel_path=filepath)
    return scanner.scan()


def get_metadata_from_template_or_sample(excel_path=None) -> GPMetadata:
    if excel_path:
        meta = parse_template_excel(excel_path)
        if meta.table_count > 0:
            return meta
    sample = get_sample_metadata()
    if excel_path:
        meta = parse_template_excel(excel_path)
        if meta.db_version:
            sample.db_version = meta.db_version or sample.db_version
            sample.cluster_scale = meta.cluster_scale or sample.cluster_scale
            sample.total_capacity = meta.total_capacity or sample.total_capacity
    return sample
