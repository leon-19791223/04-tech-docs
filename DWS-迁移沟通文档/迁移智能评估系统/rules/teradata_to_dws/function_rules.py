"""Teradata -> DWS 函数与操作符兼容性规则
从 DWS 9.1.0 Hybrid产品文档中31行对比表提炼
包含: 字符串/数值/日期/条件函数 + TD特有函数
"""

FUNCTION_RULES = [
    # ================================================================
    # NULL 处理
    # ================================================================
    {
        "id": "TD-FUNC-001", "name": "NULL拼接行为",
        "severity": "warning", "score_deduction": 3,
        "description": "Teradata模式: 'abc'||null 返回 null; (DWS-PG模式: 返回 'abc')",
        "source_pattern": "'abc' || null_column",
        "target_solution": "设置GUC: behavior_compat_options='strict_text_concat_td'; 或使用 COALESCE(null_column, '')",
        "compatible": True,
        "note": "DWS TD兼容模式下可通过GUC参数控制为Teradata行为",
        "migration_difficulty": "低",
        "migration_suggestion": "开启GUC strict_text_concat_td; 或改SQL: 'abc'||COALESCE(col,'')"
    },
    {
        "id": "TD-FUNC-002", "name": "NULL排序",
        "severity": "warning", "score_deduction": 3,
        "description": "Teradata: NULL排序视NULL为最小值; DWS默认NULLS LAST",
        "source_pattern": "ORDER BY col (Teradata默认NULL最小)",
        "target_solution": "显式指定: ORDER BY col NULLS FIRST (TD兼容); 或 ORDER BY col NULLS LAST (DWS默认)",
        "compatible": True,
        "note": "DWS支持NULLS FIRST/NULLS LAST语法，建议显式指定",
        "migration_difficulty": "低",
        "migration_suggestion": "在所有ORDER BY中追加NULLS FIRST或NULLS LAST"
    },
    {
        "id": "TD-FUNC-003", "name": "NULL + 数值运算",
        "severity": "warning", "score_deduction": 2,
        "description": "Teradata: NULL参与数值运算返回NULL; DWS行为相同",
        "source_pattern": "NULL + 1 (返回NULL)",
        "target_solution": "使用COALESCE: COALESCE(col, 0) + 1",
        "compatible": True,
        "note": "行为一致，但TD中NULL+0=0需开启GUC"
    },

    # ================================================================
    # 字符串函数
    # ================================================================
    {
        "id": "TD-FUNC-004", "name": "SUBSTR(s,0) 行为",
        "severity": "warning", "score_deduction": 2,
        "description": "Teradata: SUBSTR(s,0,n) 从第0位取前n字符 (等同Oracle行为)",
        "source_pattern": "SUBSTR(str, 0, n)",
        "target_solution": "DWS TD模式兼容: 行为与TD一致; DWS普通模式: 需改为 SUBSTR(str, 1, n)",
        "compatible": True,
        "note": "DBCOMPATIBILITY 'TD' 模式下行为与TD一致，无需修改",
        "migration_difficulty": "低",
        "migration_suggestion": "确保数据库在TD兼容模式下运行; 或全局替换SUBSTR(x,0,n)->SUBSTR(x,1,n)"
    },
    {
        "id": "TD-FUNC-005", "name": "SUBSTRING(s from 0)",
        "severity": "warning", "score_deduction": 2,
        "description": "Teradata: SUBSTRING(s FROM 0 FOR n) 从前0位取n-1字符",
        "source_pattern": "SUBSTRING(str FROM 0 FOR n)",
        "target_solution": "SUBSTRING(str FROM 1 FOR n) 或确保TD兼容模式",
        "compatible": True,
        "note": "TD模式下行为兼容"
    },
    {
        "id": "TD-FUNC-006", "name": "TRIM函数差异",
        "severity": "info", "score_deduction": 0,
        "description": "Teradata/DWS均支持TRIM/LTRIM/RTRIM，语法基本兼容",
        "compatible": True,
        "note": "兼容"
    },
    {
        "id": "TD-FUNC-007", "name": "LPAD/RPAD填充函数",
        "severity": "warning", "score_deduction": 2,
        "description": "Teradata: LPAD/RPAD fill字段为空字符串时返回原字符串; DWS普通模式返回空",
        "source_pattern": "LPAD(str, 10, '')",
        "target_solution": "TD模式兼容: fill为空字符串时返回原字符串",
        "compatible": True,
        "note": "GUC behavior_compat_options 控制具体行为"
    },

    # ================================================================
    # 数值函数
    # ================================================================
    {
        "id": "TD-FUNC-008", "name": "MOD(x, 0) 除零处理",
        "severity": "warning", "score_deduction": 2,
        "description": "Teradata: MOD(x, 0) 返回 x; DWS普通模式返回 NULL",
        "source_pattern": "MOD(value, 0)",
        "target_solution": "DWS TD兼容模式下也返回x",
        "compatible": True,
        "note": "TD模式下行为一致"
    },
    {
        "id": "TD-FUNC-009", "name": "LOG函数底数",
        "severity": "info", "score_deduction": 0,
        "description": "Teradata: LOG(x) 以10为底; DWS: LOG(x) 以10为底",
        "compatible": True,
        "note": "兼容"
    },

    # ================================================================
    # 日期时间函数
    # ================================================================
    {
        "id": "TD-FUNC-010", "name": "DATE转TIMESTAMP",
        "severity": "warning", "score_deduction": 2,
        "description": "Teradata: DATE类型转为TIMESTAMP时时间部分为00:00:00; DWS TD模式相同",
        "source_pattern": "CAST(date_col AS TIMESTAMP)",
        "target_solution": "DWS TD模式行为一致; 如需要可用 date_col::TIMESTAMP",
        "compatible": True,
        "note": "TD模式下兼容"
    },
    {
        "id": "TD-FUNC-011", "name": "CURRENT_DATE格式",
        "severity": "warning", "score_deduction": 2,
        "description": "Teradata: CURRENT_DATE 返回 TIMESTAMP(0) 并带时区; DWS返回DATE",
        "source_pattern": "CURRENT_DATE",
        "target_solution": "改为 CURRENT_TIMESTAMP 或 now() 获取完整时间",
        "compatible": True,
        "note": "TD模式下CURRENT_DATE返回格式为'YYYY/MM/DD'(受GUC影响)",
        "migration_difficulty": "低",
        "migration_suggestion": "根据SQL上下文: 需要时间用CURRENT_TIMESTAMP, 仅日期用CURRENT_DATE"
    },
    {
        "id": "TD-FUNC-012", "name": "TO_DATE空串处理",
        "severity": "warning", "score_deduction": 3,
        "description": "Teradata: TO_DATE('') 返回 NULL; DWS普通模式可能报错",
        "source_pattern": "TO_DATE('', 'YYYY-MM-DD')",
        "target_solution": "DWS TD模式下: TO_DATE('')返回NULL; 通用做法: NULLIF(str,'')::DATE",
        "compatible": True,
        "note": "可通过GUC convert_empty_str_to_null_td 控制",
        "migration_difficulty": "低"
    },
    {
        "id": "TD-FUNC-013", "name": "字符串转时间戳",
        "severity": "warning", "score_deduction": 2,
        "description": "Teradata: 隐式字符串转时间戳格式宽松; DWS较严格",
        "source_pattern": "CAST('2024-01-01' AS TIMESTAMP)",
        "target_solution": "显式使用 TO_TIMESTAMP('2024-01-01', 'YYYY-MM-DD')",
        "compatible": True,
        "note": "建议显式指定格式"
    },

    # ================================================================
    # Teradata特有函数
    # ================================================================
    {
        "id": "TD-FUNC-014", "name": "Teradata QUALIFY子句",
        "severity": "error",
        "score_deduction": 10,
        "description": "Teradata QUALIFY子句在DWS中不支持",
        "source_pattern": "SELECT col, ROW_NUMBER() OVER(PARTITION BY ... ORDER BY ...) AS rn FROM t QUALIFY rn = 1",
        "target_solution": "使用子查询+WHERE: SELECT * FROM (SELECT col, ROW_NUMBER() OVER(...) AS rn FROM t) WHERE rn = 1",
        "compatible": False,
        "note": "QUALIFY是Teradata特有语法，需改写为子查询",
        "migration_difficulty": "低",
        "migration_suggestion": "将QUALIFY条件移到外层WHERE: SELECT * FROM (SELECT ..., ROW_NUMBER() OVER(...) AS rn FROM t) sub WHERE sub.rn = 1"
    },
    {
        "id": "TD-FUNC-015", "name": "Teradata GROUP BY 列序号",
        "severity": "error",
        "score_deduction": 6,
        "description": "Teradata支持GROUP BY 1,2,3 (列序号); DWS不支持",
        "source_pattern": "SELECT col1, col2, SUM(col3) FROM t GROUP BY 1, 2",
        "target_solution": "改为显式列名: SELECT col1, col2, SUM(col3) FROM t GROUP BY col1, col2",
        "compatible": False,
        "note": "DWS要求GROUP BY使用列名或表达式",
        "migration_difficulty": "低",
        "migration_suggestion": "全局将 GROUP BY 数字 替换为对应列名"
    },
    {
        "id": "TD-FUNC-016", "name": "Teradata GROUP BY 列别名",
        "severity": "error",
        "score_deduction": 6,
        "description": "Teradata允许GROUP BY中使用列别名; DWS部分版本不支持",
        "source_pattern": "SELECT col1 AS c FROM t GROUP BY c",
        "target_solution": "改为原始列名或完整表达式: SELECT col1 AS c FROM t GROUP BY col1",
        "compatible": False,
        "note": "DWS 9.x已支持GROUP BY别名",
        "migration_difficulty": "低",
        "migration_suggestion": "如DWS版本不支持，替换为原始列名"
    },
    {
        "id": "TD-FUNC-017", "name": "Teradata RANGE_N/CASE_N 表达式",
        "severity": "error",
        "score_deduction": 8,
        "description": "Teradata RANGE_N分区表达式在DWS中不支持",
        "source_pattern": "RANGE_N(transaction_date BETWEEN DATE '2024-01-01' AND '2024-12-31' EACH INTERVAL '1' MONTH)",
        "target_solution": "改写为DWS标准RANGE分区语法",
        "compatible": False,
        "note": "DWS不支持RANGE_N/CASE_N分区表达式",
        "migration_difficulty": "中",
        "migration_suggestion": "手动将RANGE_N映射为RANGE分区列表"
    },
    {
        "id": "TD-FUNC-018", "name": "Teradata RESET WHEN (OLAP)",
        "severity": "error",
        "score_deduction": 8,
        "description": "Teradata OLAP函数的RESET WHEN子句在DWS中不支持",
        "source_pattern": "SUM(col) OVER(PARTITION BY ... ORDER BY ... RESET WHEN condition)",
        "target_solution": "使用CASE WHEN + 嵌套窗口函数替代",
        "compatible": False,
        "note": "Teradata特有的窗口函数累积重置功能",
        "migration_difficulty": "高",
        "migration_suggestion": "使用CASE WHEN区分重置条件，配合SUM(...) OVER(...)实现"
    },

    # ================================================================
    # 类型转换
    # ================================================================
    {
        "id": "TD-FUNC-019", "name": "隐式字符串转数值",
        "severity": "info",
        "score_deduction": 0,
        "description": "Teradata/DWS均支持隐式字符串转数值",
        "compatible": True,
        "note": "兼容"
    },
    {
        "id": "TD-FUNC-020", "name": "COALESCE类型统一",
        "severity": "warning",
        "score_deduction": 2,
        "description": "COALESCE中参数类型不一致时，Teradata和DWS行为有差异",
        "source_pattern": "COALESCE(int_col, varchar_col)",
        "target_solution": "确保COALESCE中所有参数类型一致",
        "compatible": True,
        "note": "建议使用显式CAST统一类型"
    },
]
