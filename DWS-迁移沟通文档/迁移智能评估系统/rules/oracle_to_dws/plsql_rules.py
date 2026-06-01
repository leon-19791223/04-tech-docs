"""Oracle -> DWS PL/SQL与函数兼容性规则

Oracle PL/SQL是迁移中最复杂的部分，涵盖:
- SQL函数差异 (NVL/DECODE等)
- PL/SQL语法差异 (游标/异常/动态SQL)
- 存储过程/函数/包
- 触发器
"""

# ================================================================
# 标准SQL函数差异
# ================================================================
FUNCTION_RULES = [
    {
        "id": "ORA-FUNC-001", "name": "NVL函数",
        "severity": "info", "score_deduction": 0,
        "description": "Oracle NVL(col, default) 与 DWS COALESCE 功能相同",
        "source_pattern": "NVL(expr, default_value)",
        "target_solution": "COALESCE(expr, default_value) 或 NVL(expr, default_value) -- DWS也支持NVL",
        "compatible": True,
        "note": "DWS兼容NVL/COALESCE，无需修改"
    },
    {
        "id": "ORA-FUNC-002", "name": "NVL2函数",
        "severity": "warning", "score_deduction": 2,
        "description": "Oracle NVL2(expr, not_null_val, null_val) 与DWS行为一致但仍需确认",
        "source_pattern": "NVL2(expr, val1, val2)",
        "target_solution": "NVL2(expr, val1, val2) -- DWS也支持NVL2",
        "compatible": True,
        "note": "DWS兼容NVL2，但参数类型推断可能有差异"
    },
    {
        "id": "ORA-FUNC-003", "name": "DECODE函数",
        "severity": "warning", "score_deduction": 2,
        "description": "Oracle DECODE(expr, s1, r1, s2, r2, default) 在DWS中支持",
        "source_pattern": "DECODE(expr, val1, result1, val2, result2, default)",
        "target_solution": "DECODE(expr, val1, result1, val2, result2, default) -- DWS兼容",
        "compatible": True,
        "note": "DWS兼容DECODE但建议逐步迁移到CASE WHEN"
    },
    {
        "id": "ORA-FUNC-004", "name": "CASE WHEN语义",
        "severity": "info", "score_deduction": 0,
        "description": "Oracle CASE WHEN在DWS中完全兼容",
        "source_pattern": "CASE WHEN condition THEN result ELSE default END",
        "target_solution": "语法兼容，无需修改",
        "compatible": True,
        "note": "完全兼容"
    },
    {
        "id": "ORA-FUNC-005", "name": "SYSDATE",
        "severity": "info", "score_deduction": 0,
        "description": "Oracle SYSDATE在DWS中使用CURRENT_TIMESTAMP或now()",
        "source_pattern": "SYSDATE",
        "target_solution": "CURRENT_TIMESTAMP 或 now() 或 SYSDATE -- DWS兼容SYSDATE别名",
        "compatible": True,
        "note": "DWS有SYSDATE内置函数，可直接使用"
    },
    {
        "id": "ORA-FUNC-006", "name": "TO_CHAR格式掩码差异",
        "severity": "warning", "score_deduction": 3,
        "description": "Oracle TO_CHAR格式掩码与DWS存在差异",
        "source_pattern": "TO_CHAR(date, 'YYYY-MM-DD HH24:MI:SS')",
        "target_solution": "TO_CHAR(date, 'YYYY-MM-DD HH24:MI:SS') -- 基本兼容但部分格式不同",
        "compatible": True,
        "note": "TO_CHAR基本格式兼容，但Oracle特有格式(如'HH:MI:SSXFF')需调整",
        "migration_difficulty": "中",
        "migration_suggestion": "对TO_CHAR中的格式掩码逐一检查，Oracle 'MON'/'MONTH'/'RR' 等格式需替换"
    },
    {
        "id": "ORA-FUNC-007", "name": "TRUNC对日期的处理",
        "severity": "info", "score_deduction": 0,
        "source_pattern": "TRUNC(date) / TRUNC(date, 'MM')",
        "target_solution": "DATE_TRUNC('month', date) / 直接trunc -- DWS兼容TRUNC",
        "compatible": True,
        "note": "DWS同时支持TRUNC和DATE_TRUNC"
    },
    {
        "id": "ORA-FUNC-008", "name": "EXTRACT函数",
        "severity": "info", "score_deduction": 0,
        "description": "Oracle EXTRACT在DWS中兼容",
        "source_pattern": "EXTRACT(YEAR FROM date)",
        "target_solution": "EXTRACT(YEAR FROM date) -- 完全兼容",
        "compatible": True,
        "note": "完全兼容"
    },
    {
        "id": "ORA-FUNC-009", "name": "ADD_MONTHS函数",
        "severity": "warning", "score_deduction": 2,
        "description": "Oracle ADD_MONTHS在DWS中行为有细微差异",
        "source_pattern": "ADD_MONTHS(date, n)",
        "target_solution": "ADD_MONTHS(date, n) -- DWS支持但月末处理逻辑不同",
        "compatible": True,
        "note": "Oracle月末日期的截断行为和DWS有差异，需验证关键业务"
    },
    {
        "id": "ORA-FUNC-010", "name": "LAST_DAY函数",
        "severity": "info", "score_deduction": 0,
        "description": "Oracle LAST_DAY在DWS中支持",
        "source_pattern": "LAST_DAY(date)",
        "target_solution": "LAST_DAY(date) -- DWS兼容",
        "compatible": True,
        "note": "兼容"
    },
    {
        "id": "ORA-FUNC-011", "name": "INSTR函数",
        "severity": "info", "score_deduction": 0,
        "description": "Oracle INSTR在DWS中兼容",
        "source_pattern": "INSTR(string, substring, position, occurrence)",
        "target_solution": "INSTR(string, substring, position, occurrence) -- DWS兼容",
        "compatible": True,
        "note": "完全兼容"
    },
    {
        "id": "ORA-FUNC-012", "name": "SUBSTR函数",
        "severity": "info", "score_deduction": 0,
        "description": "Oracle SUBSTR在DWS中兼容",
        "source_pattern": "SUBSTR(string, start, length)",
        "target_solution": "SUBSTR(string, start, length) -- DWS兼容",
        "compatible": True,
        "note": "完全兼容"
    },
    {
        "id": "ORA-FUNC-013", "name": "GREATEST/LEAST (参数类型)",
        "severity": "warning", "score_deduction": 2,
        "description": "Oracle GREATEST/LEAST在DWS中对混合类型参数处理更严格",
        "source_pattern": "GREATEST(10, '20', 30)",
        "target_solution": "GREATEST(10, 20, 30) -- 需确保参数类型一致",
        "compatible": True,
        "note": "DWS要求参数类型一致，Oracle自动做隐式类型转换"
    },
    {
        "id": "ORA-FUNC-014", "name": "CONNECT BY层级查询",
        "severity": "error", "score_deduction": 10,
        "description": "Oracle CONNECT BY层级查询在DWS中不支持",
        "source_pattern": "SELECT ... FROM t CONNECT BY PRIOR col = parent_col START WITH ...",
        "target_solution": "使用WITH RECURSIVE递归CTE替代: WITH RECURSIVE cte AS (...) SELECT ...",
        "compatible": False,
        "note": "DWS支持WITH RECURSIVE但不支持CONNECT BY语法，需改写成递归CTE",
        "migration_difficulty": "中",
        "migration_suggestion": "使用WITH RECURSIVE重写: 将CONNECT BY PRIOR映射为递归CTE中的JOIN条件"
    },
    {
        "id": "ORA-FUNC-015", "name": "MERGE INTO语法差异",
        "severity": "warning", "score_deduction": 3,
        "description": "Oracle MERGE INTO与DWS语法有差异",
        "source_pattern": "MERGE INTO target t USING source s ON (...) WHEN MATCHED THEN UPDATE ... WHEN NOT MATCHED THEN INSERT ...",
        "target_solution": "DWS支持MERGE INTO但语法不同: MERGE INTO target t USING source s ON ... WHEN MATCHED THEN UPDATE ... WHEN NOT MATCHED THEN INSERT ...",
        "compatible": True,
        "note": "基本语法兼容，但WHEN MATCHED/WHEN NOT MATCHED子句细节有差异",
        "migration_difficulty": "低",
        "migration_suggestion": "主要检查UPDATE SET和INSERT语法是否兼容"
    },
    {
        "id": "ORA-FUNC-016", "name": "多表INSERT ALL",
        "severity": "error", "score_deduction": 8,
        "description": "Oracle INSERT ALL/FIRST多表插入在DWS中不支持",
        "source_pattern": "INSERT ALL WHEN cond1 INTO t1 WHEN cond2 INTO t2 ELSE INTO t3 SELECT ...",
        "target_solution": "拆分为多条INSERT语句，或在ETL中处理",
        "compatible": False,
        "note": "DWS不支持条件多表插入",
        "migration_difficulty": "低",
        "migration_suggestion": "拆分为多条INSERT INTO ... SELECT ... WHERE ..."
    },
    {
        "id": "ORA-FUNC-017", "name": "FLASHBACK QUERY",
        "severity": "error", "score_deduction": 10,
        "description": "Oracle闪回查询(AS OF TIMESTAMP)在DWS中不支持",
        "source_pattern": "SELECT * FROM t AS OF TIMESTAMP (SYSTIMESTAMP - 1)",
        "target_solution": "DWS不支持闪回查询，需通过备份或CDC工具实现",
        "compatible": False,
        "note": "DWS没有Oracle的UNDO机制，不支持闪回",
        "migration_difficulty": "高",
        "migration_suggestion": "无需迁移该功能; 如需历史数据查询: 1) 保留历史快照表; 2) 使用CDC工具"
    },
    {
        "id": "ORA-FUNC-018", "name": "SAMPLE子句",
        "severity": "warning", "score_deduction": 3,
        "description": "Oracle SAMPLE抽样查询在DWS中语法不同",
        "source_pattern": "SELECT * FROM t SAMPLE(10)",
        "target_solution": "SELECT * FROM t TABLESAMPLE SYSTEM(10)",
        "compatible": True,
        "note": "DWS使用TABLESAMPLE语法，功能对等",
        "migration_difficulty": "低",
        "migration_suggestion": "SAMPLE(n) -> TABLESAMPLE SYSTEM(n)"
    },
    {
        "id": "ORA-FUNC-019", "name": "聚合函数兼容性",
        "severity": "info", "score_deduction": 0,
        "description": "常见聚合函数(SUM/AVG/COUNT/MAX/MIN)完全兼容",
        "compatible": True,
        "note": "完全兼容"
    },
    {
        "id": "ORA-FUNC-020", "name": "分析函数(窗口函数)",
        "severity": "info", "score_deduction": 0,
        "description": "Oracle分析函数(ROW_NUMBER/RANK/DENSE_RANK/LEAD/LAG/FIRST_VALUE等)兼容",
        "compatible": True,
        "note": "完全兼容"
    },
    {
        "id": "ORA-FUNC-021", "name": "LISTAGG函数",
        "severity": "info", "score_deduction": 0,
        "description": "Oracle LISTAGG在DWS中对应STRING_AGG",
        "source_pattern": "LISTAGG(col, ',') WITHIN GROUP (ORDER BY col)",
        "target_solution": "STRING_AGG(col, ',' ORDER BY col)",
        "compatible": True,
        "note": "功能对等，语法不同"
    },
    {
        "id": "ORA-FUNC-022", "name": "WM_CONCAT函数",
        "severity": "error", "score_deduction": 6,
        "description": "Oracle WM_CONCAT(非公开函数)在DWS中不支持",
        "source_pattern": "WM_CONCAT(col)",
        "target_solution": "STRING_AGG(col, ',')",
        "compatible": False,
        "note": "WM_CONCAT是Oracle非官方函数，DWS不支持",
        "migration_difficulty": "低",
        "migration_suggestion": "WM_CONCAT(col) -> STRING_AGG(col, ',')"
    },
]

