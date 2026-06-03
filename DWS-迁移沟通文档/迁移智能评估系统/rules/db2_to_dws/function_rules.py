"""DB2 -> DWS SQL函数兼容性规则

基于 DB2_DWS_迁移解决方案_证券基金资管行业_展开版 第4章
"""

FUNCTION_RULES = [
    # ================================================================
    # 空值处理
    # ================================================================
    {
        "id": "DB2-FUNC-001", "name": "VALUE() 空值处理",
        "severity": "warning", "score_deduction": 2,
        "description": "DB2 VALUE(expr, default)在DWS中对应COALESCE(expr, default)",
        "source_pattern": "VALUE(expr, default_value)",
        "target_solution": "COALESCE(expr, default_value)",
        "compatible": True, "note": "功能对等",
        "migration_difficulty": "低",
        "migration_suggestion": "全局替换 VALUE -> COALESCE"
    },
    {
        "id": "DB2-FUNC-002", "name": "COALESCE / NVL",
        "severity": "info", "score_deduction": 0,
        "description": "DB2 COALESCE在DWS中兼容",
        "source_pattern": "COALESCE(expr1, expr2, default)",
        "target_solution": "COALESCE(expr1, expr2, default) -- 兼容",
        "compatible": True, "note": "完全兼容"
    },
    {
        "id": "DB2-FUNC-003", "name": "NULLIF",
        "severity": "info", "score_deduction": 0,
        "description": "DB2 NULLIF在DWS中兼容",
        "source_pattern": "NULLIF(expr1, expr2)",
        "target_solution": "NULLIF(expr1, expr2) -- 兼容",
        "compatible": True, "note": "完全兼容"
    },
    # ================================================================
    # 条件判断
    # ================================================================
    {
        "id": "DB2-FUNC-004", "name": "DECODE() 条件判断",
        "severity": "warning", "score_deduction": 3,
        "description": "DB2 DECODE多分支在DWS中用CASE WHEN替代",
        "source_pattern": "DECODE(expr, val1, result1, val2, result2, default)",
        "target_solution": "CASE WHEN expr = val1 THEN result1 WHEN expr = val2 THEN result2 ELSE default END",
        "compatible": True,
        "note": "功能对等，语法不同。DWS也支持DECODE但建议迁移到CASE WHEN",
        "migration_difficulty": "低",
        "migration_suggestion": "DECODE -> CASE WHEN 批量转换"
    },
    {
        "id": "DB2-FUNC-005", "name": "CASE WHEN表达式",
        "severity": "info", "score_deduction": 0,
        "description": "DB2 CASE WHEN在DWS中完全兼容",
        "source_pattern": "CASE WHEN cond THEN val ELSE default END",
        "target_solution": "语法兼容",
        "compatible": True, "note": "完全兼容"
    },
    # ================================================================
    # 字符串函数
    # ================================================================
    {
        "id": "DB2-FUNC-006", "name": "字符串拼接",
        "severity": "info", "score_deduction": 0,
        "description": "DB2 || 和CONCAT在DWS中兼容",
        "source_pattern": "col1 || col2 / CONCAT(col1, col2)",
        "target_solution": "col1 || col2 / CONCAT(col1, col2) -- 兼容",
        "compatible": True, "note": "完全兼容"
    },
    {
        "id": "DB2-FUNC-007", "name": "LISTAGG",
        "severity": "warning", "score_deduction": 3,
        "description": "DB2 LISTAGG在DWS中对应STRING_AGG",
        "source_pattern": "LISTAGG(col, ',') / LISTAGG(col, ',') WITHIN GROUP(ORDER BY col)",
        "target_solution": "STRING_AGG(col, ',') / STRING_AGG(col, ',' ORDER BY col)",
        "compatible": True,
        "note": "功能对等，函数名不同。WITHIN GROUP语法也不同",
        "migration_difficulty": "低",
        "migration_suggestion": "LISTAGG(col, sep) -> STRING_AGG(col, sep)"
    },
    {
        "id": "DB2-FUNC-008", "name": "HEX() 十六进制编码",
        "severity": "warning", "score_deduction": 3,
        "description": "DB2 HEX()在DWS中对应ENCODE(..., 'hex')",
        "source_pattern": "HEX(string)",
        "target_solution": "ENCODE(string::bytea, 'hex')",
        "compatible": True, "note": "功能对等，语法不同",
        "migration_difficulty": "低",
        "migration_suggestion": "HEX(s) -> ENCODE(s::bytea, 'hex')"
    },
    {
        "id": "DB2-FUNC-009", "name": "SUBSTR / LEFT / RIGHT",
        "severity": "info", "score_deduction": 0,
        "description": "DB2 SUBSTR在DWS中兼容",
        "source_pattern": "SUBSTR(str, pos, len)",
        "target_solution": "SUBSTR(str, pos, len) -- 兼容",
        "compatible": True, "note": "完全兼容"
    },
    {
        "id": "DB2-FUNC-010", "name": "TRIM / LTRIM / RTRIM",
        "severity": "info", "score_deduction": 0,
        "description": "DB2 TRIM在DWS中兼容",
        "source_pattern": "TRIM(str) / LTRIM(str) / RTRIM(str)",
        "target_solution": "TRIM(str) / LTRIM(str) / RTRIM(str) -- 兼容",
        "compatible": True, "note": "完全兼容"
    },
    {
        "id": "DB2-FUNC-011", "name": "UPPER / LOWER",
        "severity": "info", "score_deduction": 0,
        "description": "DB2 UPPER/LOWER在DWS中兼容",
        "source_pattern": "UPPER(str) / LOWER(str)",
        "target_solution": "UPPER(str) / LOWER(str) -- 兼容",
        "compatible": True, "note": "完全兼容"
    },
    {
        "id": "DB2-FUNC-012", "name": "REPLACE",
        "severity": "info", "score_deduction": 0,
        "description": "DB2 REPLACE在DWS中兼容",
        "source_pattern": "REPLACE(str, from, to)",
        "target_solution": "REPLACE(str, from, to) -- 兼容",
        "compatible": True, "note": "完全兼容"
    },
    # ================================================================
    # 日期时间函数
    # ================================================================
    {
        "id": "DB2-FUNC-020", "name": "CURRENT DATE",
        "severity": "warning", "score_deduction": 2,
        "description": "DB2 CURRENT DATE在DWS中对应CURRENT_DATE",
        "source_pattern": "CURRENT DATE / CURRENT_DATE",
        "target_solution": "CURRENT_DATE (下划线连接)",
        "compatible": True, "note": "关键差异: DB2允许空格分隔(CURRENT DATE)，DWS要求下划线(CURRENT_DATE)",
        "migration_difficulty": "低",
        "migration_suggestion": "全局替换 CURRENT DATE -> CURRENT_DATE"
    },
    {
        "id": "DB2-FUNC-021", "name": "CURRENT TIME / CURRENT TIMESTAMP",
        "severity": "warning", "score_deduction": 2,
        "description": "DB2 CURRENT TIME/TIMESTAMP与DWS语法有差异",
        "source_pattern": "CURRENT TIME / CURRENT TIMESTAMP",
        "target_solution": "CURRENT_TIME / CURRENT_TIMESTAMP (下划线连接)",
        "compatible": True, "note": "同样为空格vs下划线差异",
        "migration_difficulty": "低",
        "migration_suggestion": "全局替换 CURRENT TIME -> CURRENT_TIME; CURRENT TIMESTAMP -> CURRENT_TIMESTAMP"
    },
    {
        "id": "DB2-FUNC-022", "name": "日期运算 (DAYS/MONTHS/YEARS)",
        "severity": "error", "score_deduction": 6,
        "description": "DB2 col + N DAYS 在DWS中需使用INTERVAL语法",
        "source_pattern": "col + 1 DAY / col - 3 MONTHS / col + 2 YEARS",
        "target_solution": "col + INTERVAL '1 day' / col - INTERVAL '3 months' / col + INTERVAL '2 years'",
        "compatible": False,
        "note": "DB2有独特的日期运算语法(+N DAYS/MONTHS/YEARS)，DWS使用标准SQL INTERVAL",
        "migration_difficulty": "中",
        "migration_suggestion": "将+N DAYS替换为+INTERVAL 'N days'，注意复数形式"
    },
    {
        "id": "DB2-FUNC-023", "name": "VARCHAR_FORMAT 日期格式化",
        "severity": "error", "score_deduction": 5,
        "description": "DB2 VARCHAR_FORMAT在DWS中对应TO_CHAR",
        "source_pattern": "VARCHAR_FORMAT(date, 'YYYY-MM-DD')",
        "target_solution": "TO_CHAR(date, 'YYYY-MM-DD')",
        "compatible": False,
        "note": "功能对等，函数名不同。格式掩码接近(DB2和DWS都使用Oracle风格格式)但需验证",
        "migration_difficulty": "低",
        "migration_suggestion": "VARCHAR_FORMAT(date, fmt) -> TO_CHAR(date, fmt)"
    },
    {
        "id": "DB2-FUNC-024", "name": "MONTHS_BETWEEN",
        "severity": "error", "score_deduction": 5,
        "description": "DB2 MONTHS_BETWEEN在DWS中无直接函数",
        "source_pattern": "MONTHS_BETWEEN(date1, date2)",
        "target_solution": "EXTRACT(YEAR FROM age(date1, date2))*12 + EXTRACT(MONTH FROM age(date1, date2))",
        "compatible": False, "note": "需要EXTRACT+age组合实现",
        "migration_difficulty": "中",
        "migration_suggestion": "使用EXTRACT(YEAR FROM age(d1,d2))*12+EXTRACT(MONTH FROM age(d1,d2))实现"
    },
    {
        "id": "DB2-FUNC-025", "name": "LAST_DAY",
        "severity": "warning", "score_deduction": 3,
        "description": "DB2 LAST_DAY在DWS中使用DATE_TRUNC+INTERVAL实现",
        "source_pattern": "LAST_DAY(date)",
        "target_solution": "(DATE_TRUNC('month', date) + INTERVAL '1 month' - INTERVAL '1 day')::DATE",
        "compatible": True,
        "note": "DWS不直接支持LAST_DAY函数，需用日期计算",
        "migration_difficulty": "中",
        "migration_suggestion": "创建自定义函数: CREATE FUNCTION last_day(d DATE) RETURNS DATE AS $$ SELECT (DATE_TRUNC('month', d) + INTERVAL '1 month' - INTERVAL '1 day')::DATE; $$ LANGUAGE sql"
    },
    {
        "id": "DB2-FUNC-026", "name": "DATE_TRUNC / TRUNC",
        "severity": "warning", "score_deduction": 2,
        "description": "DB2 TRUNC(timestamp)在DWS中对应DATE_TRUNC",
        "source_pattern": "TRUNC(timestamp, 'DD')",
        "target_solution": "DATE_TRUNC('day', timestamp)",
        "compatible": True,
        "note": "功能对等，参数顺序和函数名不同",
        "migration_difficulty": "低",
        "migration_suggestion": "TRUNC(ts, 'DD') -> DATE_TRUNC('day', ts)"
    },
    {
        "id": "DB2-FUNC-027", "name": "EXTRACT函数",
        "severity": "info", "score_deduction": 0,
        "description": "DB2 EXTRACT在DWS中兼容",
        "source_pattern": "EXTRACT(YEAR FROM date)",
        "target_solution": "EXTRACT(YEAR FROM date) -- 兼容",
        "compatible": True, "note": "完全兼容"
    },
    # ================================================================
    # 异常与错误处理函数
    # ================================================================
    {
        "id": "DB2-FUNC-030", "name": "RAISE_ERROR",
        "severity": "error", "score_deduction": 5,
        "description": "DB2 RAISE_ERROR在DWS中对应RAISE EXCEPTION",
        "source_pattern": "RAISE_ERROR('70001', 'error message')",
        "target_solution": "RAISE EXCEPTION 'error message'",
        "compatible": False,
        "note": "DB2 RAISE_ERROR需要SQLSTATE码，DWS不需要",
        "migration_difficulty": "低",
        "migration_suggestion": "RAISE_ERROR('state', 'msg') -> RAISE EXCEPTION 'msg'"
    },
    # ================================================================
    # 数学与分析函数
    # ================================================================
    {
        "id": "DB2-FUNC-040", "name": "聚合函数(SUM/AVG/COUNT/MAX/MIN)",
        "severity": "info", "score_deduction": 0,
        "description": "DB2标准聚合函数在DWS中完全兼容",
        "compatible": True, "note": "完全兼容"
    },
    {
        "id": "DB2-FUNC-041", "name": "窗口函数(ROW_NUMBER/RANK等)",
        "severity": "info", "score_deduction": 0,
        "description": "DB2窗口函数在DWS中完全兼容",
        "compatible": True, "note": "完全兼容"
    },
    {
        "id": "DB2-FUNC-042", "name": "OLAP聚合(GROUP BY ROLLUP/CUBE)",
        "severity": "info", "score_deduction": 0,
        "description": "DB2 GROUP BY ROLLUP/CUBE在DWS中兼容",
        "source_pattern": "GROUP BY ROLLUP(col1, col2) / GROUP BY CUBE(col1, col2)",
        "target_solution": "语法兼容",
        "compatible": True, "note": "完全兼容"
    },
]
