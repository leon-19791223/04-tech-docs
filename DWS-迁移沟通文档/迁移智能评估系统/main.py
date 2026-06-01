"""
GP -> DWS 迁移智能评估系统 - CLI入口

演示新架构用法:
    python main.py                           # 使用样本数据 + GP->DWS规则
    python main.py -t xxx-调研模板.xlsx       # 从调研模板Excel生成
    python main.py -o report.docx             # 指定输出路径
    python main.py --list-rules               # 查看已注册规则集
"""

import os
import sys
import argparse


def main():
    parser = argparse.ArgumentParser(
        description="迁移智能评估系统 - 通用异构数据库迁移引擎",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("-t", "--template", help="调研模板Excel路径")
    parser.add_argument("-o", "--output", help="输出报告路径")
    parser.add_argument("-v", "--verbose", action="store_true", help="详细输出")
    parser.add_argument("--list-rules", action="store_true", help="列出已注册规则集")
    args = parser.parse_args()

    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

    if args.list_rules:
        from rules.registry import list_registered
        print("=" * 50)
        print("  已注册规则集:")
        for item in list_registered():
            print(f"    - {item}")
        return

    # 使用新架构：scanner + rules.registry + core.engine
    from rules.registry import get_rules
    from rules.gp_to_dws import load_weights
    from scanners.gp_scanner import GPScanner
    from scanners.sample_scanner import SampleScanner
    from core.engine import MigrationAnalyzer
    from core.models import MigrationMetadata

    # --- 1. 采集元数据 ---
    print("=" * 50)
    print("  迁移智能评估系统")
    print("=" * 50)

    template_path = None
    if args.template:
        template_path = args.template
        if not os.path.exists(template_path):
            search_path = os.path.join(os.path.dirname(__file__), args.template)
            if os.path.exists(search_path):
                template_path = search_path
            else:
                print(f"[WARN] 未找到模板: {args.template}")
                template_path = None

    if template_path:
        print(f"[INFO] 读取调研模板: {template_path}")
        scanner = GPScanner(excel_path=template_path)
    else:
        print(f"[INFO] 使用内置样本数据")
        scanner = SampleScanner()

    metadata = scanner.scan()

    if args.verbose:
        print(f"[DEBUG] 源端: {metadata.db_version}")
        print(f"[DEBUG] 集群: {metadata.cluster_scale}")
        print(f"[DEBUG] 数据量: {metadata.total_capacity}")
        print(f"[DEBUG] 表/视图/函数: {metadata.table_count}/{metadata.view_count}/{metadata.function_count}")
        print()

    # --- 2. 加载规则集 ---
    print("[INFO] 加载 GP->DWS 规则集...")
    rules = get_rules("gp", "dws")
    weights = load_weights()

    if args.verbose:
        total = sum(len(v) for v in rules.values())
        print(f"[DEBUG] 规则总数: {total} 条")

    # --- 3. 执行分析 ---
    print("[INFO] 执行兼容性分析...")
    analyzer = MigrationAnalyzer(
        metadata=metadata,
        rules=rules,
        category_weights=weights,
        source_type="gp",
        target_type="dws",
    )
    result = analyzer.analyze()

    if args.verbose:
        print(f"[DEBUG] 总分: {result.overall_score}")
        print(f"[DEBUG] 风险: {result.risk_level}")
        print(f"[DEBUG] 关键问题: {len(result.critical_issues)}")
        print()

    # --- 4. 生成报告 ---
    output_path = args.output or "GP到DWS迁移智能评估报告.docx"
    if not os.path.isabs(output_path):
        output_path = os.path.join(os.path.dirname(__file__), output_path)

    print(f"[INFO] 生成评估报告...")
    from report_generator import ReportGenerator
    generator = ReportGenerator(result, output_path)
    final_path = generator.generate()

    print(f"[DONE] 报告已生成: {final_path}")
    print()
    print(f"  评分: {result.overall_score}/100 | 风险: {result.risk_level}")
    print(f"  规则: {sum(c.total_rules for c in result.category_results)} 条")
    print(f"  不兼容: {len(result.critical_issues)} 项")
    print(f"  工期: {result.workload_estimate.get('total_estimated_months', '—')} 人月")
    print()


if __name__ == "__main__":
    main()
