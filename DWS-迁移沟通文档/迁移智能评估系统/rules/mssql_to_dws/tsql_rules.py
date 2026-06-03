"""SQL Server T-SQL 存储过程兼容性规则"""
TSQL_RULES = [
    {
        "id": "MSSQL-TSQL-001", "name": "存储过程创建语法",
        "severity": "warning", "score_deduction": 3,
        "description": "SQL Server CREATE PROCEDURE与DWS PL/pgSQL语法有差异",
        "source_pattern": "CREATE PROCEDURE proc_name @p1 INT, @p2 VARCHAR(100) AS BEGIN ... END",
        "target_solution": "CREATE OR REPLACE FUNCTION proc_name(p1 INT, p2 VARCHAR(300)) RETURNS ... LANGUAGE plpgsql AS $$ ... $$",
        "compatible": True,
        "note": "SQL Server参数使用@前缀，DWS不需要; AS BEGIN...END改为LANGUAGE plpgsql AS $$...$$",
        "migration_difficulty": "中",
        "migration_suggestion": "1)移除@前缀; 2) RETURNS类型适配; 3)体包装到$$内"
    },
    {
        "id": "MSSQL-TSQL-002", "name": "变量声明与赋值",
        "severity": "warning", "score_deduction": 2,
        "description": "SQL Server DECLARE @var TYPE = val 与PL/pgSQL语法差异",
        "source_pattern": "DECLARE @v_name VARCHAR(100) = 'default'; / SET @v_name = 'value';",
        "target_solution": "v_name VARCHAR(300) := 'default'; / v_name := 'value'; (注意VARCHAR长度3倍扩展)",
        "compatible": True,
        "note": "SQL Server使用@前缀+SET赋值，DWS使用:=直接赋值",
        "migration_difficulty": "低",
        "migration_suggestion": "批量替换: DECLARE @v TYPE = val -> v TYPE := val; SET @v = -> v := "
    },
    {
        "id": "MSSQL-TSQL-003", "name": "IF...ELSE语法",
        "severity": "info", "score_deduction": 0,
        "description": "SQL Server IF...ELSE在DWS中兼容",
        "compatible": True, "note": "完全兼容"
    },
    {
        "id": "MSSQL-TSQL-004", "name": "WHILE循环差异",
        "severity": "warning", "score_deduction": 2,
        "description": "SQL Server WHILE cond BEGIN ... END在DWS中为WHILE cond LOOP ... END LOOP",
        "source_pattern": "WHILE cond BEGIN statements; END",
        "target_solution": "WHILE cond LOOP statements; END LOOP;",
        "compatible": True,
        "note": "SQL Server使用BEGIN...END块，DWS使用LOOP...END LOOP",
        "migration_difficulty": "低",
        "migration_suggestion": "全局替换 BEGIN -> LOOP (在WHILE体内); END -> END LOOP"
    },
    {
        "id": "MSSQL-TSQL-005", "name": "游标处理差异",
        "severity": "warning", "score_deduction": 3,
        "description": "SQL Server游标(DECLARE CURSOR)与DWS语法差异",
        "source_pattern": "DECLARE cur CURSOR FOR SELECT ...; OPEN cur; FETCH NEXT FROM cur INTO @var; CLOSE cur; DEALLOCATE cur;",
        "target_solution": "DECLARE cur CURSOR FOR SELECT ...; OPEN cur; FETCH cur INTO var; CLOSE cur;",
        "compatible": True,
        "note": "SQL Server使用FETCH NEXT FROM、需DEALLOCATE; DWS使用FETCH INTO、CLOSE即释放",
        "migration_difficulty": "中",
        "migration_suggestion": "批量替换: FETCH NEXT FROM cur INTO @v -> FETCH cur INTO v; 移除DEALLOCATE"
    },
    {
        "id": "MSSQL-TSQL-006", "name": "异常处理(TRY...CATCH)",
        "severity": "error", "score_deduction": 6,
        "description": "SQL Server TRY...CATCH在DWS中使用EXCEPTION块替代",
        "source_pattern": "BEGIN TRY statements; END TRY BEGIN CATCH SELECT ERROR_MESSAGE(); END CATCH",
        "target_solution": "BEGIN ... EXCEPTION WHEN OTHERS THEN RAISE NOTICE '%', SQLERRM; END;",
        "compatible": False,
        "note": "SQL Server的TRY...CATCH与DWS的EXCEPTION块范式不同",
        "migration_difficulty": "高",
        "migration_suggestion": "将TRY...CATCH改为BEGIN...EXCEPTION...END; ERROR_MESSAGE()改为SQLERRM或GET STACKED DIAGNOSTICS"
    },
    {
        "id": "MSSQL-TSQL-007", "name": "事务控制(BEGIN TRAN/COMMIT/ROLLBACK)",
        "severity": "warning", "score_deduction": 3,
        "description": "SQL Server事务控制与DWS兼容但SAVE TRAN不支持",
        "source_pattern": "BEGIN TRANSACTION; ... SAVE TRANSACTION sp; ... ROLLBACK TRANSACTION sp; COMMIT;",
        "target_solution": "BEGIN; ... SAVEPOINT sp; ... ROLLBACK TO sp; COMMIT;",
        "compatible": True,
        "note": "SAVE TRANSACTION->SAVEPOINT, ROLLBACK TRANSACTION sp->ROLLBACK TO sp",
        "migration_difficulty": "中",
        "migration_suggestion": "全局替换事务控制关键字"
    },
    {
        "id": "MSSQL-TSQL-008", "name": "动态SQL(EXEC/sp_executesql)",
        "severity": "warning", "score_deduction": 3,
        "description": "SQL Server EXEC(@sql)/sp_executesql在DWS中使用EXECUTE...USING",
        "source_pattern": "EXEC(@sql) / EXEC sp_executesql @sql, N'@p1 INT', @p1=1",
        "target_solution": "EXECUTE sql_string; / EXECUTE sql_string USING p1;",
        "compatible": True,
        "note": "功能对等，语法不同。DWS的EXECUTE...USING支持参数化",
        "migration_difficulty": "中",
        "migration_suggestion": "EXEC(@sql) -> EXECUTE sql_str; sp_executesql -> EXECUTE ... USING"
    },
]
