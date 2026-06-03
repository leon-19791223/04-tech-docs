# -*- coding: utf-8 -*-
"""Remove duplicate D4-9/D4-10 from CH2_MULTI_EXT section"""
FILE = r"C:\Users\52985\Desktop\04-技术文档\HCCDE-GaussDB题库系统\hccde_quiz.py"

with open(FILE, "r", encoding="utf-8") as f:
    content = f.read()

# Remove the duplicate D4-9 and D4-10 items from the wrong location
# They exist at both CH2_MULTI_EXT and CH4_SINGLE_EXT - remove from CH2
old = '''    },
    {
        "id": "D4-9",
        "question": "GaussDB中，查看指定时间区间审计日志的正确语法是？",
        "options": ["A. SELECT * FROM pg_audit_log WHERE time BETWEEN 't1' AND 't2'", "B. gs_audit_log -s 't1' -e 't2'", "C. SELECT * FROM pg_query_audit('t1', 't2')", "D. AUDIT LOG FROM 't1' TO 't2'"],
        "answer": "C",
        "analysis": "GaussDB通过pg_query_audit('start_time', 'end_time')函数查询指定时间区间的审计日志记录。"
    }
,
    {
        "id": "D4-10",
        "question": "GaussDB的动态数据脱敏功能，支持对以下哪些DML操作进行脱敏？",
        "options": ["A. 仅SELECT", "B. SELECT和INSERT", "C. SELECT、INSERT、UPDATE、DELETE", "D. 仅INSERT和UPDATE"],
        "answer": "C",
        "analysis": "动态数据脱敏支持对SELECT、INSERT、UPDATE、DELETE四种操作进行脱敏处理。"
    }
]

CH3_JUDGE_EXT'''

new = '''    }
]

CH3_JUDGE_EXT'''

if old in content:
    content = content.replace(old, new, 1)
    print("Duplicates removed from CH2_MULTI_EXT")
else:
    print("Pattern not found! Trying alternative...")
    # Search for the vicinity
    for i, line in enumerate(content.split("\n")):
        if '"D4-9"' in line and i > 1100 and i < 1160:
            print(f"Line {i+1}: {line}")

with open(FILE, "w", encoding="utf-8") as f:
    f.write(content)
print("Saved.")
