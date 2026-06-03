"""DB2 -> DWS SQL PL 存储过程兼容性规则

基于 DB2_DWS_迁移解决方案_证券基金资管行业_展开版 第5章
SQL PL (SQL Procedural Language) 到 PL/pgSQL 的转换是DB2迁移最大难点
"""

SQLPL_RULES = [
    # ================================================================
    # 基本语法结构
    # ================================================================
    {
        "id": "DB2-SPL-001", "name": "变量声明语法",
        "severity": "warning", "score_deduction": 3,
        "description": "DB2 DECLARE v TYPE DEFAULT val 在PL/pgSQL中为 v TYPE := val",
        "source_pattern": "DECLARE v_name VARCHAR(100) DEFAULT 'default';",
        "target_solution": "v_name VARCHAR(300) := 'default'; -- 注意VARCHAR长度3倍扩展",
        "compatible": True,
        "note": "DB2使用DECLARE...DEFAULT，DWS使用:=直接赋值",
        "migration_difficulty": "低",
        "migration_suggestion": "DECLARE v TYPE DEFAULT val -> v TYPE := val (移除DECLARE关键字)"
    },
    {
        "id": "DB2-SPL-002", "name": "变量赋值语法",
        "severity": "warning", "score_deduction": 2,
        "description": "DB2 SET v = value 在PL/pgSQL中为 v := value",
        "source_pattern": "SET v_variable = expression;",
        "target_solution": "v_variable := expression;",
        "compatible": True,
        "note": "DB2使用SET赋值，DWS使用:=赋值运算符",
        "migration_difficulty": "低",
        "migration_suggestion": "SET v = expr -> v := expr (存储过程体内的SET赋值)"
    },
    {
        "id": "DB2-SPL-003", "name": "IF语句语法",
        "severity": "warning", "score_deduction": 2,
        "description": "DB2 ELSEIF 在PL/pgSQL中为 ELSIF (无E)",
        "source_pattern": "IF cond1 THEN ... ELSEIF cond2 THEN ... ELSE ... END IF",
        "target_solution": "IF cond1 THEN ... ELSIF cond2 THEN ... ELSE ... END IF",
        "compatible": True,
        "note": "关键差异: DB2的ELSEIF与DWS的ELSIF(少一个E)",
        "migration_difficulty": "低",
        "migration_suggestion": "全局替换 ELSEIF -> ELSIF"
    },
    # ================================================================
    # 循环
    # ================================================================
    {
        "id": "DB2-SPL-004", "name": "FOR循环语法",
        "severity": "warning", "score_deduction": 3,
        "description": "DB2 FOR v AS cur CURSOR FOR sql DO 在PL/pgSQL中为 FOR v IN sql LOOP",
        "source_pattern": "FOR v AS cur CURSOR FOR SELECT * FROM t DO ... END FOR;",
        "target_solution": "FOR v IN SELECT * FROM t LOOP ... END LOOP;",
        "compatible": True,
        "note": "DB2的游标FOR循环使用CURSOR FOR...DO，DWS使用FOR...IN...LOOP",
        "migration_difficulty": "中",
        "migration_suggestion": "FOR v AS cur CURSOR FOR sql DO -> FOR v IN sql LOOP; END FOR -> END LOOP"
    },
    {
        "id": "DB2-SPL-005", "name": "WHILE循环语法",
        "severity": "warning", "score_deduction": 2,
        "description": "DB2 WHILE cond DO ... END WHILE 在PL/pgSQL中为 WHILE cond LOOP ... END LOOP",
        "source_pattern": "WHILE cond DO statements; END WHILE;",
        "target_solution": "WHILE cond LOOP statements; END LOOP;",
        "compatible": True,
        "note": "关键字差异: DO->LOOP, END WHILE->END LOOP",
        "migration_difficulty": "低",
        "migration_suggestion": "WHILE cond DO -> WHILE cond LOOP; END WHILE -> END LOOP"
    },
    {
        "id": "DB2-SPL-006", "name": "REPEAT/LOOP循环",
        "severity": "warning", "score_deduction": 3,
        "description": "DB2 REPEAT/LOOP循环与PL/pgSQL语法不同",
        "source_pattern": "REPEAT statements UNTIL cond END REPEAT;",
        "target_solution": "LOOP statements EXIT WHEN cond; END LOOP;",
        "compatible": True,
        "note": "DB2 REPEAT...UNTIL在DWS中需改为LOOP...EXIT WHEN",
        "migration_difficulty": "中",
        "migration_suggestion": "REPEAT...UNTIL cond -> LOOP...EXIT WHEN cond; END LOOP"
    },
    {
        "id": "DB2-SPL-007", "name": "LEAVE / ITERATE",
        "severity": "warning", "score_deduction": 3,
        "description": "DB2 LEAVE/ITERATE在DWS中对应EXIT/CONTINUE",
        "source_pattern": "LEAVE loop_label; / ITERATE loop_label;",
        "target_solution": "EXIT loop_label; / CONTINUE loop_label;",
        "compatible": True,
        "note": "LEAVE->EXIT, ITERATE->CONTINUE",
        "migration_difficulty": "低",
        "migration_suggestion": "全局替换 LEAVE -> EXIT; ITERATE -> CONTINUE"
    },
    # ================================================================
    # 异常处理
    # ================================================================
    {
        "id": "DB2-SPL-008", "name": "异常处理机制 (HANDLER vs EXCEPTION)",
        "severity": "error", "score_deduction": 8,
        "description": "DB2使用DECLARE CONTINUE/EXIT HANDLER，DWS使用BEGIN...EXCEPTION...END块",
        "source_pattern": "DECLARE CONTINUE HANDLER FOR SQLEXCEPTION BEGIN ROLLBACK; ... END;",
        "target_solution": "BEGIN ... EXCEPTION WHEN OTHERS THEN ROLLBACK; ... END;",
        "compatible": False,
        "note": "完全不同的异常处理范式。DB2的HANDLER可声明为CONTINUE或EXIT，DWS的EXCEPTION块总是退出",
        "migration_difficulty": "高",
        "migration_suggestion": "将DECLARE ... HANDLER改为BEGIN...EXCEPTION WHEN OTHERS...END; CONTINUE HANDLER改为在EXCEPTION块内处理异常后继续"
    },
    {
        "id": "DB2-SPL-009", "name": "条件声明 (CONDITION)",
        "severity": "error", "score_deduction": 6,
        "description": "DB2 DECLARE CONDITION在DWS中不支持",
        "source_pattern": "DECLARE my_cond CONDITION FOR SQLSTATE '70001';",
        "target_solution": "DWS无CONDITION概念，直接用RAISE EXCEPTION抛出异常",
        "compatible": False, "note": "DWS不支持声明自定义条件",
        "migration_difficulty": "中",
        "migration_suggestion": "移除CONDITION声明，在需要处直接使用RAISE EXCEPTION"
    },
    {
        "id": "DB2-SPL-010", "name": "信号语句 (SIGNAL)",
        "severity": "warning", "score_deduction": 3,
        "description": "DB2 SIGNAL SQLSTATE '...' SET MESSAGE_TEXT='...' 在DWS中对应RAISE EXCEPTION",
        "source_pattern": "SIGNAL SQLSTATE '70001' SET MESSAGE_TEXT = 'error occurred';",
        "target_solution": "RAISE EXCEPTION 'error occurred';",
        "compatible": True,
        "note": "功能对等，语法不同。DWS不需要SQLSTATE码",
        "migration_difficulty": "低",
        "migration_suggestion": "SIGNAL SQLSTATE 'state' SET MESSAGE_TEXT='msg' -> RAISE EXCEPTION 'msg'"
    },
    {
        "id": "DB2-SPL-011", "name": "RESIGNAL",
        "severity": "error", "score_deduction": 6,
        "description": "DB2 RESIGNAL(重新抛出异常)在DWS中不支持",
        "source_pattern": "HANDLER ... RESIGNAL; -- 重新抛出相同的异常",
        "target_solution": "在EXCEPTION块中不捕获则自动抛出; 如需重新抛出，使用RAISE",
        "compatible": False, "note": "DWS无RESIGNAL概念",
        "migration_difficulty": "中",
        "migration_suggestion": "如果需要在处理部分异常后重新抛出: 先处理, 然后RAISE"
    },
    # ================================================================
    # 游标
    # ================================================================
    {
        "id": "DB2-SPL-012", "name": "游标声明和操作",
        "severity": "warning", "score_deduction": 3,
        "description": "DB2游标声明(DECLARE CURSOR)与DWS语法有差异",
        "source_pattern": "DECLARE cur CURSOR FOR SELECT ...; OPEN cur; FETCH cur INTO var; CLOSE cur;",
        "target_solution": "DECLARE cur CURSOR FOR SELECT ...; OPEN cur; FETCH cur INTO var; CLOSE cur;",
        "compatible": True,
        "note": "基本语法兼容，但游标属性的访问方式不同(DB2: SQLSTATE, DWS: FOUND/NOT FOUND)",
        "migration_difficulty": "中",
        "migration_suggestion": "检查游标循环中的结束判断逻辑: SQLSTATE '02000' -> NOT FOUND"
    },
    {
        "id": "DB2-SPL-013", "name": "游标WITH HOLD",
        "severity": "warning", "score_deduction": 3,
        "description": "DB2游标WITH HOLD在事务提交后保持游标打开，DWS行为不同",
        "source_pattern": "DECLARE cur CURSOR WITH HOLD FOR SELECT ...",
        "target_solution": "DWS不支持WITH HOLD游标，需要在应用层重新打开游标",
        "compatible": True,
        "note": "DWS游标在事务结束后自动关闭",
        "migration_difficulty": "中",
        "migration_suggestion": "移除WITH HOLD; 如需跨事务保持，在应用层重建游标"
    },
    {
        "id": "DB2-SPL-014", "name": "游标返回 (REFCURSOR)",
        "severity": "warning", "score_deduction": 4,
        "description": "DB2存储过程返回结果集(REFCURSOR)与DWS方式不同",
        "source_pattern": "CREATE PROCEDURE get_data() DYNAMIC RESULT SETS 1 ... OPEN cur FOR SELECT ...",
        "target_solution": "CREATE FUNCTION get_data() RETURNS TABLE(...) AS $$ RETURN QUERY SELECT ...; $$ LANGUAGE plpgsql",
        "compatible": True,
        "note": "DB2使用DYNAMIC RESULT SETS+OPEN CURSOR; DWS使用RETURNS TABLE+RETURN QUERY",
        "migration_difficulty": "高",
        "migration_suggestion": "将返回结果集的存储过程改写为函数(RETURNS TABLE); 或使用REFCURSOR OUT参数"
    },
    # ================================================================
    # 动态SQL
    # ================================================================
    {
        "id": "DB2-SPL-015", "name": "动态SQL (EXECUTE IMMEDIATE)",
        "severity": "info", "score_deduction": 0,
        "description": "DB2 EXECUTE IMMEDIATE在DWS中兼容",
        "source_pattern": "EXECUTE IMMEDIATE sql_string;",
        "target_solution": "EXECUTE IMMEDIATE sql_string; -- 兼容",
        "compatible": True, "note": "完全兼容"
    },
    {
        "id": "DB2-SPL-016", "name": "PREPARE + EXECUTE",
        "severity": "warning", "score_deduction": 3,
        "description": "DB2 PREPARE+EXECUTE...USING与DWS语法差异",
        "source_pattern": "PREPARE stmt FROM 'SELECT * FROM t WHERE id=?'; EXECUTE stmt USING var;",
        "target_solution": "EXECUTE 'SELECT * FROM t WHERE id=$1' USING var;",
        "compatible": True,
        "note": "DWS的EXECUTE...USING语法更简洁，但PREPARE+EXECUTE两步方式不同",
        "migration_difficulty": "中",
        "migration_suggestion": "PREPARE+EXECUTE...USING合并为DWS的EXECUTE...USING"
    },
    # ================================================================
    # 函数/过程创建
    # ================================================================
    {
        "id": "DB2-SPL-017", "name": "存储过程创建语法",
        "severity": "warning", "score_deduction": 2,
        "description": "DB2 CREATE PROCEDURE与DWS语法有差异",
        "source_pattern": "CREATE PROCEDURE proc_name (IN p1 INT, OUT p2 VARCHAR(100)) LANGUAGE SQL ...",
        "target_solution": "CREATE OR REPLACE PROCEDURE proc_name (IN p1 INT, OUT p2 VARCHAR(300)) LANGUAGE plpgsql AS $$ ... $$",
        "compatible": True,
        "note": "主要差异: 1) LANGUAGE SQL -> LANGUAGE plpgsql; 2) 需添加$$包围; 3) VARCHAR长度调整",
        "migration_difficulty": "低",
        "migration_suggestion": "批量转换创建语法模板"
    },
    {
        "id": "DB2-SPL-018", "name": "函数创建语法",
        "severity": "warning", "score_deduction": 2,
        "description": "DB2 CREATE FUNCTION与DWS语法有差异",
        "source_pattern": "CREATE FUNCTION func_name (p1 INT) RETURNS INT LANGUAGE SQL ...",
        "target_solution": "CREATE OR REPLACE FUNCTION func_name (p1 INT) RETURNS INT LANGUAGE plpgsql AS $$ ... $$",
        "compatible": True,
        "note": "与存储过程类似的语言和体结构差异",
        "migration_difficulty": "低",
        "migration_suggestion": "批量转换函数创建语法模板"
    },
    {
        "id": "DB2-SPL-019", "name": "RETURNS TABLE 结果集",
        "severity": "warning", "score_deduction": 3,
        "description": "DB2函数返回表结果与DWS语法有差异",
        "source_pattern": "CREATE FUNCTION f() RETURNS TABLE (col1 INT, col2 VARCHAR(100))",
        "target_solution": "CREATE FUNCTION f() RETURNS TABLE (col1 INT, col2 VARCHAR(300)) LANGUAGE plpgsql AS $$ RETURN QUERY SELECT ...; $$",
        "compatible": True,
        "note": "基本兼容，注意VARCHAR长度调整。推荐使用RETURN QUERY返回结果集",
        "migration_difficulty": "低",
        "migration_suggestion": "在函数体内使用RETURN QUERY替代FOR循环+RETURN NEXT"
    },
    # ================================================================
    # 特定SQL PL功能
    # ================================================================
    {
        "id": "DB2-SPL-020", "name": "复合语句标签 (label:)",
        "severity": "info", "score_deduction": 0,
        "description": "DB2标签语法在DWS中兼容",
        "source_pattern": "label: BEGIN ... END label",
        "target_solution": "语法兼容",
        "compatible": True, "note": "完全兼容"
    },
    {
        "id": "DB2-SPL-021", "name": "GET DIAGNOSTICS",
        "severity": "warning", "score_deduction": 3,
        "description": "DB2 GET DIAGNOSTICS在DWS中语法兼容但内容不同",
        "source_pattern": "GET DIAGNOSTICS v_var = ROW_COUNT;",
        "target_solution": "GET DIAGNOSTICS v_var = ROW_COUNT; -- 兼容",
        "compatible": True,
        "note": "基本语法兼容，但DB2的诊断属性和DWS不同(DWS支持PG_EXCEPTION_DETAIL等)",
        "migration_difficulty": "中",
        "migration_suggestion": "检查使用的诊断属性名称是否在DWS中可用"
    },
    {
        "id": "DB2-SPL-022", "name": "中间结果集临时表",
        "severity": "warning", "score_deduction": 3,
        "description": "DB2 DECLARE GLOBAL TEMPORARY TABLE在DWS中使用CREATE TEMPORARY TABLE",
        "source_pattern": "DECLARE GLOBAL TEMPORARY TABLE temp_t (col INT) ON COMMIT DELETE ROWS",
        "target_solution": "CREATE TEMPORARY TABLE temp_t (col INT) ON COMMIT DELETE ROWS",
        "compatible": True,
        "note": "功能对等，语法不同。注意SESSION临时表和事务临时表的生命周期差异",
        "migration_difficulty": "低",
        "migration_suggestion": "DECLARE GLOBAL TEMPORARY TABLE -> CREATE TEMPORARY TABLE"
    },
]