# ================================================================
# PL/SQL语法差异
# ================================================================
PLSQL_RULES = [
    {
        "id": "ORA-PLSQL-001", "name": "包(PACKAGE)",
        "severity": "error", "score_deduction": 10,
        "description": "Oracle包(PACKAGE)将存储过程分组，DWS不支持",
        "source_pattern": "CREATE OR REPLACE PACKAGE pkg_name AS ... END; CREATE OR REPLACE PACKAGE BODY pkg_name AS ... END;",
        "target_solution": "将包内函数/过程拆分为独立schema-level函数，按包名前缀命名",
        "compatible": False,
        "note": "DWS只支持独立函数/存储过程，不支持包的封装概念",
        "migration_difficulty": "中",
        "migration_suggestion": "1) 包内变量: 改为函数参数或临时表; 2) 包内函数: 改为独立函数; 3) 命名规范: pkg_name.func_name -> pkg_name_func_name"
    },
    {
        "id": "ORA-PLSQL-002", "name": "包变量/全局变量",
        "severity": "error", "score_deduction": 8,
        "description": "Oracle包变量(全局状态)在DWS中不支持",
        "source_pattern": "CREATE PACKAGE ... g_var NUMBER; -- 包全局变量",
        "target_solution": "改为函数参数传递，或使用临时表存储会话级状态",
        "compatible": False,
        "note": "DWS没有包的概念，因此不支持包级别的全局变量",
        "migration_difficulty": "高",
        "migration_suggestion": "分析包变量的生命周期: 参数传递 / 临时表 / 应用层变量"
    },
    {
        "id": "ORA-PLSQL-003", "name": "游标FOR循环",
        "severity": "warning", "score_deduction": 3,
        "description": "Oracle游标FOR循环在plpgsql中语法不同",
        "source_pattern": "FOR rec IN (SELECT * FROM t) LOOP ... END LOOP;",
        "target_solution": "FOR rec IN (SELECT * FROM t) LOOP ... END LOOP; -- 语法兼容但行为有差异",
        "compatible": True,
        "note": "基本语法兼容，但Oracle中的隐式游标属性(SQL%ROWCOUNT等)需改写"
    },
    {
        "id": "ORA-PLSQL-004", "name": "REF CURSOR (游标变量)",
        "severity": "warning", "score_deduction": 4,
        "description": "Oracle REF CURSOR在DWS中使用游标方式不同",
        "source_pattern": "TYPE ref_cur IS REF CURSOR; OPEN cur FOR SELECT ...",
        "target_solution": "DWS使用REFCURSOR: DECLARE cur REFCURSOR; OPEN cur FOR SELECT ...",
        "compatible": True,
        "note": "DWS支持游标变量但类型声明方式不同",
        "migration_difficulty": "中",
        "migration_suggestion": "Oracle的自定义REF CURSOR类型改为DWS的REFCURSOR"
    },
    {
        "id": "ORA-PLSQL-005", "name": "异常处理语法",
        "severity": "warning", "score_deduction": 3,
        "description": "Oracle异常处理与DWS plpgsql语法有差异",
        "source_pattern": "EXCEPTION WHEN NO_DATA_FOUND THEN ... WHEN OTHERS THEN ...",
        "target_solution": "EXCEPTION WHEN NO_DATA_FOUND THEN ... WHEN OTHERS THEN ...",
        "compatible": True,
        "note": "基本语法兼容，但Oracle特有异常(如DUP_VAL_ON_INDEX)和SQLCODE需要映射",
        "migration_difficulty": "中",
        "migration_suggestion": "Oracle特有异常名改为DWS对应异常; SQLERRM->SQLERRM兼容"
    },
    {
        "id": "ORA-PLSQL-006", "name": "自治事务(PRAGMA AUTONOMOUS_TRANSACTION)",
        "severity": "error", "score_deduction": 8,
        "description": "Oracle自治事务在DWS中不支持",
        "source_pattern": "PRAGMA AUTONOMOUS_TRANSACTION; ... COMMIT;",
        "target_solution": "DWS不支持自治事务，需通过dblink或应用层实现",
        "compatible": False,
        "note": "DWS不支持在函数/过程中独立提交事务",
        "migration_difficulty": "高",
        "migration_suggestion": "1) 拆分函数，在应用层控制事务; 2) 使用dblink到自身实现"
    },
    {
        "id": "ORA-PLSQL-007", "name": "EXECUTE IMMEDIATE动态SQL",
        "severity": "warning", "score_deduction": 3,
        "description": "Oracle动态SQL在DWS中使用EXECUTE方式不同",
        "source_pattern": "EXECUTE IMMEDIATE 'SELECT ...' INTO var USING param;",
        "target_solution": "EXECUTE 'SELECT ...' INTO var USING param; -- 去掉IMMEDIATE关键字",
        "compatible": True,
        "note": "DWS使用EXECUTE代替EXECUTE IMMEDIATE，功能对等",
        "migration_difficulty": "低",
        "migration_suggestion": "全局替换 EXECUTE IMMEDIATE -> EXECUTE"
    },
    {
        "id": "ORA-PLSQL-008", "name": "BULK COLLECT批量操作",
        "severity": "warning", "score_deduction": 3,
        "description": "Oracle BULK COLLECT在plpgsql中语法不同",
        "source_pattern": "SELECT col BULK COLLECT INTO var_collect FROM t; FORALL i IN var_collect.FIRST..var_collect.LAST ...",
        "target_solution": "使用数组方式: SELECT array_agg(col) INTO var_arr FROM t; FOREACH ... LOOP",
        "compatible": True,
        "note": "DWS不再支持Oracle的BULK COLLECT/FORALL语法，需改写为数组操作",
        "migration_difficulty": "中",
        "migration_suggestion": "BULK COLLECT INTO -> 使用数组类型+array_agg; FORALL -> FOR/FOREACH循环"
    },
    {
        "id": "ORA-PLSQL-009", "name": "PLS_INTEGER数组(Associative Array)",
        "severity": "error", "score_deduction": 6,
        "description": "Oracle PL/SQL索引表(Associative Array)在DWS中不支持",
        "source_pattern": "TYPE type_name IS TABLE OF datatype INDEX BY PLS_INTEGER;",
        "target_solution": "使用DWS数组类型或临时表替代",
        "compatible": False,
        "note": "Oracle PL/SQL特有的内存集合类型，DWS不支持",
        "migration_difficulty": "中",
        "migration_suggestion": "改用DWS一维数组类型或用临时表存储键值对"
    },
    {
        "id": "ORA-PLSQL-010", "name": "记录类型(%ROWTYPE / %TYPE)",
        "severity": "warning", "score_deduction": 3,
        "description": "Oracle %ROWTYPE/%TYPE在plpgsql中对应方式不同",
        "source_pattern": "rec table_name%ROWTYPE; var table.col%TYPE;",
        "target_solution": "rec RECORD; var table.col%TYPE; -- %TYPE兼容，%ROWTYPE用RECORD替代",
        "compatible": True,
        "note": "DWS支持%TYPE但%ROWTYPE需改为RECORD类型",
        "migration_difficulty": "低",
        "migration_suggestion": "table%ROWTYPE -> RECORD; v_col table.col%TYPE 兼容"
    },
    {
        "id": "ORA-PLSQL-011", "name": "命名参数表示法",
        "severity": "info", "score_deduction": 0,
        "description": "Oracle plpgsql均支持命名参数调用",
        "compatible": True,
        "note": "兼容"
    },
    {
        "id": "ORA-PLSQL-012", "name": "DBMS_OUTPUT输出",
        "severity": "warning", "score_deduction": 2,
        "description": "Oracle DBMS_OUTPUT在DWS中使用RAISE方式",
        "source_pattern": "DBMS_OUTPUT.PUT_LINE('message');",
        "target_solution": "RAISE NOTICE 'message'; 或 RAISE INFO 'message';",
        "compatible": True,
        "note": "功能对等，语法不同",
        "migration_difficulty": "低",
        "migration_suggestion": "DBMS_OUTPUT.PUT_LINE -> RAISE NOTICE"
    },
]

