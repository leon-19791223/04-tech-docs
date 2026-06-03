# -*- coding: utf-8 -*-
"""Add 6 missing exam review questions to hccde_quiz.py"""
FILE = r"C:\Users\52985\Desktop\04-技术文档\HCCDE-GaussDB题库系统\hccde_quiz.py"

with open(FILE, "r", encoding="utf-8") as f:
    content = f.read()

# 1. CH3_SINGLE_EXT - Add D3-21 startup order + D3-22 CN recovery
old1 = '''        "analysis": "就地升级需停止数据库服务进行升级，业务中断时间长。滚动/灰度升级支持在线逐节点升级。"
    }
]

CH3_MULTI_EXT = ['''

new1 = '''        "analysis": "就地升级需停止数据库服务进行升级，业务中断时间长。滚动/灰度升级支持在线逐节点升级。"
    },
    {
        "id": "D3-21",
        "question": "GaussDB集群启动时，各组件的正确启动顺序是？",
        "options": ["A. DN - CN - GTM - CSS", "B. CSS - GTM - CN - DN", "C. CN - DN - GTM - CSS", "D. 所有组件同时启动"],
        "answer": "B",
        "analysis": "GaussDB集群启动顺序：CSS先启动负责管理启动流程，然后GTM启动，接着CN启动，最后DN启动，确保组件依赖正确。"
    },
    {
        "id": "D3-22",
        "question": "GaussDB集群中，当CN节点发生故障被自动剔除后，修复完成后应如何恢复？",
        "options": ["A. 被剔除的CN会自动重启恢复", "B. 使用gs_ctl或集群管理工具重新启动CN进程", "C. 无需操作，故障后新CN自动创建", "D. 故障CN不再需要恢复，直接删除"],
        "answer": "B",
        "analysis": "CN故障被剔除后的恢复流程：修复故障原因（硬件/网络/配置）后，使用gs_ctl或集群管理工具重新启动CN进程，验证CN与GTM连接正常，确认集群状态恢复balanced。"
    }
]

CH3_MULTI_EXT = ['''

if old1 in content:
    content = content.replace(old1, new1, 1)
    print("1. CH3_SINGLE_EXT: D3-21 + D3-22 added")
else:
    print("1. ERROR: CH3_SINGLE_EXT end not found!")

# 2. CH4_SINGLE_EXT - Add D4-11 TDE scenarios
old2 = '''        "answer": "B",
        "analysis": "TDE（Transparent Data Encryption）在数据库内核层完成加密/解密操作，对上层应用完全透明，无需修改应用程序。"
    }
]

CH4_MULTI_EXT = ['''

new2 = '''        "answer": "B",
        "analysis": "TDE（Transparent Data Encryption）在数据库内核层完成加密/解密操作，对上层应用完全透明，无需修改应用程序。"
    },
    {
        "id": "D4-11",
        "question": "关于GaussDB透明加密（TDE）的使用场景和性能影响，以下说法正确的是？",
        "options": ["A. TDE对所有数据类型加密性能开销相同", "B. TDE加密后查询性能完全不变", "C. TDE适用于存储敏感数据的场景，会有一定的读写性能开销", "D. TDE仅对列存储生效"],
        "answer": "C",
        "analysis": "TDE在存储引擎层对数据文件进行实时加密/解密，适用于存储身份证、银行卡等敏感数据的场景。由于加解密操作在数据读写路径上，会有一定的性能开销，并非完全无影响。"
    }
]

CH4_MULTI_EXT = ['''

if old2 in content:
    content = content.replace(old2, new2, 1)
    print("2. CH4_SINGLE_EXT: D4-11 added")
else:
    print("2. ERROR: CH4_SINGLE_EXT end not found!")

# 3. CH5_SINGLE_EXT - Add D5-15 query optimization with many tables
old3 = '''        "analysis": "pg_stat_activity视图可以查看当前数据库会话状态和正在执行的SQL语句，当动态内存使用较高时，通过该视图查找占用内存较多的会话和SQL进行优化。"
    }
]

CH5_MULTI_EXT = ['''

new3 = '''        "analysis": "pg_stat_activity视图可以查看当前数据库会话状态和正在执行的SQL语句，当动态内存使用较高时，通过该视图查找占用内存较多的会话和SQL进行优化。"
    },
    {
        "id": "D5-15",
        "question": "客户数据库中表数量较多（数千张表），查询效率偏低，以下哪个GUC参数调整最有助于优化此类场景的查询效率？",
        "options": ["A. 增大max_connections", "B. 开启enable_global_plancache缓存通用计划", "C. 增大wal_buffers", "D. 降低maintenance_work_mem"],
        "answer": "B",
        "analysis": "表数量多的场景，频繁的SQL编译和计划生成会消耗大量资源。开启enable_global_plancache后，通用执行计划（gplan）可被多个会话复用，减少重复优化开销。max_connections控制连接数而非查询效率。"
    }
]

CH5_MULTI_EXT = ['''

if old3 in content:
    content = content.replace(old3, new3, 1)
    print("3. CH5_SINGLE_EXT: D5-15 added")
else:
    print("3. ERROR: CH5_SINGLE_EXT end not found!")

# 4. CH2_MULTI_EXT - Add M2-11 TPS concept question
old4 = '''        "analysis": "A方案深圳全部轻量化不满足HA要求。B/C/D方案均满足HCS+轻量化混合部署的可行性要求，兼顾成本和业务连续性。"
    }
]

CH3_JUDGE_EXT = ['''

new4 = '''        "analysis": "A方案深圳全部轻量化不满足HA要求。B/C/D方案均满足HCS+轻量化混合部署的可行性要求，兼顾成本和业务连续性。"
    },
    {
        "id": "M2-11",
        "question": "关于GaussDB性能指标TPS（Transactions Per Second），以下描述正确的有？",
        "options": ["A. TPS表示系统每秒处理的事务数量", "B. TPS计算需要考虑高峰期集中系数", "C. tpmC是TPC-C基准测试的每分钟吞吐量指标", "D. TPS与tpmC是同一概念的不同表达", "E. 单笔业务可能产生多个数据库事务"],
        "answer": "ABCE",
        "analysis": "TPS衡量每秒事务处理能力，计算时需考虑高峰期集中系数。tpmC是TPC-C基准测试的每分钟吞吐量，TPS和tpmC是不同的指标概念（D错误）。单笔业务操作可能分解为多个数据库事务。"
    }
]

CH3_JUDGE_EXT = ['''

if old4 in content:
    content = content.replace(old4, new4, 1)
    print("4. CH2_MULTI_EXT: M2-11 added")
else:
    print("4. ERROR: CH2_MULTI_EXT end not found!")

with open(FILE, "w", encoding="utf-8") as f:
    f.write(content)

print("\nDone! All 6 questions added.")
