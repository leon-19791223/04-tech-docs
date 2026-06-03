# -*- coding: utf-8 -*-
"""Fix: Move D4-9/D4-10 from CH2_MULTI_EXT to CH4_SINGLE_EXT, add M2-11 to CH2_MULTI_EXT"""
FILE = r"C:\Users\52985\Desktop\04-技术文档\HCCDE-GaussDB题库系统\hccde_quiz.py"

with open(FILE, "r", encoding="utf-8") as f:
    content = f.read()

# Step 1: Fix CH2_MULTI_EXT - remove D4-9/D4-10, append M2-11
old_ch2 = '''CH2_MULTI_EXT = [
    {
        "id": "M2-6",
        "question": "关于GaussDB集中式和分布式部署方案的选型考虑，以下说法正确的有？",
        "options": ["A. 集中式适合SQL复杂、存量存储过程较多的场景", "B. 分布式适合大容量(>=2TB)、高并发的场景", "C. 集中式不支持主备高可用", "D. 分布式支持扩缩容，扩展性好", "E. 数据量小于2TB时只能选择集中式"],
        "answer": "ABD",
        "analysis": "集中式适合SQL复杂、存储过程多、<2TB；分布式适合>=2TB、高并发、扩展性要求高的场景。集中式也支持主备高可用，E选项过于绝对。"
    },
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
]'''

new_ch2 = '''CH2_MULTI_EXT = [
    {
        "id": "M2-6",
        "question": "关于GaussDB集中式和分布式部署方案的选型考虑，以下说法正确的有？",
        "options": ["A. 集中式适合SQL复杂、存量存储过程较多的场景", "B. 分布式适合大容量(>=2TB)、高并发的场景", "C. 集中式不支持主备高可用", "D. 分布式支持扩缩容，扩展性好", "E. 数据量小于2TB时只能选择集中式"],
        "answer": "ABD",
        "analysis": "集中式适合SQL复杂、存储过程多、<2TB；分布式适合>=2TB、高并发、扩展性要求高的场景。集中式也支持主备高可用，E选项过于绝对。"
    },
    {
        "id": "M2-7",
        "question": "国标GB/T 20988-2007容灾等级中，以下关于各级RPO/RTO的描述正确的有？",
        "options": ["A. 1级：RTO<=2天，RPO=1~7天", "B. 2级和3级：RTO均<=12小时", "C. 4级：RTO<=6小时，RPO<15分钟", "D. 5级：RPO=0~30分钟，RTO=数分钟~2天", "E. 6级：RPO=0，RTO=秒级"],
        "answer": "ACDE",
        "analysis": "2级RTO<=24小时，3级RTO<=12小时。B选项中2级和3级RTO并不同。"
    },
    {
        "id": "M2-8",
        "question": "使用本地盘规划GaussDB存储时，推荐的RAID方案为？",
        "options": ["A. 系统盘RAID1", "B. 数据盘RAID10", "C. 系统盘RAID5", "D. 数据盘RAID6", "E. 数据盘RAID-TP"],
        "answer": "AB",
        "analysis": "系统盘RAID1（镜像冗余），数据盘RAID10（条带+镜像）。"
    },
    {
        "id": "M2-9",
        "question": "GaussDB数据压缩与性能的关系，以下说法正确的有？",
        "options": ["A. TP业务表典型压缩率2:1", "B. 索引典型压缩率3:1", "C. 历史数据典型压缩率5:1", "D. WAL日志典型压缩率4:1", "E. 高性能场景应采用有损压缩"],
        "answer": "ABCD",
        "analysis": "TP表2:1、索引3:1、历史数据5:1、WAL4:1。E错误，有损压缩不适用于数据库数据。"
    },
    {
        "id": "M2-10",
        "question": "关于GaussDB性能指标TPS，以下描述正确的有？",
        "options": ["A. TPS表示系统每秒处理的事务数量", "B. TPS计算需要考虑高峰期集中系数", "C. tpmC是TPC-C基准测试的每分钟吞吐量指标", "D. TPS与tpmC是同一概念的不同表达", "E. 单笔业务可能产生多个数据库事务"],
        "answer": "ABCE",
        "analysis": "TPS衡量每秒事务处理能力，需考虑高峰期集中系数。tpmC是TPC-C每分钟吞吐量，TPS与tpmC是不同的指标概念（D错误）。"
    }
]'''

assert old_ch2 in content, "CH2_MULTI_EXT content not found!"
content = content.replace(old_ch2, new_ch2, 1)
print("1. CH2_MULTI_EXT: fixed (removed D4-9/D4-10, added M2-7~M2-10)")

# Step 2: Fix CH4_SINGLE_EXT - add D4-9, D4-10, D4-11 after D4-8
old_ch4 = '''        "answer": "B",
        "analysis": "TDE（Transparent Data Encryption）在数据库内核层完成加密/解密操作，对上层应用完全透明，无需修改应用程序。"
    }
]

CH4_MULTI_EXT = ['''

new_ch4 = '''        "answer": "B",
        "analysis": "TDE（Transparent Data Encryption）在数据库内核层完成加密/解密操作，对上层应用完全透明，无需修改应用程序。"
    },
    {
        "id": "D4-9",
        "question": "GaussDB中，查看指定时间区间审计日志的正确语法是？",
        "options": ["A. SELECT * FROM pg_audit_log WHERE time BETWEEN 't1' AND 't2'", "B. gs_audit_log -s 't1' -e 't2'", "C. SELECT * FROM pg_query_audit('t1', 't2')", "D. AUDIT LOG FROM 't1' TO 't2'"],
        "answer": "C",
        "analysis": "GaussDB通过pg_query_audit函数查询指定时间区间的审计日志记录。"
    },
    {
        "id": "D4-10",
        "question": "GaussDB的动态数据脱敏功能，支持对以下哪些DML操作进行脱敏？",
        "options": ["A. 仅SELECT", "B. SELECT和INSERT", "C. SELECT、INSERT、UPDATE、DELETE", "D. 仅INSERT和UPDATE"],
        "answer": "C",
        "analysis": "动态数据脱敏支持对SELECT、INSERT、UPDATE、DELETE四种操作进行脱敏处理。"
    },
    {
        "id": "D4-11",
        "question": "关于GaussDB透明加密（TDE）的使用场景和性能影响，以下说法正确的是？",
        "options": ["A. TDE对所有数据类型加密性能开销相同", "B. TDE加密后查询性能完全不变", "C. TDE适用于存储敏感数据的场景，有一定的读写性能开销", "D. TDE仅对列存储生效"],
        "answer": "C",
        "analysis": "TDE在存储引擎层对数据文件实时加密/解密，适用于存储敏感数据的场景，会有一定的读写性能开销，并非完全无影响。"
    }
]

CH4_MULTI_EXT = ['''

assert old_ch4 in content, "CH4_SINGLE_EXT end not found!"
content = content.replace(old_ch4, new_ch4, 1)
print("2. CH4_SINGLE_EXT: D4-9, D4-10, D4-11 added")

with open(FILE, "w", encoding="utf-8") as f:
    f.write(content)

print("Done! File saved.")