# ================================================================
# 触发器
# ================================================================
TRIGGER_RULES = [
    {
        "id": "ORA-TRIG-001", "name": "行级触发器",
        "severity": "warning", "score_deduction": 3,
        "description": "Oracle行级触发器(FOR EACH ROW)在DWS中支持但语法有差异",
        "source_pattern": "CREATE OR REPLACE TRIGGER trg_name BEFORE INSERT ON table FOR EACH ROW",
        "target_solution": "CREATE TRIGGER trg_name BEFORE INSERT ON table FOR EACH ROW EXECUTE FUNCTION func_name()",
        "compatible": True,
        "note": "DWS支持行级触发器但需要定义触发器函数，且不支持BEFORE DELETE",
        "migration_difficulty": "中",
        "migration_suggestion": "将触发器逻辑拆分到触发器函数中，通过EXECUTE FUNCTION调用"
    },
    {
        "id": "ORA-TRIG-002", "name": "INSTEAD OF触发器",
        "severity": "error", "score_deduction": 8,
        "description": "Oracle INSTEAD OF触发器在DWS中不支持",
        "source_pattern": "CREATE TRIGGER trg INSTEAD OF INSERT ON view_name",
        "target_solution": "DWS不支持INSTEAD OF触发器，使用规则(RULE)替代",
        "compatible": False,
        "note": "DWS没有INSTEAD OF触发器的对等概念",
        "migration_difficulty": "高",
        "migration_suggestion": "视图改为表，通过应用层控制写入; 或使用DWS的RULE系统"
    },
    {
        "id": "ORA-TRIG-003", "name": "DDL触发器",
        "severity": "error", "score_deduction": 8,
        "description": "Oracle DDL触发器(CREATE/ALTER/DROP)在DWS中不支持",
        "source_pattern": "CREATE TRIGGER trg AFTER CREATE ON SCHEMA ...",
        "target_solution": "DWS不支持DDL触发器",
        "compatible": False,
        "note": "DDL事件监听功能在DWS中不可用",
        "migration_difficulty": "高",
        "migration_suggestion": "通过应用层或外部工具(DMS/审计)替代DDL监听"
    },
    {
        "id": "ORA-TRIG-004", "name": "复合触发器",
        "severity": "error", "score_deduction": 8,
        "description": "Oracle复合触发器(COMPOUND TRIGGER)在DWS中不支持",
        "source_pattern": "CREATE TRIGGER trg FOR INSERT ON table COMPOUND TRIGGER ...",
        "target_solution": "拆分为多个简单触发器或使用存储过程统一控制",
        "compatible": False,
        "note": "复合触发器是Oracle 11g+特性，DWS只支持简单触发器",
        "migration_difficulty": "中",
        "migration_suggestion": "将不同触发时机的逻辑拆分为多个独立触发器"
    },
]
