"""MySQL -> DWS 函数兼容性规则"""

FUNCTION_RULES = [
    # ================================================================
    # 字符串函数
    # ================================================================
    {
        "id": "MYSQL-FUNC-001", "name": "GROUP_CONCAT",
        "severity": "error", "score_deduction": 6,
        "description": "MySQL GROUP_CONCAT在DWS中使用STRING_AGG替代",
        "source_pattern": "GROUP_CONCAT(col ORDER BY col SEPARATOR ',')",
        "target_solution": "STRING_AGG(col, ',' ORDER BY col)",
        "compatible": False, "note": "功能对等，语法不同",
        "migration_difficulty": "低",
        "migration_suggestion": "全局替换 GROUP_CONCAT -> STRING_AGG"
    },
    {
        "id": "MYSQL-FUNC-002", "name": "CONCAT函数",
        "severity": "info", "score_deduction": 0,
        "description": "MySQL CONCAT在DWS中兼容",
        "source_pattern": "CONCAT(str1, str2)",
        "target_solution": "CONCAT(str1, str2) -- 兼容",
        "compatible": True, "note": "完全兼容"
    },
    {
        "id": "MYSQL-FUNC-003", "name": "CONCAT_WS函数",
        "severity": "info", "score_deduction": 0,
        "description": "MySQL CONCAT_WS在DWS中兼容",
        "source_pattern": "CONCAT_WS(',', str1, str2)",
        "target_solution": "CONCAT_WS(',', str1, str2) -- 兼容",
        "compatible": True, "note": "完全兼容"
    },
    {
        "id": "MYSQL-FUNC-004", "name": "LEFT/RIGHT",
        "severity": "info", "score_deduction": 0,
        "description": "MySQL LEFT/RIGHT在DWS中兼容",
        "source_pattern": "LEFT(str, n) / RIGHT(str, n)",
        "target_solution": "LEFT(str, n) / RIGHT(str, n) -- 兼容",
        "compatible": True, "note": "完全兼容"
    },
    {
        "id": "MYSQL-FUNC-005", "name": "SUBSTRING/SUBSTR",
        "severity": "info", "score_deduction": 0,
        "description": "MySQL SUBSTRING/SUBSTR在DWS中兼容",
        "source_pattern": "SUBSTRING(str FROM pos FOR len)",
        "target_solution": "SUBSTR(str, pos, len) -- 兼容",
        "compatible": True, "note": "完全兼容"
    },
    {
        "id": "MYSQL-FUNC-006", "name": "SUBSTRING_INDEX",
        "severity": "warning", "score_deduction": 3,
        "description": "MySQL SUBSTRING_INDEX在DWS中无直接对应函数",
        "source_pattern": "SUBSTRING_INDEX(str, '.', 2)",
        "target_solution": "使用SPLIT_PART(str, '.', 1) || '.' || SPLIT_PART(str, '.', 2)",
        "compatible": True, "note": "需用SPLIT_PART组合实现",
        "migration_difficulty": "中",
        "migration_suggestion": "SPLIT_PART + 字符串拼接替代 SUBSTRING_INDEX"
    },
    {
        "id": "MYSQL-FUNC-007", "name": "FIND_IN_SET",
        "severity": "error", "score_deduction": 5,
        "description": "MySQL FIND_IN_SET在DWS中不支持",
        "source_pattern": "FIND_IN_SET('val', col)",
        "target_solution": "POSITION(',val,' IN ',' || col || ',') > 0",
        "compatible": False, "note": "需用字符串处理替代",
        "migration_difficulty": "中",
        "migration_suggestion": "用POSITION/CASE WHEN组合实现; 或拆分关联表"
    },
    {
        "id": "MYSQL-FUNC-008", "name": "INSTR/LOCATE",
        "severity": "warning", "score_deduction": 2,
        "description": "MySQL INSTR/LOCATE在DWS中对应POSITION/STRPOS",
        "source_pattern": "INSTR(str, substr) / LOCATE(substr, str)",
        "target_solution": "POSITION(substr IN str) 或 STRPOS(str, substr)",
        "compatible": True,
        "note": "功能对等，参数顺序可能不同(LOCATE参数顺序与DWS不同)",
        "migration_difficulty": "低",
        "migration_suggestion": "INSTR(str,substr) -> STRPOS(str,substr); LOCATE(substr,str) -> POSITION(substr IN str)"
    },
    {
        "id": "MYSQL-FUNC-009", "name": "LPAD/RPAD",
        "severity": "info", "score_deduction": 0,
        "description": "MySQL LPAD/RPAD在DWS中兼容",
        "source_pattern": "LPAD(str, n, pad) / RPAD(str, n, pad)",
        "target_solution": "LPAD(str, n, pad) / RPAD(str, n, pad) -- 兼容",
        "compatible": True, "note": "完全兼容"
    },
    {
        "id": "MYSQL-FUNC-010", "name": "REPEAT函数",
        "severity": "info", "score_deduction": 0,
        "description": "MySQL REPEAT在DWS中兼容",
        "source_pattern": "REPEAT(str, n)",
        "target_solution": "REPEAT(str, n) -- 兼容",
        "compatible": True, "note": "完全兼容"
    },
    {
        "id": "MYSQL-FUNC-011", "name": "REPLACE函数",
        "severity": "info", "score_deduction": 0,
        "description": "MySQL REPLACE在DWS中兼容",
        "source_pattern": "REPLACE(str, from, to)",
        "target_solution": "REPLACE(str, from, to) -- 兼容",
        "compatible": True, "note": "完全兼容"
    },
    {
        "id": "MYSQL-FUNC-012", "name": "REVERSE函数",
        "severity": "info", "score_deduction": 0,
        "description": "MySQL REVERSE在DWS中兼容",
        "source_pattern": "REVERSE(str)",
        "target_solution": "REVERSE(str) -- 兼容",
        "compatible": True, "note": "完全兼容"
    },
    {
        "id": "MYSQL-FUNC-013", "name": "TRIM/LTRIM/RTRIM",
        "severity": "info", "score_deduction": 0,
        "description": "MySQL TRIM/LTRIM/RTRIM在DWS中兼容",
        "source_pattern": "TRIM(str) / LTRIM(str) / RTRIM(str)",
        "target_solution": "TRIM(str) / LTRIM(str) / RTRIM(str) -- 兼容",
        "compatible": True, "note": "完全兼容"
    },
    {
        "id": "MYSQL-FUNC-014", "name": "UPPER/LOWER",
        "severity": "info", "score_deduction": 0,
        "description": "MySQL UPPER/LOWER在DWS中兼容",
        "source_pattern": "UPPER(str) / LOWER(str)",
        "target_solution": "UPPER(str) / LOWER(str) -- 兼容",
        "compatible": True, "note": "完全兼容"
    },
    {
        "id": "MYSQL-FUNC-015", "name": "CHAR_LENGTH/CHARACTER_LENGTH",
        "severity": "info", "score_deduction": 0,
        "description": "MySQL CHAR_LENGTH在DWS中兼容",
        "source_pattern": "CHAR_LENGTH(str)",
        "target_solution": "CHAR_LENGTH(str) 或 LENGTH(str) -- 注意DWS LENGTH返回字节数",
        "compatible": True, "note": "DWS中CHAR_LENGTH返回字符数，与MySQL一致"
    },
    {
        "id": "MYSQL-FUNC-016", "name": "ELT/FIELD函数",
        "severity": "error", "score_deduction": 4,
        "description": "MySQL ELT/FIELD在DWS中不支持",
        "source_pattern": "ELT(n, str1, str2, ...) / FIELD(str, val1, val2, ...)",
        "target_solution": "使用CASE WHEN替代",
        "compatible": False, "note": "需用CASE WHEN重写",
        "migration_difficulty": "低",
        "migration_suggestion": "ELT -> CASE n WHEN 1 THEN str1 WHEN 2 THEN str2; FIELD -> CASE str WHEN val1 THEN 1 WHEN val2 THEN 2"
    },
    # ================================================================
    # 日期时间函数
    # ================================================================
    {
        "id": "MYSQL-FUNC-020", "name": "NOW() / CURRENT_TIMESTAMP",
        "severity": "info", "score_deduction": 0,
        "description": "MySQL NOW()在DWS中对应CURRENT_TIMESTAMP或now()",
        "source_pattern": "NOW()",
        "target_solution": "now() 或 CURRENT_TIMESTAMP -- 兼容",
        "compatible": True, "note": "完全兼容"
    },
    {
        "id": "MYSQL-FUNC-021", "name": "SYSDATE()",
        "severity": "info", "score_deduction": 0,
        "description": "MySQL SYSDATE()在DWS中对应clock_timestamp()",
        "source_pattern": "SYSDATE()",
        "target_solution": "clock_timestamp() -- 注意: MySQL SYSDATE返回执行时间，now()返回事务开始时间",
        "compatible": True,
        "note": "DWS有clock_timestamp()函数功能对等; 若接受事务时间可直接用now()"
    },
    {
        "id": "MYSQL-FUNC-022", "name": "CURDATE() / CURRENT_DATE",
        "severity": "info", "score_deduction": 0,
        "description": "MySQL CURDATE()在DWS中对应CURRENT_DATE",
        "source_pattern": "CURDATE()",
        "target_solution": "CURRENT_DATE -- 兼容",
        "compatible": True, "note": "完全兼容"
    },
    {
        "id": "MYSQL-FUNC-023", "name": "DATE_FORMAT",
        "severity": "error", "score_deduction": 6,
        "description": "MySQL DATE_FORMAT在DWS中需改为TO_CHAR",
        "source_pattern": "DATE_FORMAT(date, '%Y-%m-%d %H:%i:%s')",
        "target_solution": "TO_CHAR(date, 'YYYY-MM-DD HH24:MI:SS')",
        "compatible": False,
        "note": "格式掩码完全不同，需全局转换",
        "migration_difficulty": "中",
        "migration_suggestion": "编写格式转换映射: %Y->YYYY, %m->MM, %d->DD, %H->HH24, %i->MI, %s->SS"
    },
    {
        "id": "MYSQL-FUNC-024", "name": "STR_TO_DATE",
        "severity": "warning", "score_deduction": 3,
        "description": "MySQL STR_TO_DATE在DWS中对应TO_TIMESTAMP/TO_DATE",
        "source_pattern": "STR_TO_DATE(str, '%Y-%m-%d')",
        "target_solution": "TO_DATE(str, 'YYYY-MM-DD') 或 TO_TIMESTAMP(str, 'YYYY-MM-DD')",
        "compatible": True,
        "note": "功能对等，格式掩码不同",
        "migration_difficulty": "低",
        "migration_suggestion": "STR_TO_DATE -> TO_DATE/TO_TIMESTAMP，转换格式掩码"
    },
    {
        "id": "MYSQL-FUNC-025", "name": "DATE_ADD / DATE_SUB",
        "severity": "warning", "score_deduction": 3,
        "description": "MySQL DATE_ADD/DATE_SUB在DWS中使用+/- INTERVAL语法",
        "source_pattern": "DATE_ADD(date, INTERVAL 1 DAY) / DATE_SUB(date, INTERVAL 1 MONTH)",
        "target_solution": "date + INTERVAL '1 day' / date - INTERVAL '1 month'",
        "compatible": True,
        "note": "功能对等，语法不同",
        "migration_difficulty": "低",
        "migration_suggestion": "全局替换 DATE_ADD(date, INTERVAL n UNIT) -> date + INTERVAL 'n unit'"
    },
    {
        "id": "MYSQL-FUNC-026", "name": "DATEDIFF",
        "severity": "warning", "score_deduction": 2,
        "description": "MySQL DATEDIFF在DWS中对应EXTRACT或直接相减",
        "source_pattern": "DATEDIFF(date1, date2)",
        "target_solution": "EXTRACT(DAY FROM date1 - date2) 或 (date1 - date2)  -- 注意参数顺序",
        "compatible": True,
        "note": "功能对等但参数顺序：MySQL DATEDIFF(date1,date2)=date1-date2",
        "migration_difficulty": "低",
        "migration_suggestion": "DATEDIFF(d1,d2) -> EXTRACT(DAY FROM d1 - d2)"
    },
    {
        "id": "MYSQL-FUNC-027", "name": "TIMESTAMPDIFF",
        "severity": "warning", "score_deduction": 3,
        "description": "MySQL TIMESTAMPDIFF在DWS中需用EXTRACT或age函数",
        "source_pattern": "TIMESTAMPDIFF(MONTH, date1, date2)",
        "target_solution": "EXTRACT(YEAR FROM age(date2, date1))*12 + EXTRACT(MONTH FROM age(date2, date1))",
        "compatible": True,
        "note": "计算两个日期时间差，DWS没有直接对等函数",
        "migration_difficulty": "中",
        "migration_suggestion": "使用EXTRACT + age()函数组合实现"
    },
    {
        "id": "MYSQL-FUNC-028", "name": "UNIX_TIMESTAMP",
        "severity": "warning", "score_deduction": 2,
        "description": "MySQL UNIX_TIMESTAMP在DWS中对应EXTRACT(EPOCH FROM ...)",
        "source_pattern": "UNIX_TIMESTAMP(date)",
        "target_solution": "EXTRACT(EPOCH FROM date)::BIGINT",
        "compatible": True,
        "note": "功能对等，语法不同; 无参数调用返回当前时间戳",
        "migration_difficulty": "低",
        "migration_suggestion": "UNIX_TIMESTAMP(date) -> EXTRACT(EPOCH FROM date)::BIGINT"
    },
    {
        "id": "MYSQL-FUNC-029", "name": "FROM_UNIXTIME",
        "severity": "warning", "score_deduction": 2,
        "description": "MySQL FROM_UNIXTIME在DWS中对应TO_TIMESTAMP",
        "source_pattern": "FROM_UNIXTIME(ts, '%Y-%m-%d')",
        "target_solution": "TO_TIMESTAMP(ts)::DATE 或 TO_CHAR(TO_TIMESTAMP(ts), 'YYYY-MM-DD')",
        "compatible": True,
        "note": "功能对等",
        "migration_difficulty": "低",
        "migration_suggestion": "FROM_UNIXTIME(ts) -> TO_TIMESTAMP(ts)"
    },
    {
        "id": "MYSQL-FUNC-030", "name": "LAST_DAY",
        "severity": "info", "score_deduction": 0,
        "description": "MySQL LAST_DAY在DWS中兼容",
        "source_pattern": "LAST_DAY(date)",
        "target_solution": "LAST_DAY(date) -- 兼容",
        "compatible": True, "note": "完全兼容"
    },
    {
        "id": "MYSQL-FUNC-031", "name": "EXTRACT函数",
        "severity": "info", "score_deduction": 0,
        "description": "MySQL EXTRACT在DWS中兼容",
        "source_pattern": "EXTRACT(YEAR FROM date)",
        "target_solution": "EXTRACT(YEAR FROM date) -- 兼容",
        "compatible": True, "note": "完全兼容"
    },
    {
        "id": "MYSQL-FUNC-032", "name": "WEEK/MONTH/YEAR/DAY等简写函数",
        "severity": "warning", "score_deduction": 2,
        "description": "MySQL YEAR(date)/MONTH(date)/DAY(date)在DWS中需使用EXTRACT",
        "source_pattern": "YEAR(date) / MONTH(date) / DAY(date)",
        "target_solution": "EXTRACT(YEAR FROM date) / EXTRACT(MONTH FROM date) / EXTRACT(DAY FROM date)",
        "compatible": True, "note": "DWS不支持YEAR/MONTH/DAY简写函数",
        "migration_difficulty": "低",
        "migration_suggestion": "全局替换 YEAR(date) -> EXTRACT(YEAR FROM date)"
    },
    {
        "id": "MYSQL-FUNC-033", "name": "DATE/DAYOFMONTH/HOUR等提取函数",
        "severity": "warning", "score_deduction": 2,
        "description": "MySQL HOUR/MINUTE/SECOND/MICROSECOND在DWS中需使用EXTRACT",
        "source_pattern": "HOUR(date) / MINUTE(date) / SECOND(date)",
        "target_solution": "EXTRACT(HOUR FROM date) / EXTRACT(MINUTE FROM date) / EXTRACT(SECOND FROM date)",
        "compatible": True, "note": "DWS不支持这些简写函数",
        "migration_difficulty": "低",
        "migration_suggestion": "全局替换为EXTRACT"
    },
    {
        "id": "MYSQL-FUNC-034", "name": "DATE_ADD(date, INTERVAL) 替代语法",
        "severity": "warning", "score_deduction": 2,
        "description": "MySQL date + INTERVAL n unit 在DWS中语法兼容但需微调",
        "source_pattern": "date + INTERVAL 1 DAY / date - INTERVAL 1 MONTH",
        "target_solution": "date + INTERVAL '1 day' / date - INTERVAL '1 month' (注意引号)",
        "compatible": True,
        "note": "DWS要求INTERVAL后面的值使用引号: INTERVAL 'n unit'",
        "migration_difficulty": "低",
        "migration_suggestion": "全局替换 INTERVAL n -> INTERVAL 'n'"
    },
    # ================================================================
    # 条件与流程控制
    # ================================================================
    {
        "id": "MYSQL-FUNC-040", "name": "IF函数(三目)",
        "severity": "error", "score_deduction": 4,
        "description": "MySQL IF(expr, val1, val2)在DWS中需改为CASE WHEN",
        "source_pattern": "IF(condition, val_true, val_false)",
        "target_solution": "CASE WHEN condition THEN val_true ELSE val_false END",
        "compatible": False, "note": "DWS不支持IF()三目函数(但支持IF语句)",
        "migration_difficulty": "低",
        "migration_suggestion": "全局替换 IF(条件, 真值, 假值) -> CASE WHEN 条件 THEN 真值 ELSE 假值 END"
    },
    {
        "id": "MYSQL-FUNC-041", "name": "IFNULL函数",
        "severity": "warning", "score_deduction": 2,
        "description": "MySQL IFNULL在DWS中对应COALESCE或NVL",
        "source_pattern": "IFNULL(expr, default)",
        "target_solution": "COALESCE(expr, default) 或 NVL(expr, default)",
        "compatible": True, "note": "DWS支持NVL和COALESCE",
        "migration_difficulty": "低",
        "migration_suggestion": "全局替换 IFNULL -> COALESCE 或 NVL"
    },
    {
        "id": "MYSQL-FUNC-042", "name": "NULLIF函数",
        "severity": "info", "score_deduction": 0,
        "description": "MySQL NULLIF在DWS中兼容",
        "source_pattern": "NULLIF(expr1, expr2)",
        "target_solution": "NULLIF(expr1, expr2) -- 兼容",
        "compatible": True, "note": "完全兼容"
    },
    {
        "id": "MYSQL-FUNC-043", "name": "CASE WHEN表达式",
        "severity": "info", "score_deduction": 0,
        "description": "MySQL CASE WHEN在DWS中完全兼容",
        "source_pattern": "CASE WHEN condition THEN result ELSE default END",
        "target_solution": "语法兼容",
        "compatible": True, "note": "完全兼容"
    },
    {
        "id": "MYSQL-FUNC-044", "name": "COALESCE函数",
        "severity": "info", "score_deduction": 0,
        "description": "MySQL COALESCE在DWS中兼容",
        "source_pattern": "COALESCE(val1, val2, default)",
        "target_solution": "COALESCE(val1, val2, default) -- 兼容",
        "compatible": True, "note": "完全兼容"
    },
    # ================================================================
    # 数学函数
    # ================================================================
    {
        "id": "MYSQL-FUNC-050", "name": "RAND()随机数",
        "severity": "warning", "score_deduction": 2,
        "description": "MySQL RAND()在DWS中对应RANDOM()",
        "source_pattern": "RAND() / RAND(n)",
        "target_solution": "RANDOM() -- 注意: DWS RANDOM返回[0,1)，不带种子参数",
        "compatible": True, "note": "功能对等，函数名不同",
        "migration_difficulty": "低",
        "migration_suggestion": "全局替换 RAND() -> RANDOM(); RAND(n) -> SETSEED(n); SELECT RANDOM()"
    },
    {
        "id": "MYSQL-FUNC-051", "name": "ROUND/CEIL/FLOOR",
        "severity": "info", "score_deduction": 0,
        "description": "MySQL ROUND/CEIL/FLOOR在DWS中兼容",
        "source_pattern": "ROUND(x, d) / CEIL(x) / FLOOR(x)",
        "target_solution": "ROUND(x, d) / CEIL(x) / FLOOR(x) -- 兼容",
        "compatible": True, "note": "完全兼容"
    },
    {
        "id": "MYSQL-FUNC-052", "name": "ABS/POW/SQRT/MOD",
        "severity": "info", "score_deduction": 0,
        "description": "MySQL ABS/POW/SQRT/MOD在DWS中兼容",
        "source_pattern": "ABS(x) / POW(x,y) / SQRT(x) / MOD(x,y)",
        "target_solution": "ABS(x) / POW(x,y) / SQRT(x) / MOD(x,y) -- 兼容",
        "compatible": True, "note": "完全兼容"
    },
    {
        "id": "MYSQL-FUNC-053", "name": "GREATEST/LEAST",
        "severity": "warning", "score_deduction": 2,
        "description": "MySQL GREATEST/LEAST支持混合类型参数，DWS要求类型一致",
        "source_pattern": "GREATEST(10, '20', 30)",
        "target_solution": "GREATEST(10, 20, 30) -- 需确保参数类型一致",
        "compatible": True, "note": "DWS要求参数类型统一",
        "migration_difficulty": "低",
        "migration_suggestion": "确保参数类型一致，或添加类型转换"
    },
    # ================================================================
    # 聚合与窗口函数
    # ================================================================
    {
        "id": "MYSQL-FUNC-060", "name": "SUM/AVG/COUNT/MAX/MIN",
        "severity": "info", "score_deduction": 0,
        "description": "MySQL标准聚合函数在DWS中完全兼容",
        "compatible": True, "note": "完全兼容"
    },
    {
        "id": "MYSQL-FUNC-061", "name": "窗口函数(ROW_NUMBER/RANK等)",
        "severity": "info", "score_deduction": 0,
        "description": "MySQL窗口函数在DWS中完全兼容",
        "compatible": True, "note": "完全兼容"
    },
    {
        "id": "MYSQL-FUNC-062", "name": "BIT_AND/BIT_OR/BIT_XOR聚合",
        "severity": "error", "score_deduction": 4,
        "description": "MySQL位聚合函数在DWS中不支持",
        "source_pattern": "BIT_AND(col) / BIT_OR(col) / BIT_XOR(col)",
        "target_solution": "使用自定义聚合或应用层处理",
        "compatible": False, "note": "DWS不支持位聚合函数",
        "migration_difficulty": "中",
        "migration_suggestion": "使用自定义聚合函数(plpgsql)实现"
    },
    # ================================================================
    # 其他函数
    # ================================================================
    {
        "id": "MYSQL-FUNC-070", "name": "MD5/SHA1/SHA2加密函数",
        "severity": "info", "score_deduction": 0,
        "description": "MySQL MD5/SHA1/SHA2在DWS中兼容",
        "source_pattern": "MD5(str) / SHA1(str) / SHA2(str, 256)",
        "target_solution": "MD5(str) / SHA1(str) / SHA256(str) -- 兼容",
        "compatible": True, "note": "完全兼容"
    },
    {
        "id": "MYSQL-FUNC-071", "name": "UUID函数",
        "severity": "warning", "score_deduction": 2,
        "description": "MySQL UUID()在DWS中对应UUID_GENERATE_V4()",
        "source_pattern": "UUID()",
        "target_solution": "UUID_GENERATE_V4()",
        "compatible": True, "note": "需要uuid-ossp扩展",
        "migration_difficulty": "低",
        "migration_suggestion": "全局替换 UUID() -> UUID_GENERATE_V4()，确保已安装uuid-ossp扩展"
    },
    {
        "id": "MYSQL-FUNC-072", "name": "CAST类型转换",
        "severity": "info", "score_deduction": 0,
        "description": "MySQL CAST在DWS中兼容",
        "source_pattern": "CAST(expr AS type)",
        "target_solution": "CAST(expr AS type) -- 兼容",
        "compatible": True, "note": "完全兼容，注意DWS ::运算符也可用"
    },
    {
        "id": "MYSQL-FUNC-073", "name": "IF(expr, val1, val2) 与 IFNULL区别",
        "severity": "warning", "score_deduction": 2,
        "description": "注意区分 IF 三目函数与 IFNULL，DWS都不支持这两个函数名",
        "compatible": True,
        "note": "IF -> CASE WHEN; IFNULL -> COALESCE/NVL"
    },
    {
        "id": "MYSQL-FUNC-074", "name": "JSON函数",
        "severity": "warning", "score_deduction": 3,
        "description": "MySQL JSON_EXTRACT/JSON_UNQUOTE等与DWS JSON函数名不同",
        "source_pattern": "JSON_EXTRACT(col, '$.key') / JSON_UNQUOTE(JSON_EXTRACT(col, '$.key'))",
        "target_solution": "col -> 'key' (jsonb操作符) / col #>> '{key}'",
        "compatible": True,
        "note": "DWS使用PostgreSQL风格JSON操作符(->, ->>, #>, #>>)",
        "migration_difficulty": "中",
        "migration_suggestion": "JSON_EXTRACT -> ->; JSON_UNQUOTE(JSON_EXTRACT) -> ->>"
    },
    {
        "id": "MYSQL-FUNC-075", "name": "ANY_VALUE函数",
        "severity": "error", "score_deduction": 4,
        "description": "MySQL ANY_VALUE在DWS中不支持",
        "source_pattern": "ANY_VALUE(col)",
        "target_solution": "使用MIN/MAX替代，或保证GROUP BY包含所有SELECT列",
        "compatible": False, "note": "DWS要求GROUP BY列必须在SELECT中",
        "migration_difficulty": "低",
        "migration_suggestion": "ANY_VALUE(col) -> MIN(col) 或 MAX(col)"
    },
]
