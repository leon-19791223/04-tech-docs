"""GP -> DWS 函数兼容性规则"""

FUNCTION_RULES = [
    {
        "id": "FUNC-001", "name": "窗口函数",
        "severity": "info", "score_deduction": 0,
        "description": "ROW_NUMBER/RANK/DENSE_RANK/LEAD/LAG/FIRST_VALUE/LAST_VALUE等",
        "compatible": True, "note": "完全兼容"
    },
    {
        "id": "FUNC-002", "name": "聚合函数",
        "severity": "info", "score_deduction": 0,
        "description": "SUM/AVG/COUNT/MAX/MIN/STRING_AGG/ARRAY_AGG等",
        "compatible": True, "note": "完全兼容"
    },
    {
        "id": "FUNC-003", "name": "NULL排序行为",
        "severity": "warning", "score_deduction": 3,
        "description": "GP默认NULLS LAST，DWS默认NULLS FIRST",
        "compatible": False,
        "note": "需在所有ORDER BY中显式指定NULLS FIRST/LAST",
        "migration_difficulty": "低",
        "migration_suggestion": "批量在ORDER BY后追加NULLS FIRST/LAST"
    },
    {
        "id": "FUNC-004", "name": "generate_series",
        "severity": "warning", "score_deduction": 3,
        "description": "GP的generate_series支持步进参数，DWS行为有差异",
        "compatible": True,
        "note": "简单使用兼容，复杂步进场景需改写"
    },
    {
        "id": "FUNC-005", "name": "字符串函数",
        "severity": "info", "score_deduction": 0,
        "description": "SUBSTR/REPLACE/CONCAT/TRIM/UPPER/LOWER等",
        "compatible": True, "note": "完全兼容"
    },
    {
        "id": "FUNC-006", "name": "日期时间函数",
        "severity": "info", "score_deduction": 0,
        "description": "DATE_TRUNC/EXTRACT/TO_CHAR/NOW/CURRENT_DATE等",
        "compatible": True, "note": "基本兼容，个别格式掩码有差异"
    },
    {
        "id": "FUNC-007", "name": "正则表达式函数",
        "severity": "warning", "score_deduction": 2,
        "description": "~ / ~* / regexp_replace / regexp_matches等",
        "compatible": True,
        "note": "基本兼容，逆向引用语法有细微差异"
    },
    {
        "id": "FUNC-008", "name": "加密哈希函数",
        "severity": "info", "score_deduction": 0,
        "description": "MD5/SHA1/SHA256/HMAC等",
        "compatible": True, "note": "完全兼容"
    },
]
