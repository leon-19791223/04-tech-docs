"""SQL Server -> DWS 函数兼容性规则"""

FUNCTION_RULES = [
    # ================================================================
    # 排序与分页
    # ================================================================
    {
        "id": "MSSQL-FUNC-001", "name": "TOP n",
        "severity": "error", "score_deduction": 5,
        "description": "SQL Server SELECT TOP n在DWS中使用LIMIT n替代",
        "source_pattern": "SELECT TOP 10 * FROM t ORDER BY col",
        "target_solution": "SELECT * FROM t ORDER BY col LIMIT 10",
        "compatible": False, "note": "语法不同: TOP放在SELECT后，LIMIT放在最后",
        "migration_difficulty": "低",
        "migration_suggestion": "SELECT [TOP n] ... -> SELECT ... LIMIT n (注意列顺序调整)"
    },
    {
        "id": "MSSQL-FUNC-002", "name": "TOP n PERCENT",
        "severity": "error", "score_deduction": 6,
        "description": "SQL Server TOP n PERCENT在DWS中无直接等效",
        "source_pattern": "SELECT TOP 10 PERCENT * FROM t",
        "target_solution": "先COUNT计算总数，再计算LIMIT值",
        "compatible": False, "note": "需要两个SQL或子查询实现",
        "migration_difficulty": "中",
        "migration_suggestion": "SELECT * FROM t LIMIT (SELECT ROUND(COUNT(*)*0.1) FROM t)"
    },
    {
        "id": "MSSQL-FUNC-003", "name": "OFFSET ... FETCH",
        "severity": "warning", "score_deduction": 2,
        "description": "SQL Server OFFSET n ROWS FETCH NEXT m ROWS ONLY在DWS中兼容",
        "source_pattern": "ORDER BY col OFFSET 10 ROWS FETCH NEXT 20 ROWS ONLY",
        "target_solution": "ORDER BY col OFFSET 10 LIMIT 20 或 ORDER BY col OFFSET 10 ROWS FETCH NEXT 20 ROWS ONLY",
        "compatible": True,
        "note": "两种语法都支持，推荐使用LIMIT/OFFSET更简洁",
        "migration_difficulty": "低",
        "migration_suggestion": "可保留FETCH语法(兼容)或改为LIMIT/OFFSET"
    },
    # ================================================================
    # 字符串函数
    # ================================================================
    {
        "id": "MSSQL-FUNC-010", "name": "CHARINDEX",
        "severity": "warning", "score_deduction": 2,
        "description": "SQL Server CHARINDEX在DWS中对应POSITION/STRPOS",
        "source_pattern": "CHARINDEX(substr, str) / CHARINDEX(substr, str, start)",
        "target_solution": "STRPOS(str, substr) 或 POSITION(substr IN str)",
        "compatible": True,
        "note": "功能对等，参数顺序不同(CHARINDEX(substr,str) vs STRPOS(str,substr))",
        "migration_difficulty": "低",
        "migration_suggestion": "CHARINDEX(s, str) -> STRPOS(str, s); 有起始位置时使用SUBSTR+STRPOS"
    },
    {
        "id": "MSSQL-FUNC-011", "name": "PATINDEX",
        "severity": "error", "score_deduction": 5,
        "description": "SQL Server PATINDEX(正则匹配位置)在DWS中无直接对应",
        "source_pattern": "PATINDEX('%pattern%', str)",
        "target_solution": "POSITION(substr IN str) 或正则 regexp_instr",
        "compatible": False,
        "note": "DWS不支持类似PATINDEX的简单模式匹配位置函数",
        "migration_difficulty": "中",
        "migration_suggestion": "简单LIKE模式: 用POSITION; 正则模式: 用regexp_matches"
    },
    {
        "id": "MSSQL-FUNC-012", "name": "LEFT/RIGHT",
        "severity": "info", "score_deduction": 0,
        "description": "SQL Server LEFT/RIGHT在DWS中兼容",
        "source_pattern": "LEFT(str, n) / RIGHT(str, n)",
        "target_solution": "LEFT(str, n) / RIGHT(str, n) -- 兼容",
        "compatible": True, "note": "完全兼容"
    },
    {
        "id": "MSSQL-FUNC-013", "name": "SUBSTRING/SUBSTR",
        "severity": "info", "score_deduction": 0,
        "description": "SQL Server SUBSTRING在DWS中兼容",
        "source_pattern": "SUBSTRING(str, start, length)",
        "target_solution": "SUBSTR(str, start, length) -- 兼容",
        "compatible": True, "note": "完全兼容"
    },
    {
        "id": "MSSQL-FUNC-014", "name": "LEN / DATALENGTH",
        "severity": "warning", "score_deduction": 2,
        "description": "SQL Server LEN(不包含尾部空格)和DATALENGTH(字节数)与DWS不同",
        "source_pattern": "LEN(str) / DATALENGTH(str)",
        "target_solution": "LENGTH(TRIM(str)) 或 OCTET_LENGTH(str)",
        "compatible": True,
        "note": "DWS的LENGTH返回字符数(含尾部空格)，需注意差异",
        "migration_difficulty": "低",
        "migration_suggestion": "LEN(str) -> LENGTH(TRIM(str, '')) 或使用CHAR_LENGTH"
    },
    {
        "id": "MSSQL-FUNC-015", "name": "REPLACE",
        "severity": "info", "score_deduction": 0,
        "description": "SQL Server REPLACE在DWS中兼容",
        "source_pattern": "REPLACE(str, old, new)",
        "target_solution": "REPLACE(str, old, new) -- 兼容",
        "compatible": True, "note": "完全兼容"
    },
    {
        "id": "MSSQL-FUNC-016", "name": "REPLICATE函数",
        "severity": "info", "score_deduction": 0,
        "description": "SQL Server REPLICATE在DWS中对应REPEAT",
        "source_pattern": "REPLICATE(str, n)",
        "target_solution": "REPEAT(str, n)",
        "compatible": True, "note": "功能对等，函数名不同",
        "migration_difficulty": "低",
        "migration_suggestion": "全局替换 REPLICATE -> REPEAT"
    },
    {
        "id": "MSSQL-FUNC-017", "name": "SPACE函数",
        "severity": "warning", "score_deduction": 2,
        "description": "SQL Server SPACE(n)在DWS中对应REPEAT(' ', n)",
        "source_pattern": "SPACE(n)",
        "target_solution": "REPEAT(' ', n)",
        "compatible": True, "note": "功能对等，语法不同",
        "migration_difficulty": "低",
        "migration_suggestion": "全局替换 SPACE(n) -> REPEAT(' ', n)"
    },
    {
        "id": "MSSQL-FUNC-018", "name": "STUFF函数",
        "severity": "error", "score_deduction": 4,
        "description": "SQL Server STUFF(字符串替换)在DWS中无直接对应",
        "source_pattern": "STUFF(str, start, length, insert_str)",
        "target_solution": "SUBSTR(str, 1, start-1) || insert_str || SUBSTR(str, start+length)",
        "compatible": False, "note": "需用SUBSTR+拼接替代",
        "migration_difficulty": "中",
        "migration_suggestion": "使用字符串拼接+SUBSTR实现STUFF功能"
    },
    {
        "id": "MSSQL-FUNC-019", "name": "REVERSE",
        "severity": "info", "score_deduction": 0,
        "description": "SQL Server REVERSE在DWS中兼容",
        "source_pattern": "REVERSE(str)",
        "target_solution": "REVERSE(str) -- 兼容",
        "compatible": True, "note": "完全兼容"
    },
    {
        "id": "MSSQL-FUNC-020", "name": "UPPER/LOWER",
        "severity": "info", "score_deduction": 0,
        "description": "SQL Server UPPER/LOWER在DWS中兼容",
        "source_pattern": "UPPER(str) / LOWER(str)",
        "target_solution": "UPPER(str) / LOWER(str) -- 兼容",
        "compatible": True, "note": "完全兼容"
    },
    {
        "id": "MSSQL-FUNC-021", "name": "LTRIM/RTRIM/TRIM",
        "severity": "info", "score_deduction": 0,
        "description": "SQL Server LTRIM/RTRIM在DWS中兼容",
        "source_pattern": "LTRIM(str) / RTRIM(str) / TRIM(str)",
        "target_solution": "LTRIM(str) / RTRIM(str) / TRIM(str) -- 兼容",
        "compatible": True, "note": "完全兼容"
    },
    {
        "id": "MSSQL-FUNC-022", "name": "CHAR(n)和ASCII函数",
        "severity": "info", "score_deduction": 0,
        "description": "SQL Server CHAR(ASCII码转字符)在DWS中兼容",
        "source_pattern": "CHAR(n) / ASCII(str)",
        "target_solution": "CHR(n) / ASCII(str) -- CHR函数名不同",
        "compatible": True, "note": "功能对等: CHAR(n) -> CHR(n)",
        "migration_difficulty": "低",
        "migration_suggestion": "全局替换 CHAR(n) -> CHR(n) (注意不替换CHAR类型定义)"
    },
    {
        "id": "MSSQL-FUNC-023", "name": "CONCAT/CONCAT_WS",
        "severity": "info", "score_deduction": 0,
        "description": "SQL Server CONCAT/CONCAT_WS在DWS中兼容",
        "source_pattern": "CONCAT(a, b) / CONCAT_WS(',', a, b)",
        "target_solution": "CONCAT(a, b) / CONCAT_WS(',', a, b) -- 兼容",
        "compatible": True, "note": "完全兼容"
    },
    {
        "id": "MSSQL-FUNC-024", "name": "STRING_AGG",
        "severity": "info", "score_deduction": 0,
        "description": "SQL Server STRING_AGG(2017+)在DWS中兼容",
        "source_pattern": "STRING_AGG(col, ',') / STRING_AGG(col, ',') WITHIN GROUP (ORDER BY col)",
        "target_solution": "STRING_AGG(col, ',') / STRING_AGG(col, ',' ORDER BY col) -- 兼容",
        "compatible": True, "note": "DWS语法更简洁(WITHIN GROUP改为直接ORDER BY)"
    },
    {
        "id": "MSSQL-FUNC-025", "name": "FORMAT函数",
        "severity": "error", "score_deduction": 5,
        "description": "SQL Server FORMAT函数(.NET格式)在DWS中不支持",
        "source_pattern": "FORMAT(date, 'yyyy-MM-dd') / FORMAT(num, 'N2')",
        "target_solution": "TO_CHAR(date, 'YYYY-MM-DD') / TO_CHAR(num, '999G999D99')",
        "compatible": False, "note": "需使用TO_CHAR重写",
        "migration_difficulty": "中",
        "migration_suggestion": "FORMAT(date,格式) -> TO_CHAR(date,格式)，注意格式掩码差异"
    },
    # ================================================================
    # 日期时间函数
    # ================================================================
    {
        "id": "MSSQL-FUNC-030", "name": "GETDATE()",
        "severity": "warning", "score_deduction": 2,
        "description": "SQL Server GETDATE()在DWS中对应CURRENT_TIMESTAMP或now()",
        "source_pattern": "GETDATE()",
        "target_solution": "now() 或 CURRENT_TIMESTAMP",
        "compatible": True, "note": "功能对等",
        "migration_difficulty": "低",
        "migration_suggestion": "全局替换 GETDATE() -> CURRENT_TIMESTAMP"
    },
    {
        "id": "MSSQL-FUNC-031", "name": "GETUTCDATE()",
        "severity": "warning", "score_deduction": 2,
        "description": "SQL Server GETUTCDATE()在DWS中对应now() AT TIME ZONE 'UTC'",
        "source_pattern": "GETUTCDATE()",
        "target_solution": "now() AT TIME ZONE 'UTC' 或 CURRENT_TIMESTAMP AT TIME ZONE 'UTC'",
        "compatible": True, "note": "功能对等",
        "migration_difficulty": "低",
        "migration_suggestion": "全局替换 GETUTCDATE() -> CURRENT_TIMESTAMP AT TIME ZONE 'UTC'"
    },
    {
        "id": "MSSQL-FUNC-032", "name": "SYSDATETIME()",
        "severity": "info", "score_deduction": 0,
        "description": "SQL Server SYSDATETIME()在DWS中对应now()",
        "source_pattern": "SYSDATETIME()",
        "target_solution": "now() 或 clock_timestamp()",
        "compatible": True, "note": "功能对等"
    },
    {
        "id": "MSSQL-FUNC-033", "name": "DATEADD",
        "severity": "warning", "score_deduction": 3,
        "description": "SQL Server DATEADD(unit, n, date)在DWS中使用+/- INTERVAL语法",
        "source_pattern": "DATEADD(day, 7, date) / DATEADD(month, -1, date)",
        "target_solution": "date + INTERVAL '7 days' / date - INTERVAL '1 month'",
        "compatible": True,
        "note": "功能对等，语法不同",
        "migration_difficulty": "低",
        "migration_suggestion": "DATEADD(unit, n, date) -> date +/- INTERVAL 'n unit'"
    },
    {
        "id": "MSSQL-FUNC-034", "name": "DATEDIFF",
        "severity": "warning", "score_deduction": 3,
        "description": "SQL Server DATEDIFF(unit, d1, d2)在DWS中使用EXTRACT或age函数",
        "source_pattern": "DATEDIFF(day, date1, date2)",
        "target_solution": "EXTRACT(DAY FROM date2 - date1) -- 注意: DWS日期相减直接得到天数",
        "compatible": True,
        "note": "DWS日期相减返回天数(date2-date1)，类似DATEDIFF(day,d1,d2)",
        "migration_difficulty": "中",
        "migration_suggestion": "DATEDIFF(day, d1, d2) -> EXTRACT(DAY FROM d2 - d1); 月/年用age函数"
    },
    {
        "id": "MSSQL-FUNC-035", "name": "DATEPART",
        "severity": "warning", "score_deduction": 2,
        "description": "SQL Server DATEPART(unit, date)在DWS中使用EXTRACT",
        "source_pattern": "DATEPART(year, date) / DATEPART(month, date)",
        "target_solution": "EXTRACT(YEAR FROM date) / EXTRACT(MONTH FROM date)",
        "compatible": True, "note": "功能对等",
        "migration_difficulty": "低",
        "migration_suggestion": "DATEPART(unit, date) -> EXTRACT(unit FROM date)"
    },
    {
        "id": "MSSQL-FUNC-036", "name": "DATENAME",
        "severity": "warning", "score_deduction": 2,
        "description": "SQL Server DATENAME在DWS中使用TO_CHAR",
        "source_pattern": "DATENAME(month, date) / DATENAME(weekday, date)",
        "target_solution": "TO_CHAR(date, 'Month') / TO_CHAR(date, 'Day')",
        "compatible": True, "note": "功能对等",
        "migration_difficulty": "低",
        "migration_suggestion": "DATENAME(month,date) -> TO_CHAR(date, 'Month')"
    },
    {
        "id": "MSSQL-FUNC-037", "name": "YEAR/MONTH/DAY简写函数",
        "severity": "warning", "score_deduction": 2,
        "description": "SQL Server YEAR/MONTH/DAY(date)在DWS中使用EXTRACT",
        "source_pattern": "YEAR(date) / MONTH(date) / DAY(date)",
        "target_solution": "EXTRACT(YEAR FROM date) / EXTRACT(MONTH FROM date) / EXTRACT(DAY FROM date)",
        "compatible": True, "note": "DWS不支持这些简写函数",
        "migration_difficulty": "低",
        "migration_suggestion": "全局替换 YEAR(date) -> EXTRACT(YEAR FROM date)"
    },
    {
        "id": "MSSQL-FUNC-038", "name": "EOMONTH",
        "severity": "warning", "score_deduction": 3,
        "description": "SQL Server EOMONTH(date)在DWS中使用DATE_TRUNC+INTERVAL",
        "source_pattern": "EOMONTH(date) / EOMONTH(date, offset)",
        "target_solution": "DATE_TRUNC('month', date) + INTERVAL '1 month' - INTERVAL '1 day'",
        "compatible": True, "note": "功能对等，需用日期计算实现",
        "migration_difficulty": "中",
        "migration_suggestion": "EOMONTH(date) -> (DATE_TRUNC('month', date) + INTERVAL '1 month' - INTERVAL '1 day')::DATE"
    },
    {
        "id": "MSSQL-FUNC-039", "name": "ISDATE函数",
        "severity": "warning", "score_deduction": 3,
        "description": "SQL Server ISDATE在DWS中无直接对应",
        "source_pattern": "ISDATE(expr)",
        "target_solution": "使用CASE WHEN TO_DATE(expr, 'YYYY-MM-DD') IS NOT NULL 或正则匹配",
        "compatible": True, "note": "需用TRY-CATCH或正则实现",
        "migration_difficulty": "中",
        "migration_suggestion": "使用TO_DATE(expr, 'YYYY-MM-DD') IS NOT NULL做验证"
    },
    # ================================================================
    # 条件与类型转换
    # ================================================================
    {
        "id": "MSSQL-FUNC-040", "name": "ISNULL函数",
        "severity": "warning", "score_deduction": 2,
        "description": "SQL Server ISNULL(expr, default)在DWS中对应COALESCE或NVL",
        "source_pattern": "ISNULL(expr, default)",
        "target_solution": "COALESCE(expr, default) 或 NVL(expr, default)",
        "compatible": True, "note": "功能对等",
        "migration_difficulty": "低",
        "migration_suggestion": "全局替换 ISNULL -> COALESCE (注意ISNULL只接受2参，COALESCE可接受多参)"
    },
    {
        "id": "MSSQL-FUNC-041", "name": "NULLIF",
        "severity": "info", "score_deduction": 0,
        "description": "SQL Server NULLIF在DWS中兼容",
        "source_pattern": "NULLIF(expr1, expr2)",
        "target_solution": "NULLIF(expr1, expr2) -- 兼容",
        "compatible": True, "note": "完全兼容"
    },
    {
        "id": "MSSQL-FUNC-042", "name": "COALESCE",
        "severity": "info", "score_deduction": 0,
        "description": "SQL Server COALESCE在DWS中兼容",
        "source_pattern": "COALESCE(val1, val2, ...)",
        "target_solution": "COALESCE(val1, val2, ...) -- 兼容",
        "compatible": True, "note": "完全兼容"
    },
    {
        "id": "MSSQL-FUNC-043", "name": "IIF函数",
        "severity": "error", "score_deduction": 4,
        "description": "SQL Server IIF(条件,真,假)在DWS中不支持",
        "source_pattern": "IIF(condition, true_val, false_val)",
        "target_solution": "CASE WHEN condition THEN true_val ELSE false_val END",
        "compatible": False, "note": "需改为CASE WHEN",
        "migration_difficulty": "低",
        "migration_suggestion": "全局替换 IIF(cond, t, f) -> CASE WHEN cond THEN t ELSE f END"
    },
    {
        "id": "MSSQL-FUNC-044", "name": "CHOOSE函数",
        "severity": "error", "score_deduction": 4,
        "description": "SQL Server CHOOSE(index, val1, val2, ...)在DWS中不支持",
        "source_pattern": "CHOOSE(2, 'A', 'B', 'C')",
        "target_solution": "CASE index WHEN 1 THEN 'A' WHEN 2 THEN 'B' WHEN 3 THEN 'C' END",
        "compatible": False, "note": "需改为CASE WHEN",
        "migration_difficulty": "低",
        "migration_suggestion": "CHOOSE -> CASE WHEN 语句"
    },
    {
        "id": "MSSQL-FUNC-045", "name": "CAST/CONVERT",
        "severity": "warning", "score_deduction": 2,
        "description": "SQL Server CAST在DWS中兼容，CONVERT(style)需处理",
        "source_pattern": "CAST(expr AS type) / CONVERT(type, expr, style)",
        "target_solution": "CAST(expr AS type) -- 兼容; 移除CONVERT的style参数",
        "compatible": True,
        "note": "CAST兼容; CONVERT的style参数(如日期格式121)需移除或改写",
        "migration_difficulty": "低",
        "migration_suggestion": "CONVERT(type, expr, style) -> CAST(expr AS type) 或 TO_CHAR"
    },
    {
        "id": "MSSQL-FUNC-046", "name": "TRY_CAST / TRY_CONVERT",
        "severity": "error", "score_deduction": 5,
        "description": "SQL Server TRY_CAST/TRY_CONVERT在DWS中不支持",
        "source_pattern": "TRY_CAST(expr AS type)",
        "target_solution": "使用CASE WHEN + 正则验证，或自定义函数实现",
        "compatible": False, "note": "DWS无安全类型转换函数",
        "migration_difficulty": "中",
        "migration_suggestion": "自定义函数: CREATE FUNCTION try_cast_int(p TEXT) RETURNS INT AS $$ BEGIN RETURN p::INT; EXCEPTION WHEN OTHERS THEN RETURN NULL; END $$ LANGUAGE plpgsql"
    },
    {
        "id": "MSSQL-FUNC-047", "name": "CASE WHEN",
        "severity": "info", "score_deduction": 0,
        "description": "SQL Server CASE WHEN在DWS中完全兼容",
        "source_pattern": "CASE WHEN condition THEN result ELSE default END",
        "target_solution": "语法兼容",
        "compatible": True, "note": "完全兼容"
    },
    # ================================================================
    # 聚合与窗口函数
    # ================================================================
    {
        "id": "MSSQL-FUNC-050", "name": "SUM/AVG/COUNT/MAX/MIN",
        "severity": "info", "score_deduction": 0,
        "description": "SQL Server标准聚合函数在DWS中完全兼容",
        "compatible": True, "note": "完全兼容"
    },
    {
        "id": "MSSQL-FUNC-051", "name": "窗口函数(ROW_NUMBER/RANK等)",
        "severity": "info", "score_deduction": 0,
        "description": "SQL Server窗口函数在DWS中完全兼容",
        "compatible": True, "note": "完全兼容"
    },
    {
        "id": "MSSQL-FUNC-052", "name": "PIVOT/UNPIVOT",
        "severity": "error", "score_deduction": 6,
        "description": "SQL Server PIVOT/UNPIVOT在DWS中不支持",
        "source_pattern": "SELECT ... FROM t PIVOT (SUM(val) FOR col IN ([A],[B],[C])) AS pvt",
        "target_solution": "使用CASE WHEN + 聚合函数: SUM(CASE WHEN col='A' THEN val END)",
        "compatible": False, "note": "需手动展开PIVOT为条件聚合",
        "migration_difficulty": "中",
        "migration_suggestion": "PIVOT替换为: SELECT col1, SUM(CASE WHEN pivot_col='A' THEN val END) AS A, ... GROUP BY col1"
    },
    {
        "id": "MSSQL-FUNC-053", "name": "STDEV/STDEVP/VAR/VARP",
        "severity": "info", "score_deduction": 0,
        "description": "SQL Server统计聚合函数在DWS中兼容",
        "source_pattern": "STDEV(col) / VAR(col)",
        "target_solution": "STDDEV(col) / VARIANCE(col) -- 函数名略有不同",
        "compatible": True, "note": "功能对等，函数名稍有差异",
        "migration_difficulty": "低",
        "migration_suggestion": "STDEV -> STDDEV_SAMP; STDEVP -> STDDEV_POP"
    },
    # ================================================================
    # 数学函数
    # ================================================================
    {
        "id": "MSSQL-FUNC-060", "name": "ABS/CEIL/FLOOR",
        "severity": "info", "score_deduction": 0,
        "description": "SQL Server ABS/CEIL/FLOOR在DWS中兼容",
        "compatible": True, "note": "完全兼容"
    },
    {
        "id": "MSSQL-FUNC-061", "name": "ROUND(截断模式)",
        "severity": "warning", "score_deduction": 2,
        "description": "SQL Server ROUND支持截断模式(3参fFunction)，DWS不直接支持",
        "source_pattern": "ROUND(val, 2, 1) -- 1=截断",
        "target_solution": "TRUNC(val, 2) 或 ROUND(val, 2) -- DWS使用TRUNC做截断",
        "compatible": True, "note": "功能对等，语法不同",
        "migration_difficulty": "低",
        "migration_suggestion": "ROUND(val, precision, 1) -> TRUNC(val, precision)"
    },
    {
        "id": "MSSQL-FUNC-062", "name": "RAND随机数",
        "severity": "warning", "score_deduction": 2,
        "description": "SQL Server RAND()在DWS中对应RANDOM()",
        "source_pattern": "RAND() / RAND(seed)",
        "target_solution": "RANDOM() -- 不带种子参数",
        "compatible": True, "note": "功能对等，函数名不同",
        "migration_difficulty": "低",
        "migration_suggestion": "RAND() -> RANDOM(); 带种子: SETSEED(n); SELECT RANDOM()"
    },
    {
        "id": "MSSQL-FUNC-063", "name": "GREATEST/LEAST",
        "severity": "info", "score_deduction": 0,
        "description": "SQL Server IIF/嵌套CASE实现G/L，DWS原生支持GREATEST/LEAST",
        "source_pattern": "CASE WHEN a > b THEN a ELSE b END",
        "target_solution": "GREATEST(a, b) -- 更简洁",
        "compatible": True, "note": "DWS支持GREATEST/LEAST，可简化SQL"
    },
    # ================================================================
    # 系统函数
    # ================================================================
    {
        "id": "MSSQL-FUNC-070", "name": "NEWID() / NEWSEQUENTIALID()",
        "severity": "warning", "score_deduction": 2,
        "description": "SQL Server NEWID()在DWS中对应UUID_GENERATE_V4()",
        "source_pattern": "NEWID() / NEWSEQUENTIALID()",
        "target_solution": "UUID_GENERATE_V4()",
        "compatible": True,
        "note": "功能对等，函数名不同(需uuid-ossp扩展)",
        "migration_difficulty": "低",
        "migration_suggestion": "NEWID() -> UUID_GENERATE_V4(); NEWSEQUENTIALID() -> UUID_GENERATE_V4()"
    },
    {
        "id": "MSSQL-FUNC-071", "name": "SCOPE_IDENTITY / @@IDENTITY",
        "severity": "error", "score_deduction": 5,
        "description": "SQL Server SCOPE_IDENTITY()在DWS中使用CURRVAL或RETURNING",
        "source_pattern": "SCOPE_IDENTITY() / @@IDENTITY",
        "target_solution": "CURRVAL('seq_name') 或 INSERT ... RETURNING id",
        "compatible": False, "note": "DWS使用SEQUENCE方式",
        "migration_difficulty": "低",
        "migration_suggestion": "INSERT INTO t VALUES (...) RETURNING id INTO var; 或 CURRVAL('seq_name')"
    },
    {
        "id": "MSSQL-FUNC-072", "name": "@@ROWCOUNT",
        "severity": "error", "score_deduction": 4,
        "description": "SQL Server @@ROWCOUNT在DWS中使用GET DIAGNOSTICS",
        "source_pattern": "DELETE FROM t; SELECT @@ROWCOUNT",
        "target_solution": "GET DIAGNOSTICS row_count = ROW_COUNT;",
        "compatible": False, "note": "语法完全不同",
        "migration_difficulty": "中",
        "migration_suggestion": "在plpgsql中使用GET DIAGNOSTICS替代@@ROWCOUNT"
    },
    {
        "id": "MSSQL-FUNC-073", "name": "@@ERROR / ERROR_MESSAGE",
        "severity": "error", "score_deduction": 5,
        "description": "SQL Server @@ERROR/ERROR_MESSAGE在DWS中使用GET STACKED DIAGNOSTICS",
        "source_pattern": "@@ERROR / ERROR_MESSAGE()",
        "target_solution": "GET STACKED DIAGNOSTICS var = PG_EXCEPTION_DETAIL;",
        "compatible": False, "note": "异常处理机制差异大",
        "migration_difficulty": "高",
        "migration_suggestion": "重写异常处理为DWS plpgsql风格: EXCEPTION WHEN OTHERS THEN GET STACKED DIAGNOSTICS ..."
    },
    {
        "id": "MSSQL-FUNC-074", "name": "HASHBYTES",
        "severity": "warning", "score_deduction": 2,
        "description": "SQL Server HASHBYTES('MD5', str)在DWS中使用MD5/SHA2直接函数",
        "source_pattern": "HASHBYTES('MD5', str) / HASHBYTES('SHA2_256', str)",
        "target_solution": "MD5(str) / SHA256(str)",
        "compatible": True, "note": "功能对等",
        "migration_difficulty": "低",
        "migration_suggestion": "HASHBYTES('MD5', str) -> MD5(str); HASHBYTES('SHA2_256', str) -> SHA256(str)"
    },
    {
        "id": "MSSQL-FUNC-075", "name": "CHECKSUM / BINARY_CHECKSUM",
        "severity": "error", "score_deduction": 4,
        "description": "SQL Server CHECKSUM函数在DWS中无直接对应",
        "source_pattern": "CHECKSUM(col1, col2)",
        "target_solution": "可以使用HASH函数: MD5(col1 || '-' || col2) 作为替代",
        "compatible": False, "note": "DWS无哈希校验和函数",
        "migration_difficulty": "低",
        "migration_suggestion": "CHECKSUM -> MD5或自定义哈希函数"
    },
    {
        "id": "MSSQL-FUNC-076", "name": "OBJECT_ID / OBJECT_NAME",
        "severity": "error", "score_deduction": 5,
        "description": "SQL Server元数据函数在DWS中通过系统视图查询",
        "source_pattern": "OBJECT_ID('table') / OBJECT_NAME(obj_id)",
        "target_solution": "SELECT oid FROM pg_class WHERE relname='table' / SELECT relname FROM pg_class WHERE oid=id",
        "compatible": False, "note": "DWS使用PG系统表",
        "migration_difficulty": "低",
        "migration_suggestion": "OBJECT_ID('t') -> (SELECT oid FROM pg_class WHERE relname='t')"
    },
    {
        "id": "MSSQL-FUNC-077", "name": "NULL排序行为",
        "severity": "warning", "score_deduction": 3,
        "description": "SQL Server默认NULL最小(升序排最前)，DWS默认NULL最大(升序排最后)",
        "source_pattern": "ORDER BY col (SQL Server: NULLS FIRST默认)",
        "target_solution": "ORDER BY col NULLS FIRST/LAST -- 显式指定排序规则",
        "compatible": False, "note": "NULL排序行为相反，必须在ORDER BY中显式指定",
        "migration_difficulty": "低",
        "migration_suggestion": "在所有ORDER BY后追加NULLS LAST或NULLS FIRST以保证行为一致"
    },
    # ================================================================
    # T-SQL特有
    # ================================================================
    {
        "id": "MSSQL-FUNC-080", "name": "WAITFOR DELAY",
        "severity": "error", "score_deduction": 4,
        "description": "SQL Server WAITFOR DELAY在DWS中不支持",
        "source_pattern": "WAITFOR DELAY '00:00:05' / WAITFOR TIME '10:00:00'",
        "target_solution": "使用pg_sleep(5)替代; 不支持定时等待",
        "compatible": False, "note": "DWS有pg_sleep()但没有WAITFOR TIME",
        "migration_difficulty": "低",
        "migration_suggestion": "WAITFOR DELAY 'hh:mm:ss' -> PERFORM pg_sleep(seconds)"
    },
    {
        "id": "MSSQL-FUNC-081", "name": "RAISERROR / THROW",
        "severity": "warning", "score_deduction": 3,
        "description": "SQL Server RAISERROR/THROW在DWS中对应RAISE",
        "source_pattern": "RAISERROR('msg', 16, 1) / THROW 50001, 'msg', 1",
        "target_solution": "RAISE EXCEPTION 'msg' 或 RAISE NOTICE 'msg'",
        "compatible": True, "note": "功能对等，语法不同",
        "migration_difficulty": "中",
        "migration_suggestion": "RAISERROR('msg', severity, state) -> RAISE EXCEPTION 'msg' (DWS无严重级别概念)"
    },
]
