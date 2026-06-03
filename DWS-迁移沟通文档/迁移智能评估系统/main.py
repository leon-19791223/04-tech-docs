"""
迁移智能评估系统 - CLI入口
路径自动发现: 从规则注册表自动读取所有迁移路径

用法:
    python main.py --list-paths             # 列出所有可用迁移路径
    python main.py                           # 默认路径评估
    python main.py --path teradata_dws       # Teradata -> DWS
    python main.py --path oracle_dws         # Oracle -> DWS
    python main.py -t xxx-调研模板.xlsx       # 从调研模板Excel生成(GP)
    python main.py -o report.docx            # 指定输出路径
"""

import os
import sys
import argparse


def main():
    # 先导入所有规则模块触发注册
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import rules.gp_to_dws, rules.oracle_to_dws, rules.mysql_to_dws
    import rules.mssql_to_dws, rules.db2_to_dws, rules.teradata_to_dws
    from rules.registry import get_rules, get_registered_paths, list_registered

    MIGRATION_PATHS = get_registered_paths()
    PATH_KEYS = list(MIGRATION_PATHS.keys())

    parser = argparse.ArgumentParser(
        description="迁移智能评估系统 - 通用异构数据库迁移引擎",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--path", default=PATH_KEYS[0] if PATH_KEYS else "",
                        choices=PATH_KEYS,
                        help=f"迁移路径 (默认: {PATH_KEYS[0] if PATH_KEYS else '无'})")
    parser.add_argument("--list-paths", action="store_true", help="列出所有可用迁移路径")
    parser.add_argument("-t", "--template", help="调研模板Excel路径(仅GP路径支持)")
    parser.add_argument("-o", "--output", help="输出报告路径")
    parser.add_argument("-v", "--verbose", action="store_true", help="详细输出")
    parser.add_argument("--list-rules", action="store_true", help="列出已注册规则集")
    args = parser.parse_args()

    if args.list_rules:
        print("=" * 50)
        print("  已注册规则集:")
        for item in list_registered():
            print(f"    - {item}")
        return

    if args.list_paths:
        print("=" * 50)
        print("  可用迁移路径:")
        for key, cfg in sorted(MIGRATION_PATHS.items()):
            print(f"    {cfg['icon']} {cfg['label']:20s}  ({cfg.get('description','')})")
        return

    cfg = MIGRATION_PATHS[args.path]
    source = cfg["source"]
    target = cfg["target"]

    # 扫描器映射
    scanners = {
        "gp": ("scanners.gp_scanner", "GPScanner"),
        "oracle": ("scanners.oracle_scanner", "OracleScanner"),
        "mysql": ("scanners.mysql_scanner", "MySQLScanner"),
        "mssql": ("scanners.mssql_scanner", "MSSQLScanner"),
        "sqlserver": ("scanners.mssql_scanner", "MSSQLScanner"),
        "db2": ("scanners.db2_scanner", "DB2Scanner"),
        "db2_luw": ("scanners.db2_scanner", "DB2Scanner"),
        "teradata": ("scanners.teradata_scanner", "TeradataScanner"),
    }
    from scanners.sample_scanner import SampleScanner
    from core.engine import MigrationAnalyzer

    print("=" * 50)
    print(f"  {cfg['label']} 迁移智能评估")
    print("=" * 50)

    # 加载规则模块获取权重
    rules_mod_name = f"rules.{source}_to_dws" if source != "sqlserver" else "rules.mssql_to_dws"
    weights_module = __import__(rules_mod_name, fromlist=["load_weights"])
    load_weights = getattr(weights_module, "load_weights")

    # 扫描器
    template_path = args.template if args.template else None
    if template_path and not os.path.exists(template_path):
        sp = os.path.join(os.path.dirname(__file__), args.template)
        if os.path.exists(sp):
            template_path = sp
        else:
            print(f"[WARN] 未找到模板: {args.template}")
            template_path = None

    if template_path and source == "gp":
        from scanners.gp_scanner import GPScanner
        print(f"[INFO] 读取调研模板: {template_path}")
        scanner = GPScanner(excel_path=template_path)
    elif source in scanners:
        mod_path, cls_name = scanners[source]
        mod = __import__(mod_path, fromlist=[cls_name])
        scanner_cls = getattr(mod, cls_name)
        scanner = scanner_cls()
        print(f"[INFO] 使用 {source} 样本数据")
    else:
        print(f"[INFO] 使用通用样本数据")
        scanner = SampleScanner(source_type=source)

    metadata = scanner.scan()

    if args.verbose:
        print(f"[DEBUG] 源端: {metadata.db_version}")
        print(f"[DEBUG] 集群: {metadata.cluster_scale}")
        print(f"[DEBUG] 数据量: {metadata.total_capacity}")
        print(f"[DEBUG] 表/视图/函数: {metadata.table_count}/{metadata.view_count}/{metadata.function_count}")
        print()

    print(f"[INFO] 加载 {source}->{target} 规则集...")
    rules = get_rules(source, target)
    weights = load_weights()

    if args.verbose:
        total = sum(len(v) for v in rules.values())
        print(f"[DEBUG] 规则总数: {total} 条")

    print("[INFO] 执行兼容性分析...")
    analyzer = MigrationAnalyzer(
        metadata=metadata, rules=rules,
        category_weights=weights,
        source_type=source, target_type=target,
    )
    result = analyzer.analyze()

    if args.verbose:
        print(f"[DEBUG] 总分: {result.overall_score}")
        print(f"[DEBUG] 风险: {result.risk_level}")
        print(f"[DEBUG] 关键问题: {len(result.critical_issues)}")
        print()

    output_path = args.output or f"{source}_to_{target}_迁移智能评估报告.docx"
    if not os.path.isabs(output_path):
        output_path = os.path.join(os.path.dirname(__file__), output_path)

    print(f"[INFO] 生成评估报告...")
    from report_generator import ReportGenerator
    gen = ReportGenerator(result, output_path)
    final_path = gen.generate()

    print(f"[DONE] 报告已生成: {final_path}")
    print(f"  评分: {result.overall_score}/100 | 风险: {result.risk_level}")
    print(f"  规则: {sum(c.total_rules for c in result.category_results)} 条")
    print(f"  不兼容: {len(result.critical_issues)} 项")
    print(f"  工期: {result.workload_estimate.get('total_estimated_months', '—')} 人月")
    print()


if __name__ == "__main__":
    main()
