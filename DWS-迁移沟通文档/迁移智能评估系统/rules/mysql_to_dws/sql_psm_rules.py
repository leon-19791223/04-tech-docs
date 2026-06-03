"""MySQL 存储过程(SQL/PSM)兼容性规则"""
SQL_PSM_RULES = [
    {
        "id": "MYSQL-SQLPSM-001", "name": "存储过程创建语法",
        "severity": "warning", "score_deduction": 3,
        "description": "MySQL CREATE PROCEDURE与DWS PL/pgSQL语法有差异",
        "source_pattern": "CREATE PROCEDURE proc_name (IN p1 INT) LANGUAGE SQL BEGIN ... END",
        "target_solution": "CREATE OR REPLACE FUNCTION proc_name (p1 INT) RETURNS ... LANGUAGE plpgsql AS $$ ... $$",
        "compatible": True,
        "note": "MySQL使用BEGIN...END块，DWS使用AS $$...$$; MySQL可使用DELIMITER，DWS不需要",
        "migration_difficulty": "中",
        "migration_suggestion": "将存储过程改写为DWS函数: 1)移除DELIMITER; 2) LANGUAGE SQL->plpgsql; 3) 体包装到$$内"
    },
    {
        "id": "MYSQL-SQLPSM-002", "name": "函数创建语法",
        "severity": "warning", "score_deduction": 2,
        "description": "MySQL CREATE FUNCTION与DWS语法有差异",
        "source_pattern": "CREATE FUNCTION func_name(p1 INT) RETURNS INT DETERMINISTIC BEGIN ... END",
        "target_solution": "CREATE OR REPLACE FUNCTION func_name(p1 INT) RETURNS INT LANGUAGE plpgsql AS $$ ... $$",
        "compatible": True,
        "note": "MySQL的DETERMINISTIC/READS SQL DATA等特性描述在DWS中无对应",
        "migration_difficulty": "低",
        "migration_suggestion": "移除DETERMINISTIC等修饰词，体包装到$$内"
    },
    {
        "id": "MYSQL-SQLPSM-003", "name": "变量声明语法",
        "severity": "warning", "score_deduction": 2,
        "description": "MySQL DECLARE var TYPE [DEFAULT val]在PL/pgSQL中使用 := 赋值",
        "source_pattern": "DECLARE v_name VARCHAR(100) DEFAULT 'default';",
        "target_solution": "v_name VARCHAR(300) := 'default'; (注意VARCHAR长度3倍扩展)",
        "compatible": True,
        "note": "MySQL使用DECLARE在BEGIN后，DWS在DECLARE段声明",
        "migration_difficulty": "低",
        "migration_suggestion": "DECLARE v TYPE DEFAULT val -> v TYPE := val"
    },
    {
        "id": "MYSQL-SQLPSM-004", "name": "IF语句语法",
        "severity": "info", "score_deduction": 0,
        "description": "MySQL IF...THEN...ELSEIF...ELSE...END IF在DWS中兼容",
        "compatible": True, "note": "完全兼容"
    },
    {
        "id": "MYSQL-SQLPSM-005", "name": "游标处理差异",
        "severity": "warning", "score_deduction": 3,
        "description": "MySQL游标(DECLARE CURSOR)与DWS PL/pgSQL游标语法有差异",
        "source_pattern": "DECLARE cur CURSOR FOR SELECT ...; OPEN cur; FETCH cur INTO var; CLOSE cur;",
        "target_solution": "DECLARE cur CURSOR FOR SELECT ...; OPEN cur; FETCH cur INTO var; CLOSE cur;",
        "compatible": True,
        "note": "基本语法兼容，但MySQL的游标声明必须在HANDLER之前，DWS无此限制",
        "migration_difficulty": "中",
        "migration_suggestion": "游标循环改为FOR...IN...LOOP简化写法或保持DECLARE CURSOR"
    },
    {
        "id": "MYSQL-SQLPSM-006", "name": "异常处理(HANDLER)",
        "severity": "error", "score_deduction": 6,
        "description": "MySQL DECLARE ... HANDLER在DWS中使用EXCEPTION块替代",
        "source_pattern": "DECLARE CONTINUE HANDLER FOR SQLEXCEPTION ...",
        "target_solution": "BEGIN ... EXCEPTION WHEN OTHERS THEN ... END;",
        "compatible": False,
        "note": "MySQL的HANDLER可CONTINUE或EXIT，DWS的EXCEPTION块总是退出",
        "migration_difficulty": "高",
        "migration_suggestion": "将CONTINUE HANDLER改为BEGIN...EXCEPTION...END块重新设计"
    },
    {
        "id": "MYSQL-SQLPSM-007", "name": "循环语法差异",
        "severity": "warning", "score_deduction": 2,
        "description": "MySQL REPEAT/WHILE/LOOP循环与DWS语法差异",
        "source_pattern": "WHILE cond DO ... END WHILE; / REPEAT ... UNTIL cond END REPEAT;",
        "target_solution": "WHILE cond LOOP ... END LOOP; / LOOP ... EXIT WHEN cond; END LOOP;",
        "compatible": True,
        "note": "MySQL的DO/END WHILE -> DWS的LOOP/END LOOP",
        "migration_difficulty": "低",
        "migration_suggestion": "全局替换循环关键字"
    },
    {
        "id": "MYSQL-SQLPSM-008", "name": "动态SQL(PREPARE/EXECUTE)",
        "severity": "warning", "score_deduction": 3,
        "description": "MySQL PREPARE+EXECUTE+DEALLOCATE在DWS中使用EXECUTE...USING",
        "source_pattern": "SET @sql = '...'; PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;",
        "target_solution": "EXECUTE '...' USING var;",
        "compatible": True,
        "note": "DWS的EXECUTE...USING更简洁，不需要三步操作",
        "migration_difficulty": "中",
        "migration_suggestion": "将PREPARE+EXECUTE+DEALLOCATE合并为DWS的EXECUTE...USING"
    },
]
