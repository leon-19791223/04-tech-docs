#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HCCDE-GaussDB 分章节理论考题刷题程序
===============================
基于考试大纲六大知识领域，支持：
- 分章节刷题 / 随机抽题 / 模拟考试 三种模式
- 判断题、单选题、多选题三种题型
- 自动判分 + 详细解析
- 错题本功能
- 进度统计
"""

import sys
import random
import os

# ============================================================
# 题库数据（按章节组织）
# ============================================================

CHAPTERS = [
    {
        "id": 1,
        "name": "GaussDB 软件体系架构",
        "weight": "5%"
    },
    {
        "id": 2,
        "name": "GaussDB 数据库规划设计",
        "weight": "22%"
    },
    {
        "id": 3,
        "name": "GaussDB 数据库内核原理",
        "weight": "20%"
    },
    {
        "id": 4,
        "name": "GaussDB 安全管理",
        "weight": "9%"
    },
    {
        "id": 5,
        "name": "GaussDB 性能调优",
        "weight": "9%"
    },
    {
        "id": 6,
        "name": "GaussDB 运维与故障处理",
        "weight": "22%"
    }
]

# ---------- 第一章：软件体系架构 ----------
CH1_JUDGE = [
    {
        "id": "J1-1",
        "question": "GaussDB的\"五高两易\"中，\"两易\"指的是易部署和易迁移。",
        "answer": "√",
        "analysis": "GaussDB核心优势\"五高两易\"：高可用、高性能、高安全、高弹性、高并发；易部署/易迁移、易开发/易维护。"
    },
    {
        "id": "J1-2",
        "question": "GaussDB分布式架构中，GTM负责生成和维护全局事务ID，确保全局事务一致性。",
        "answer": "√",
        "analysis": "GTM（Global Transaction Manager）生成全局唯一事务ID和事务快照，协调各DN节点分布式事务的一致性。"
    },
    {
        "id": "J1-3",
        "question": "GaussDB仅支持集中式部署形态，不支持分布式部署。",
        "answer": "×",
        "analysis": "GaussDB同时支持集中式和分布式两种部署形态，集中式适合SQL复杂、存量存储过程多的场景，分布式适合大容量、高并发的场景。"
    },
    {
        "id": "J1-4",
        "question": "GaussDB的逻辑解码仅支持目标数据库为GaussDB自身。",
        "answer": "×",
        "analysis": "GaussDB逻辑复制原生支持GaussDB和PostgreSQL为目标数据库，通过DRS工具还可支持MySQL等其他数据库。"
    },
    {
        "id": "J1-5",
        "question": "GaussDB的线程池技术是应对高并发连接的关键手段之一。",
        "answer": "√",
        "analysis": "线程池技术通过复用工作线程，减少频繁创建/销毁线程的开销，是GaussDB高并发实现的核心策略之一。"
    }
]

CH1_SINGLE = [
    {
        "id": "D1-1",
        "question": "GaussDB分布式架构中，负责接收客户端SQL请求并进行分发处理的组件是？",
        "options": ["A. GTM", "B. DN", "C. CN", "D. CMS"],
        "answer": "C",
        "analysis": "CN（Coordinator Node）作为协调节点，接收客户端SQL请求，进行SQL解析、优化和分发执行。"
    },
    {
        "id": "D1-2",
        "question": "GaussDB中，AStore存储引擎采用的更新方式是？",
        "options": ["A. Append Update（追加更新）", "B. In-place Update（原地更新）", "C. Copy-on-Write（写时复制）", "D. Out-of-Place Update（异位更新）"],
        "answer": "A",
        "analysis": "AStore采用Append Update，更新时插入新元组（新版本），旧版本作为历史数据保留，适合insert多、update少的场景。"
    },
    {
        "id": "D1-3",
        "question": "GaussDB的UStore存储引擎相比AStore的主要优势是？",
        "options": ["A. 写入速度更快", "B. UPDATE频繁场景下存储膨胀小", "C. 查询性能更高", "D. 支持更多数据类型"],
        "answer": "B",
        "analysis": "UStore采用In-place Update，新老版本分离存储，老版本集中管理，UPDATE频繁时存储空间膨胀小、性能稳定。"
    },
    {
        "id": "D1-4",
        "question": "GaussDB分布式事务强一致性实现的核心依赖组件是？",
        "options": ["A. CN", "B. CMS", "C. GTM", "D. ETCD"],
        "answer": "C",
        "analysis": "GTM（全局事务管理器）负责全局事务ID分配、快照生成和分布式事务提交协调，是分布式强一致性的核心组件。"
    },
    {
        "id": "D1-5",
        "question": "GaussDB中，以下哪个缓存属于静态内存？",
        "options": ["A. Work mem", "B. Global plan cache", "C. Local sys cache", "D. Temp buffers"],
        "answer": "B",
        "analysis": "静态内存在实例启动时分配，固定不变，包括Global sys cache和Global plan cache。Work mem、Local sys cache、Temp buffers属于动态内存。"
    },
    {
        "id": "D1-6",
        "question": "GaussDB分布式架构的Stream技术主要作用是？",
        "options": ["A. 数据备份", "B. 日志传输", "C. 权限控制", "D. 分布式查询中数据在DN间流转"],
        "answer": "D",
        "analysis": "Stream是GaussDB分布式执行框架的核心技术，负责在DN节点间高效流转中间结果数据，支持分布式并行查询。"
    },
    {
        "id": "D1-7",
        "question": "GaussDB极速RTO（Recovery Time Objective）技术的关键实现机制是？",
        "options": ["A. 增加checkpoint频率", "B. 备机并行回放WAL日志", "C. 减少WAL日志量", "D. 预分配数据块"],
        "answer": "B",
        "analysis": "极速RTO通过备机并行回放WAL日志技术，利用多核CPU并行处理，将主备切换恢复时间降低到秒级。"
    },
    {
        "id": "D1-8",
        "question": "GaussDB集中式架构的核心组件不包括以下哪个？",
        "options": ["A. OM", "B. CMS", "C. DN", "D. GTM"],
        "answer": "D",
        "analysis": "集中式架构核心组件为OM、CMS、DN。GTM是分布式架构的专属组件，集中式无GTM。"
    },
    {
        "id": "D1-9",
        "question": "GaussDB的\"应用无损透明（ALT）\"技术的主要功能是？",
        "options": ["A. 数据加密", "B. 主备切换时客户端连接自动恢复", "C. SQL语句自动改写", "D. 自动创建索引"],
        "answer": "B",
        "analysis": "ALT实现主备切换时客户端连接自动重连、运行中SQL重试、session级参数自动恢复，对应用透明。"
    },
    {
        "id": "D1-10",
        "question": "GaussDB的分布式执行框架中，CN轻量化执行计划（SQL Bypass）的适用场景是？",
        "options": ["A. 简单查询语句（单表查询等）", "B. 复杂多表Join", "C. 分布式事务", "D. DDL操作"],
        "answer": "A",
        "analysis": "SQL Bypass针对简单SQL直接下发DN执行，跳过优化器和重写器，减少CN压力，降低执行延迟。"
    }
]

CH1_MULTI = [
    {
        "id": "M1-1",
        "question": "GaussDB的\"五高两易\"核心竞争力包括以下哪些？",
        "options": ["A. 高可用、高性能", "B. 高安全、高弹性", "C. 高并发", "D. 易部署、易迁移", "E. 易查询、易分析"],
        "answer": "ABCD",
        "analysis": "\"五高\"=高可用、高性能、高安全、高弹性、高并发；\"两易\"=易部署/易迁移、易开发/易维护。E选项\"易查询、易分析\"不属于两易。"
    },
    {
        "id": "M1-2",
        "question": "GaussDB高并发实现策略包括？",
        "options": ["A. 线程池", "B. 计划缓存（Plan Cache）", "C. SQL Bypass", "D. 数据压缩", "E. 多核CPU架构优化"],
        "answer": "ABCE",
        "analysis": "高并发策略通过减少开销和提升并行能力实现，包括线程池复用、计划缓存避免重复优化、SQL Bypass简化执行路径、多核优化并行处理。数据压缩主要节省存储，不属高并发策略。"
    },
    {
        "id": "M1-3",
        "question": "GaussDB支持的部署形态包括？",
        "options": ["A. 集中式", "B. 分布式", "C. 裸金属部署", "D. 虚拟化部署（ECS）", "E. 容器化部署"],
        "answer": "ABCD",
        "analysis": "GaussDB支持集中式/分布式核心架构，可在裸金属和虚拟化(ECS)上部署，暂不支持原生容器化部署。"
    },
    {
        "id": "M1-4",
        "question": "GaussDB集中式架构与分布式架构的区别体现在？",
        "options": ["A. 集中式无GTM/ETCD组件", "B. 分布式有CN节点进行SQL分发", "C. 集中式适合SQL复杂、存储过程多的场景", "D. 分布式也支持SQL Bypass", "E. 分布式支持线性扩容"],
        "answer": "ABCE",
        "analysis": "SQL Bypass是分布式CN的特性，集中式无此概念。D选项描述错误。"
    },
    {
        "id": "M1-5",
        "question": "GaussDB分布式执行框架中Stream技术支持的分布式执行模式包括？",
        "options": ["A. Redistribution Stream（重分布）", "B. Broadcast Stream（广播）", "C. Gather Stream（汇总）", "D. Merge Stream（合并）", "E. Split Stream（拆分）"],
        "answer": "ABC",
        "analysis": "分布式执行中Stream技术主要支持Redistribute（重分布）、Broadcast（广播）、Gather（汇总）三种数据流转模式。"
    }
]

# ---------- 第二章：数据库规划设计 ----------
CH2_JUDGE = [
    {
        "id": "J2-1",
        "question": "集中式GaussDB部署适用于业务SQL复杂、存量存储过程多、数据容量小于24TB的场景。",
        "answer": "√",
        "analysis": "集中式部署对应用透明，SQL兼容性好，适合SQL复杂、存储过程多、tps<2万、数据量<24TB的场景。"
    },
    {
        "id": "J2-2",
        "question": "GaussDB分布式部署形态下，业务系统需要具备SQL改造条件。",
        "answer": "√",
        "analysis": "分布式部署要求业务SQL相对简单，涉及分布键设计，需要对业务SQL进行一定程度的改造适配。"
    },
    {
        "id": "J2-3",
        "question": "GaussDB轻量化部署形态的管理节点数量为17台。",
        "answer": "×",
        "analysis": "轻量化部署管理节点仅需3台，而HCS标准形态单Region需17台管理节点。"
    },
    {
        "id": "J2-4",
        "question": "容灾等级国家标准GB/T 20988-2007中，6级容灾要求RPO=0、RTO为秒级。",
        "answer": "√",
        "analysis": "国标6级是最高容灾等级，要求数据零丢失（RPO=0），远程集群快速恢复（RTO为秒级）。"
    },
    {
        "id": "J2-5",
        "question": "GaussDB规划存储时，系统盘建议使用RAID5，数据盘建议使用RAID6。",
        "answer": "×",
        "analysis": "系统盘建议RAID1（镜像冗余），数据盘建议RAID10（条带+镜像，兼顾读写性能和数据冗余）。"
    }
]

CH2_SINGLE = [
    {
        "id": "D2-1",
        "question": "国标GB/T 20988-2007中，第5级容灾的RPO和RTO要求分别是？",
        "options": ["A. RPO=0，RTO=秒级", "B. RPO<15分钟，RTO≤6小时", "C. RPO=0~30分钟，RTO=数分钟~2天", "D. RPO=1~7天，RTO≤2天"],
        "answer": "C",
        "analysis": "5级容灾RPO=0~30分钟、RTO=数分钟~2天，通常采用同城多机房/双集群+异地容灾的部署方案。"
    },
    {
        "id": "D2-2",
        "question": "GaussDB HCS标准形态单Region管理节点数量为？",
        "options": ["A. 3台", "B. 6台", "C. 17台", "D. 20台"],
        "answer": "C",
        "analysis": "HCS标准形态为企业级云架构，管理节点包含OM、CMS、ETCD等全套管控组件，单Region需17台。"
    },
    {
        "id": "D2-3",
        "question": "GaussDB轻量化部署形态相比HCS标准形态的主要特点是？",
        "options": ["A. 管理节点瘦身、成本低、支持设备利旧", "B. 性能更高", "C. 功能更全面", "D. 安全性更高"],
        "answer": "A",
        "analysis": "轻量化部署精简了管理节点（3台），无虚拟化能力，支持设备利旧，初始投入成本低。"
    },
    {
        "id": "D2-4",
        "question": "GaussDB分布式架构中，单DN节点的存储利用率建议控制在多少以内？",
        "options": ["A. 50%", "B. 60%", "C. 70%", "D. 80%"],
        "answer": "C",
        "analysis": "单DN存储利用率建议控制在70%以内，为数据增长和均衡留有缓冲区，防止数据倾斜导致磁盘满。"
    },
    {
        "id": "D2-5",
        "question": "以下哪项不是GaussDB支持的存储类型？",
        "options": ["A. 本地盘", "B. 集中式存储（Dorado）", "C. 分布式存储（Pacific）", "D. NAS存储"],
        "answer": "D",
        "analysis": "GaussDB支持本地盘、集中式存储、分布式存储和云盘。NAS存储不支持作为GaussDB核心数据库存储。"
    },
    {
        "id": "D2-6",
        "question": "GaussDB容灾等级4级（RTO≤6小时，RPO<15分钟）对应的典型部署方案是？",
        "options": ["A. 本地备份", "B. 同城双机房单集群", "C. 同城双集群RPO=0+异地对等容灾", "D. 异地备份+定时同步"],
        "answer": "B",
        "analysis": "4级要求同城切换（RPO<15分钟），通常采用同城两个机房部署单集群，一个机房故障时另一个机房接管。"
    },
    {
        "id": "D2-7",
        "question": "GaussDB网络规划中，Region内（跨AZ）网络时延要求小于？",
        "options": ["A. 0.25毫秒", "B. 1毫秒", "C. 2毫秒", "D. 5毫秒"],
        "answer": "C",
        "analysis": "Region内跨AZ网络时延需<2ms，AZ内部（同机房）需<0.25ms，跨Region需<20ms。"
    },
    {
        "id": "D2-8",
        "question": "某金融客户核心系统日处理业务量500万笔，高峰期集中在2小时，单笔业务产生4个事务，高峰期TPS约为？",
        "options": ["A. 2778", "B. 5556", "C. 10000", "D. 20000"],
        "answer": "A",
        "analysis": "高峰总事务数=500万×4=2000万；高峰时长=2×3600=7200秒；TPS=2000万÷7200≈2778 tps。"
    },
    {
        "id": "D2-9",
        "question": "GaussDB规划存储时，通常需预留的存储空间比例至少为？",
        "options": ["A. 10%", "B. 20%", "C. 30%", "D. 50%"],
        "answer": "C",
        "analysis": "存储预留比例至少30%，用于应对数据增长、日志存储、WAL归档、碎片整理等。"
    },
    {
        "id": "D2-10",
        "question": "GaussDB集中式1主2备3副本架构需要多少节点？",
        "options": ["A. 3个", "B. 5个", "C. 6个", "D. 9个"],
        "answer": "A",
        "analysis": "集中式1主2备=3个节点，3副本即每个节点有1份主副本，共3份副本分布在3个节点。"
    },
    {
        "id": "D2-11",
        "question": "GaussDB分布式3C3D3副本架构所需的最小节点数为？",
        "options": ["A. 3个", "B. 6个", "C. 9个", "D. 12个"],
        "answer": "C",
        "analysis": "3C=3个CN，3D=3组DN，3副本每组DN 1主2备。最小节点数通常按9个节点理解：每个节点部署1个CN+1个DN进程，3节点为1组（含1CN+1主DN+2备DN），3组共9个节点。"
    },
    {
        "id": "D2-12",
        "question": "GaussDB规划中，对于TP类型业务数据表，典型的压缩率约为？",
        "options": ["A. 2:1", "B. 3:1", "C. 4:1", "D. 5:1"],
        "answer": "A",
        "analysis": "TP业务数据表典型压缩率2:1，索引压缩率3:1，历史数据压缩率5:1，WAL日志压缩率4:1。"
    }
]

CH2_MULTI = [
    {
        "id": "M2-1",
        "question": "适合选择GaussDB集中式部署的业务场景特征包括？",
        "options": ["A. 业务SQL复杂，改造成本高", "B. 存量存储过程多", "C. 业务TPS小于2万", "D. 数据容量在24TB以内", "E. 希望最小化应用改造"],
        "answer": "ABCDE",
        "analysis": "集中式对应用透明，适合SQL复杂、存量大存储过程、中小规模业务量的场景，无需改造应用。"
    },
    {
        "id": "M2-2",
        "question": "适合选择GaussDB分布式部署的业务场景特征包括？",
        "options": ["A. 业务SQL相对简单", "B. 业务具备改造条件", "C. 业务TPS超过2万", "D. 数据容量超过24TB", "E. 需要线性扩展性能"],
        "answer": "ABCDE",
        "analysis": "分布式部署支持在线扩容和性能线性扩展，适合高并发、大数据量、可接受SQL改造的场景。"
    },
    {
        "id": "M2-3",
        "question": "GaussDB两地三中心容灾方案包含的部署层次有？",
        "options": ["A. 生产中心（主）", "B. 同城灾备中心", "C. 异地灾备中心", "D. 公有云灾备", "E. 多云灾备"],
        "answer": "ABC",
        "analysis": "两地三中心=生产中心（主）+同城灾备中心（RPO=0）+异地灾备中心（异步复制）。"
    },
    {
        "id": "M2-4",
        "question": "GaussDB存储容量评估的关键影响要素包括？",
        "options": ["A. 表行数及字段类型", "B. 索引数量和类型", "C. Redo日志文件大小", "D. Undo日志文件大小", "E. WAL日志归档策略"],
        "answer": "ABCDE",
        "analysis": "存储容量需综合评估业务数据（表+索引）和数据库运行日志（Redo、Undo、WAL等）的全量占用。"
    },
    {
        "id": "M2-5",
        "question": "GaussDB备份容量估算的输入参数包括？",
        "options": ["A. 业务总数据量", "B. 备份保留周期", "C. 备份周期（频率）", "D. 压缩比", "E. 数据库端口号"],
        "answer": "ABCD",
        "analysis": "备份容量=全量备份容量+增量备份容量，需考虑数据量、保留周期、备份频率和压缩比。端口号属于网络规划，无关。"
    }
]

# ---------- 第三章：数据库内核原理 ----------
CH3_JUDGE = [
    {
        "id": "J3-1",
        "question": "GaussDB SQL引擎的执行器采用迭代器模式（火山模型）进行SQL执行。",
        "answer": "√",
        "analysis": "GaussDB执行器采用经典的火山模型（Volcano Model），各算子通过迭代器接口（open-next-close）逐行/批量向上层返回数据。"
    },
    {
        "id": "J3-2",
        "question": "GaussDB的ABO优化器基于贝叶斯网络实现智能基数估计。",
        "answer": "√",
        "analysis": "ABO（Adaptive Bayesian Optimizer）优化器库内集成轻量级贝叶斯网络算法，实现智能基数估计和选择率计算。"
    },
    {
        "id": "J3-3",
        "question": "GaussDB的行存表（AStore）在更新数据时，直接在原数据位置覆盖写入。",
        "answer": "×",
        "analysis": "AStore采用Append Update方式，更新时在数据页尾部追加新版本，不覆盖原数据。In-place Update是UStore的特性。"
    },
    {
        "id": "J3-4",
        "question": "GaussDB分区表支持静态分区剪枝和动态分区剪枝两种优化技术。",
        "answer": "√",
        "analysis": "静态剪枝在计划阶段根据SQL语句确定的分区条件直接裁剪；动态剪枝在执行阶段根据参数值确定分区。"
    },
    {
        "id": "J3-5",
        "question": "GaussDB的WAL日志完全采用无锁机制写入，不存在任何锁竞争。",
        "answer": "×",
        "analysis": "GaussDB WAL写入采用Lock-Free技术减少锁竞争，但并非完全无锁，只是通过预分配WAL buffer和原子操作将锁粒度降到最低。"
    }
]

CH3_SINGLE = [
    {
        "id": "D3-1",
        "question": "GaussDB的解析器（Parser）完成的主要工作是？",
        "options": ["A. 词法分析和语法分析，生成语法解析树", "B. 生成执行计划", "C. 执行SQL语句", "D. 管理事务"],
        "answer": "A",
        "analysis": "解析器负责词法分析（将SQL拆分为Token）和语法分析（生成Parse Tree），后续由优化器生成执行计划。"
    },
    {
        "id": "D3-2",
        "question": "GaussDB的ABO优化器相比传统优化器的核心增强是？",
        "options": ["A. 支持更多Join算法", "B. 更快的解析速度", "C. 基于贝叶斯网络的智能基数估计和自适应计划选择", "D. 支持更多的数据类型"],
        "answer": "C",
        "analysis": "ABO的核心竞争力是智能基数估计（贝叶斯网络）和自适应计划选择（根据实际执行反馈动态调整）。"
    },
    {
        "id": "D3-3",
        "question": "GaussDB的行存表在AStore存储引擎下，单条元组在页面中的组成部分包括？",
        "options": ["A. 元组头 + 数据", "B. 元组指针 + 元组头 + 数据", "C. 页面头 + 元组指针 + 元组头 + 数据", "D. 页面头 + 数据"],
        "answer": "C",
        "analysis": "GaussDB页面结构：Page Header（页面头）+ ItemId（元组指针数组）+ Tuple Header（元组头）+ Tuple Data（实际数据）。"
    },
    {
        "id": "D3-4",
        "question": "GaussDB的GPI（Global Partition Index）索引的适用场景是？",
        "options": ["A. 分区表上的全局索引，支持快速全局唯一约束", "B. 单表上的普通B-tree索引", "C. 本地分区索引（每个分区独立索引）", "D. 全文索引"],
        "answer": "A",
        "analysis": "GPI是作用于分区表的全局索引，索引覆盖所有分区数据，支持全局唯一约束和跨分区的快速定位。"
    },
    {
        "id": "D3-5",
        "question": "GaussDB分布式架构下，数据在DN节点间的分布策略是基于？",
        "options": ["A. 轮询（Round-Robin）", "B. Hash分片（分布键Hash）", "C. 范围分片（Range）", "D. 随机分布"],
        "answer": "B",
        "analysis": "GaussDB分布式表通过指定分布列（Distribution Key），对分布列值进行Hash计算，将数据映射到对应DN节点。"
    },
    {
        "id": "D3-6",
        "question": "GaussDB的事务隔离级别中，默认的隔离级别是？",
        "options": ["A. 读未提交（Read Uncommitted）", "B. 读已提交（Read Committed）", "C. 可重复读（Repeatable Read）", "D. 串行化（Serializable）"],
        "answer": "B",
        "analysis": "GaussDB默认隔离级别为读已提交（Read Committed），同时支持读未提交、可重复读和串行化。"
    },
    {
        "id": "D3-7",
        "question": "GaussDB的锁机制中，用于保护数据行不被并发修改的锁是？",
        "options": ["A. AccessShareLock", "B. RowShareLock", "C. RowExclusiveLock", "D. AccessExclusiveLock"],
        "answer": "C",
        "analysis": "RowExclusiveLock是行级排他锁，当事务UPDATE/DELETE一行数据时获取，防止其他事务同时修改该行。"
    },
    {
        "id": "D3-8",
        "question": "GaussDB中，用于管理多版本并发控制（MVCC）的元组可见性判断依据是？",
        "options": ["A. 时间戳", "B. 事务ID（xmin/xmax）比较", "C. 锁状态", "D. 数据版本号"],
        "answer": "B",
        "analysis": "MVCC可见性判断基于元组中的xmin（创建该版本的事务ID）和xmax（删除/更新该版本的事务ID）与当前事务快照的比较。"
    },
    {
        "id": "D3-9",
        "question": "GaussDB的UStore引擎采用什么机制来管理老版本数据？",
        "options": ["A. 在元组中保留所有历史版本", "B. 定时清理老版本", "C. 将老版本写入WAL日志", "D. 将老版本统一存储到Undo Zone中分离管理"],
        "answer": "D",
        "analysis": "UStore新老版本分离，新版本就地更新，老版本统一存储在Undo Zone中，由Undo模块集中管理。"
    },
    {
        "id": "D3-10",
        "question": "GaussDB的DB4AI特性提供的主要能力是？",
        "options": ["A. 自动索引推荐", "B. SQL自动改写", "C. 数据库内嵌AI算法执行，支持模型训练和推理", "D. 智能故障诊断"],
        "answer": "C",
        "analysis": "DB4AI（Database for AI）将AI算法内置到数据库中，支持在SQL中直接执行模型训练、预测推理等AI任务，无需数据导出。"
    },
    {
        "id": "D3-11",
        "question": "GaussDB在执行计划中，通过算子下推（Pushdown）实现的主要优化目的是？",
        "options": ["A. 减少SQL解析时间", "B. 将计算下推到存储节点就近执行，减少网络数据传输", "C. 减少索引开销", "D. 提高日志写入速度"],
        "answer": "B",
        "analysis": "算子下推将过滤、投影等操作下推到DN执行，减少CN-DN间的数据传输量，是分布式场景的核心优化手段。"
    },
    {
        "id": "D3-12",
        "question": "GaussDB的DCF（Distributed Consensus Framework）组件主要功能是？",
        "options": ["A. 基于Paxos协议实现分布式一致性选举和日志复制", "B. 事务并发控制", "C. SQL解析", "D. 数据加密"],
        "answer": "A",
        "analysis": "DCF基于Paxos协议实现主节点选举、日志强同步复制和集群一致性管理，是分布式高可用的基础组件。"
    }
]

CH3_MULTI = [
    {
        "id": "M3-1",
        "question": "GaussDB SQL引擎由以下哪些模块组成？",
        "options": ["A. 解析器（Parser）", "B. 优化器（Optimizer）", "C. 执行器（Executor）", "D. 事务管理器（Transaction Manager）", "E. 日志管理器（Log Manager）"],
        "answer": "ABC",
        "analysis": "SQL引擎三大模块：解析器（词法/语法分析→解析树）、优化器（逻辑/物理优化→执行计划）、执行器（执行计划解释执行）。事务/日志管理器属于存储引擎层。"
    },
    {
        "id": "M3-2",
        "question": "GaussDB优化器的核心优化技术包括？",
        "options": ["A. 基于代价的优化（CBO）", "B. 统计信息驱动", "C. 子查询/子链接优化", "D. SMP多核并行执行", "E. Plan Hint/SQL Patch干预"],
        "answer": "ABCDE",
        "analysis": "GaussDB优化器采用CBO，依赖统计信息估算代价，支持子查询优化（SubLink提升等）、SMP并行、通过Plan Hint/SQL Patch干预执行计划。"
    },
    {
        "id": "M3-3",
        "question": "GaussDB支持的索引类型包括？",
        "options": ["A. B-tree索引", "B. GSI（Global Secondary Index）", "C. GPI（Global Partition Index）", "D. Local分区索引", "E. 表达式索引"],
        "answer": "ABCDE",
        "analysis": "GaussDB支持多种索引类型，B-tree为基础索引，GSI/GPI支持分布式/分区场景，Local索引每个分区独立，表达式索引支持函数索引。"
    },
    {
        "id": "M3-4",
        "question": "GaussDB的日志管理机制包括以下哪些？",
        "options": ["A. WAL（Write Ahead Log）日志", "B. Undo日志", "C. Redo日志", "D. 逻辑复制日志", "E. Binlog日志"],
        "answer": "ABCD",
        "analysis": "GaussDB采用WAL机制（预写日志），包含Redo日志（前向恢复）和Undo日志（MVCC/回滚），以及逻辑复制日志。Binlog是MySQL的日志机制。"
    },
    {
        "id": "M3-5",
        "question": "GaussDB中，可能导致执行计划跳变（Plan Regression）的原因包括？",
        "options": ["A. 统计信息变更", "B. 系统参数调整", "C. 数据分布变化", "D. 索引新增或删除", "E. 数据库版本升级"],
        "answer": "ABCDE",
        "analysis": "执行计划跳变是优化器代价估算受各种因素影响导致计划选择变化。SPM（SQL Plan Management）可管理计划稳定性。"
    },
    {
        "id": "M3-6",
        "question": "GaussDB DBMind智能运维平台的核心能力包括？",
        "options": ["A. 慢SQL根因分析", "B. 索引推荐", "C. 性能容量预测", "D. 趋势分析和异常检测", "E. 自动数据备份"],
        "answer": "ABCD",
        "analysis": "DBMind覆盖SQL诊断优化、容量预测、异常检测等智能运维场景；备份管理由独立模块负责。"
    }
]

# ---------- 第四章：安全管理 ----------
CH4_JUDGE = [
    {
        "id": "J4-1",
        "question": "GaussDB的三权分立模式将数据库管理员权限拆分为系统管理员、安全管理员和审计管理员三个角色。",
        "answer": "√",
        "analysis": "三权分立将传统DBA权限拆分为三个独立角色，实现权限制衡：系统管理员管运维、安全管理员管安全策略、审计管理员管审计。"
    },
    {
        "id": "J4-2",
        "question": "GaussDB的审计日志中包含被审计操作涉及的具体数据内容。",
        "answer": "×",
        "analysis": "审计日志记录操作行为（谁、何时、做了什么），不记录数据内容，防止审计日志本身成为敏感数据泄露渠道。"
    },
    {
        "id": "J4-3",
        "question": "GaussDB透明数据加密（TDE）的加密发生在数据库驱动层。",
        "answer": "×",
        "analysis": "TDE加密在存储引擎层实现，对上层应用完全透明。加密函数在SQL引擎层，全密态加密在数据库驱动层。"
    },
    {
        "id": "J4-4",
        "question": "GaussDB的动态脱敏功能是实时的，在查询结果返回前对敏感数据进行脱敏处理。",
        "answer": "√",
        "analysis": "动态脱敏在SQL执行结果返回客户端前实时进行脱敏，不影响底层数据存储，对业务系统透明。"
    },
    {
        "id": "J4-5",
        "question": "GaussDB的RLS（Row-Level Security）行级访问控制策略在表级别配置，影响所有用户。",
        "answer": "×",
        "analysis": "RLS基于用户/角色配置行级访问策略，不同用户执行相同SQL可见的数据行不同，可以通过策略指定影响范围（不一定是所有用户）。"
    }
]

CH4_SINGLE = [
    {
        "id": "D4-1",
        "question": "GaussDB的三权分立模型中，哪个角色负责创建和维护数据库用户？",
        "options": ["A. 系统管理员（System Admin）", "B. 安全管理员（Security Admin）", "C. 审计管理员（Audit Admin）", "D. 数据库所有者（Owner）"],
        "answer": "A",
        "analysis": "三权分立中，系统管理员负责日常运维和用户创建；安全管理员负责安全策略配置；审计管理员负责审计日志查看和管理。"
    },
    {
        "id": "D4-2",
        "question": "GaussDB的透明加密（TDE）支持的加密算法是？",
        "options": ["A. MD5", "B. AES-256", "C. DES", "D. RC4"],
        "answer": "B",
        "analysis": "TDE支持AES-256国密算法（SM4），在存储引擎层对数据文件进行实时加密和解密。"
    },
    {
        "id": "D4-3",
        "question": "GaussDB的PASSWORD参数配置中，password_policy参数设置为2时表示？",
        "options": ["A. 无密码复杂度要求", "B. 仅验证密码长度", "C. 启用复杂密码检查（包含大写、小写、数字、特殊字符）", "D. 启用密码有效期检查"],
        "answer": "C",
        "analysis": "password_policy=2时启用复杂密码策略，要求密码必须包含大写字母、小写字母、数字、特殊字符中的至少3类。"
    },
    {
        "id": "D4-4",
        "question": "GaussDB的防篡改账本功能中，用于存储历史变化信息的表是？",
        "options": ["A. 用户表（User Table）", "B. 历史表（History Table）", "C. 全局表（Global Table）", "D. 审计表（Audit Table）"],
        "answer": "B",
        "analysis": "防篡改账本机制中，历史表记录用户表每一行数据的变更历史（Hash链），全局表存储所有防篡改表的全局信息。"
    },
    {
        "id": "D4-5",
        "question": "GaussDB统一审计（Unified Audit）相比传统审计的主要优势是？",
        "options": ["A. 更快的审计日志写入", "B. 更低的存储开销", "C. 更简单的配置", "D. 支持按用户、IP、时间等条件灵活组合的策略配置"],
        "answer": "D",
        "analysis": "统一审计通过CREATE AUDIT POLICY创建灵活的审计策略，可按操作类型、用户、IP地址、客户端类型、时间等条件组合定义审计范围。"
    },
    {
        "id": "D4-6",
        "question": "GaussDB全密态加密方案中，密钥的管理由谁负责？",
        "options": ["A. 数据库内核", "B. 操作系统", "C. 客户端驱动", "D. 第三方CA"],
        "answer": "C",
        "analysis": "全密态方案中密钥由客户端驱动管理和保存，数据库端仅存储加密后的密文数据，无法解密。"
    }
]

CH4_MULTI = [
    {
        "id": "M4-1",
        "question": "GaussDB安全架构包含以下哪些层次？",
        "options": ["A. 访问控制（用户认证、权限管理）", "B. 数据加密（TDE、全密态）", "C. 审计与合规（审计日志、统一审计）", "D. 数据脱敏（动态脱敏）", "E. 防篡改（账本数据库）"],
        "answer": "ABCDE",
        "analysis": "GaussDB构建了覆盖事前（访问控制）、事中（加密/脱敏/防篡改）、事后（审计）的全维度安全体系。"
    },
    {
        "id": "M4-2",
        "question": "GaussDB基于角色的访问控制（RBAC）中，以下说法正确的有？",
        "options": ["A. 用户和角色可以互相转换", "B. 角色可以嵌套继承权限", "C. Public角色是所有用户默认拥有的角色", "D. 角色不能登录数据库", "E. 角色只能包含权限，不能包含用户"],
        "answer": "ABC",
        "analysis": "在GaussDB中，用户是带LOGIN权限的角色；角色可以嵌套继承；Public角色对每个用户生效。D错误（角色可登录），E错误（角色可包含用户）。"
    },
    {
        "id": "M4-3",
        "question": "GaussDB透明加密TDE的密钥体系中包含的密钥层级有？",
        "options": ["A. 主密钥（Master Key）", "B. 表密钥（Table Key）", "C. 数据加密密钥（DEK）", "D. 用户密钥（User Key）", "E. 会话密钥（Session Key）"],
        "answer": "ABC",
        "analysis": "TDE多层密钥体系：CMK（主密钥）加密TDEK（表加密密钥），TDEK加密DEK（数据加密密钥），DEK加密实际数据。"
    },
    {
        "id": "M4-4",
        "question": "GaussDB支持的敏感数据发现和脱敏技术包括？",
        "options": ["A. 预置敏感数据类型发现", "B. 数据分类分级", "C. 动态脱敏策略", "D. 预置脱敏函数", "E. 按用户配置脱敏策略"],
        "answer": "ACDE",
        "analysis": "GaussDB提供预置敏感数据发现函数（如email、身份证、手机号等），支持动态脱敏策略和预置脱敏函数（MASK_FULL、MASK_PARTIAL等）。"
    },
    {
        "id": "M4-5",
        "question": "GaussDB的账号安全管理策略包括？",
        "options": ["A. 密码有效期设置", "B. 账号锁定策略（失败登录次数限制）", "C. 密码复杂度检查", "D. 密码重用策略", "E. 短信二次认证"],
        "answer": "ABCD",
        "analysis": "GaussDB内置密码策略包括有效期、复杂度、重用机制和账号锁定功能，但不包含短信二次认证（此为应用层能力）。"
    }
]

# ---------- 第五章：性能调优 ----------
CH5_JUDGE = [
    {
        "id": "J5-1",
        "question": "GaussDB中，系统视图pg_stat_activity可用于查看当前数据库连接和正在执行的SQL状态。",
        "answer": "√",
        "analysis": "pg_stat_activity是GaussDB性能分析的常用视图，可查看当前连接、运行SQL、等待事件、事务状态等关键信息。"
    },
    {
        "id": "J5-2",
        "question": "GaussDB中，SMP（Symmetrical Multi-Processing）并行执行技术默认在所有查询中开启。",
        "answer": "×",
        "analysis": "SMP需要根据CPU资源和查询复杂度手动配置（通过query_dop参数），仅在分析型复杂查询中启用，不适合短事务和低并发场景。"
    },
    {
        "id": "J5-3",
        "question": "GaussDB的WDR（Workload Diagnosis Report）报告基于两个时间点的快照生成性能对比分析。",
        "answer": "√",
        "analysis": "WDR通过采集两个AWR快照之间的性能数据进行对比分析，生成包括SQL统计、等待事件、系统负载等维度的性能诊断报告。"
    },
    {
        "id": "J5-4",
        "question": "GaussDB中使用analyze命令可以收集表的统计信息，帮助优化器生成更好的执行计划。",
        "answer": "√",
        "analysis": "ANALYZE收集表的数据分布统计信息（行数、列值分布、空值率等），优化器基于统计信息估算代价，是SQL性能调优的基础操作。"
    },
    {
        "id": "J5-5",
        "question": "GaussDB中，当查询使用子查询时，优化器总是会将子查询提升为表连接来提升性能。",
        "answer": "×",
        "analysis": "优化器会尝试子查询提升（SubLink提升），但并非所有子查询都能提升，相关子查询、含聚合函数的子查询等场景可能无法提升。"
    }
]

CH5_SINGLE = [
    {
        "id": "D5-1",
        "question": "GaussDB中，查看SQL执行计划应使用哪个关键字？",
        "options": ["A. SHOW PLAN FOR", "B. EXPLAIN", "C. DESCRIBE", "D. DISPLAY"],
        "answer": "B",
        "analysis": "GaussDB使用EXPLAIN关键字查看执行计划，EXPLAIN ANALYZE可输出实际的执行时间和行数统计。"
    },
    {
        "id": "D5-2",
        "question": "以下哪种情况不适合使用GaussDB的SMP并行执行？",
        "options": ["A. 高频短查询（小事务）", "B. 大表的OLAP分析查询", "C. 复杂多表关联查询", "D. 分区表的全分区扫描"],
        "answer": "A",
        "analysis": "SMP并行适合耗时较长的复杂分析型查询和CPU密集型计算，不适合高频短事务（并行调度的开销超过收益）。"
    },
    {
        "id": "D5-3",
        "question": "GaussDB中，WDR报告的性能诊断数据来源是？",
        "options": ["A. syslog系统日志", "B. ASP（Active Session Profile）和历史快照", "C. pg_stat_statements视图", "D. 审计日志"],
        "answer": "B",
        "analysis": "WDR基于ASP的活跃会话采样和定期性能快照（Snapshot）生成报告，提供时间段内的性能对比分析。"
    },
    {
        "id": "D5-4",
        "question": "GaussDB中，用于实时采集活跃会话等待事件信息的组件是？",
        "options": ["A. pg_stat_activity", "B. WDR", "C. gs_asp（Active Session Profile）", "D. pg_stat_statements"],
        "answer": "C",
        "analysis": "gs_asp定时采样活跃会话的等待事件、SQL ID、状态等信息，是WDR报告的数据源，也是实时性能分析的关键工具。"
    },
    {
        "id": "D5-5",
        "question": "GaussDB驱动参数中，用于控制批量提交的优化参数是？",
        "options": ["A. fetchSize", "B. batchMode", "C. autoBalance", "D. loginTimeout"],
        "answer": "B",
        "analysis": "batchMode开启后，驱动将多条INSERT语句合并为批量提交，减少网络交互次数，显著提升批量写入性能。"
    },
    {
        "id": "D5-6",
        "question": "GaussDB中，用于控制SQL语句是否使用DN轻量化执行计划的参数属于？",
        "options": ["A. query_dop", "B. rewrite_rule", "C. explain_perf_mode", "D. sql_beta_feature（包含enable_sql_bypass等）"],
        "answer": "D",
        "analysis": "enable_sql_bypass参数（属于sql_beta_feature）控制是否启用SQL Bypass轻量化执行计划。"
    },
    {
        "id": "D5-7",
        "question": "GaussDB性能调优中，执行计划显示\"Seq Scan\"算子的含义是？",
        "options": ["A. 索引扫描", "B. 全表顺序扫描", "C. 位图扫描", "D. 索引只扫描"],
        "answer": "B",
        "analysis": "Seq Scan（顺序扫描）表示全表扫描，通常发生在没有可用索引或优化器认为全表扫描代价更低时，大表全表扫描往往是SQL慢的根因。"
    },
    {
        "id": "D5-8",
        "question": "GaussDB中，查看表统计信息是否过旧可以通过查询哪个视图来判断？",
        "options": ["A. pg_class（reltuples、relpages字段）", "B. pg_stat_activity", "C. pg_tables", "D. pg_index"],
        "answer": "A",
        "analysis": "pg_class的reltuples（估算行数）和relpages（占用页面数）反映统计信息状态，若与实际值偏差大说明统计信息过旧。"
    },
    {
        "id": "D5-9",
        "question": "GaussDB中，PLAN HINT用于实现什么功能？",
        "options": ["A. 修改SQL语义", "B. 指定数据加密方式", "C. 强制优化器选择指定的执行路径", "D. 设置事务隔离级别"],
        "answer": "C",
        "analysis": "PLAN HINT通过在SQL中添加/*+ hint */注释，强制优化器使用指定索引、Join顺序或Join方式，用于干预优化器的计划选择。"
    },
    {
        "id": "D5-10",
        "question": "以下哪项不是GaussDB性能监控的关键等待事件类别？",
        "options": ["A. LWLock（轻量级锁等待）", "B. IO等待（数据文件读写）", "C. 网络等待（数据跨节点传输）", "D. CPU空闲等待"],
        "answer": "D",
        "analysis": "CPU空闲不视为等待事件。GaussDB关键等待事件包括LWLock、IO、网络、CLOG等。"
    }
]

CH5_MULTI = [
    {
        "id": "M5-1",
        "question": "GaussDB性能调优的总体思路包括哪些步骤？",
        "options": ["A. 识别性能瓶颈（OS、数据库、SQL各层面）", "B. 通过监控工具（TPOPS/DBMind）定位问题", "C. 分析等待事件和执行计划", "D. 制定优化方案（SQL改写、索引优化、参数调整）", "E. 验证优化效果并持续监控"],
        "answer": "ABCDE",
        "analysis": "性能调优遵循\"发现→分析→优化→验证\"的闭环流程，涉及OS、数据库、SQL多层面。"
    },
    {
        "id": "M5-2",
        "question": "GaussDB中，可通过以下哪些手段干预和优化SQL执行计划？",
        "options": ["A. 通过ANALYZE更新统计信息", "B. 使用PLAN HINT强制指定计划", "C. 使用SQL Patch在线修改执行计划", "D. 调整rewrite_rule重写规则", "E. 使用ALTER TABLE修改表结构"],
        "answer": "ABCD",
        "analysis": "A-D均为执行计划干预手段。E（改表结构）影响范围过大，通常不作为执行计划干预手段。"
    },
    {
        "id": "M5-3",
        "question": "GaussDB内存参数优化中，以下哪些参数影响查询性能？",
        "options": ["A. shared_buffers", "B. work_mem", "C. maintenance_work_mem", "D. wal_buffers", "E. max_process_memory"],
        "answer": "ABCDE",
        "analysis": "shared_buffers（共享缓冲区）、work_mem（排序/哈希内存）、maintenance_work_mem（维护操作内存）、wal_buffers（WAL缓冲区）、max_process_memory（最大内存上限）均直接影响查询执行效率。"
    },
    {
        "id": "M5-4",
        "question": "GaussDB中，导致SQL查询慢的常见原因包括？",
        "options": ["A. 缺少合适索引导致全表扫描", "B. 统计信息过旧导致执行计划不佳", "C. 数据倾斜导致分布式节点负载不均", "D. 锁冲突导致SQL等待", "E. 不合理的Join顺序"],
        "answer": "ABCDE",
        "analysis": "SQL慢的根因分析需从索引、统计信息、数据分布、锁、执行计划多维度排查。"
    },
    {
        "id": "M5-5",
        "question": "GaussDB中，通过火焰图（Flame Graph）进行性能分析的优点包括？",
        "options": ["A. 可视化展示CPU热点函数调用堆栈", "B. 快速定位CPU密集型代码路径", "C. 支持perf和gs_stack数据源", "D. 直观显示函数调用频次和耗时占比", "E. 自动给出优化建议"],
        "answer": "ABCD",
        "analysis": "火焰图可视化CPU热点，帮助定位性能瓶颈点，但需要人工分析优化建议，不自带优化建议。"
    }
]

# ---------- 第六章：运维与故障处理 ----------
CH6_JUDGE = [
    {
        "id": "J6-1",
        "question": "GaussDB在线扩容期间对业务影响控制在5%以内。",
        "answer": "√",
        "analysis": "HashBucket在线扩容技术支持在线迁移数据，扩容期间平均吞吐量和平均延时影响小于5%。"
    },
    {
        "id": "J6-2",
        "question": "GaussDB的PITR（Point-In-Time Recovery）基于全量备份+WAL归档日志实现任意时间点恢复。",
        "answer": "√",
        "analysis": "PITR利用全量备份恢复基础数据，结合WAL归档日志重放到指定时间点，实现精细粒度的按时间点恢复。"
    },
    {
        "id": "J6-3",
        "question": "GaussDB同城双集群容灾方案中，两个集群均可同时提供读写服务。",
        "answer": "×",
        "analysis": "同城双集群为主备关系，主集群提供读写服务，备集群通过增量日志同步保持数据一致，通常仅提供只读服务（或作为灾备不对外服务）。"
    },
    {
        "id": "J6-4",
        "question": "GaussDB的闪回DROP功能可以将已删除的表从系统回收站中恢复。",
        "answer": "√",
        "analysis": "UStore引擎支持闪回DROP和闪回TRUNCATE，删除的表暂存于系统回收站，可通过TIMESTAMP或CSN闪回恢复。"
    },
    {
        "id": "J6-5",
        "question": "GaussDB灰度升级允许在集群节点间分批升级，支持在线回退。",
        "answer": "√",
        "analysis": "灰度升级逐个节点滚动升级，每个节点升级完成后业务自动切换到其他节点，升级失败可在线回退到升级前版本。"
    }
]

CH6_SINGLE = [
    {
        "id": "D6-1",
        "question": "GaussDB集群DN节点多数派故障时，应采取的恢复措施是？",
        "options": ["A. 强制重启集群", "B. 停止集群后使用gs_ctl重建故障DN", "C. 直接删除故障节点", "D. 忽略故障继续运行"],
        "answer": "B",
        "analysis": "DN多数派故障会导致集群不可用，需停止集群后使用gs_ctl工具重建故障DN数据目录，重新拉齐数据。"
    },
    {
        "id": "D6-2",
        "question": "GaussDB中，当数据库进入只读状态（Read-Only）时的常见原因是？",
        "options": ["A. 配置错误", "B. 网络故障", "C. 磁盘空间满（DN数据盘使用率超阈值）", "D. 密码过期"],
        "answer": "C",
        "analysis": "GaussDB自动将数据库置为只读状态通常是因为DN数据盘使用率超过阈值（默认85%），触发只读保护机制。"
    },
    {
        "id": "D6-3",
        "question": "GaussDB流复制中，如果主机发送WAL日志的速度超过备机回放速度，可能导致的后果是？",
        "options": ["A. 主机宕机", "B. 备机宕机", "C. 数据丢失", "D. 主备复制延迟增大，可能触发流控"],
        "answer": "D",
        "analysis": "主机日志发送速率超过备机回放能力时，复制延迟持续增大，GaussDB通过流控机制限制主机的日志发送速率，防止备机被\"淹\"。"
    },
    {
        "id": "D6-4",
        "question": "GaussDB的CSS（Cluster Startup Service）集群启动服务的主要功能是？",
        "options": ["A. 管理集群启动流程，确保各组件按正确顺序启动", "B. SQL解析", "C. 数据加密", "D. 监控磁盘"],
        "answer": "A",
        "analysis": "CSS负责集群启动管理和组件启动顺序控制，是GaussDB集群管理的重要组件。"
    },
    {
        "id": "D6-5",
        "question": "GaussDB逻辑备份工具是？",
        "options": ["A. pg_dump", "B. pg_dumpall", "C. gs_dump", "D. copy"],
        "answer": "C",
        "analysis": "gs_dump是GaussDB的逻辑备份工具，导出数据库对象的SQL定义和数据。pg_dump是PostgreSQL原生工具，GaussDB兼容但不推荐。"
    },
    {
        "id": "D6-6",
        "question": "GaussDB中，CPU 100%问题的应急处理第一步通常是？",
        "options": ["A. 重启数据库", "B. 通过top/gs_session统计定位消耗CPU的会话和SQL", "C. 扩容CPU", "D. 清理日志"],
        "answer": "B",
        "analysis": "CPU 100%需先定位源头：通过top找到高CPU进程，关联gs_session/wait_event找到对应SQL，然后分析SQL是否可优化或kill问题会话。"
    },
    {
        "id": "D6-7",
        "question": "GaussDB中，gs_stack工具的作用是？",
        "options": ["A. 打印指定线程的内核态堆栈信息", "B. 查看系统表", "C. 查看数据文件", "D. 检查备份状态"],
        "answer": "A",
        "analysis": "gs_stack打印数据库线程的堆栈信息，用于分析线程卡住、死锁、hang等问题场景。"
    },
    {
        "id": "D6-8",
        "question": "GaussDB的流式容灾（异地）与同城双集群容灾的主要区别是？",
        "options": ["A. 流式容灾不需要网络连接", "B. 流式容灾基于WAL日志异步传输，RPO大于0；同城双集群基于同步复制RPO=0", "C. 流式容灾性能更好", "D. 同城双集群不支持故障切换"],
        "answer": "B",
        "analysis": "流式容灾通过WAL日志异步传输实现异地容灾，RPO>0；同城双集群采用同步复制确保RPO=0。"
    },
    {
        "id": "D6-9",
        "question": "GaussDB升级中，需要中断业务进行升级的方式是？",
        "options": ["A. 滚动升级", "B. 就地升级", "C. 灰度升级", "D. 热补丁升级"],
        "answer": "B",
        "analysis": "就地升级需停止数据库服务进行升级，业务中断时间长。滚动/灰度升级支持在线逐节点升级。热补丁升级无需重启。"
    },
    {
        "id": "D6-10",
        "question": "GaussDB备机I/O异常时，首先应排查的根因是？",
        "options": ["A. 备机磁盘硬件故障或磁盘I/O压力过大", "B. 主机性能不足", "C. 网络带宽不足", "D. 内存不足"],
        "answer": "A",
        "analysis": "备机I/O异常应首先排查备机自身的磁盘健康状况和I/O负载，如磁盘坏道、RAID卡故障、I/O队列堆积等。"
    }
]

CH6_MULTI = [
    {
        "id": "M6-1",
        "question": "GaussDB的\"五类问题\"（慢、满、错、hang、宕）的定位处理方法论包括？",
        "options": ["A. 慢：定位慢SQL，分析执行计划，优化索引/参数", "B. 满：检查磁盘、内存使用率，清理/扩容", "C. 错：检查错误日志，分析错误码，回滚/修复", "D. hang：查看锁等待、线程堆栈，分析死锁", "E. 宕：查看coredump、系统日志，分析宕机根因"],
        "answer": "ABCDE",
        "analysis": "GaussDB运维五类问题各有针对性的定位方法和管理手段。"
    },
    {
        "id": "M6-2",
        "question": "GaussDB支持的主要升级方式包括？",
        "options": ["A. 就地升级（业务中断）", "B. 灰度升级（在线逐节点）", "C. 滚动升级（在线逐节点）", "D. 热补丁升级（无需重启）", "E. 全量重装升级"],
        "answer": "ABCD",
        "analysis": "A-D是GaussDB标准升级方式，全量重装属于极端恢复手段，不是升级方式。"
    },
    {
        "id": "M6-3",
        "question": "GaussDB集群只读问题的处理步骤包括？",
        "options": ["A. 确认只读状态：查询pg_sessions/df -h确认磁盘使用", "B. 清理空间：删除临时文件/清理过期WAL/truncate历史表", "C. 扩容存储：添加新磁盘或扩容数据目录", "D. 确认集群退出只读状态", "E. 重启数据库"],
        "answer": "ABCD",
        "analysis": "只读状态通常不需要重启数据库，清理/扩容后自动退出只读保护。重启可作为最后手段但不是必选步骤。"
    },
    {
        "id": "M6-4",
        "question": "GaussDB常见的锁问题包括？",
        "options": ["A. 锁超时（LockTimeout）", "B. 死锁（Deadlock）", "C. 锁阻塞链阻塞", "D. 行锁丢失", "E. 锁等待导致业务堆积"],
        "answer": "ABCE",
        "analysis": "GaussDB会自动检测死锁并回滚其中一个事务解决死锁。锁阻塞链可通过pg_locks/pg_sessions定位。\"行锁丢失\"不是标准问题类型。"
    },
    {
        "id": "M6-5",
        "question": "GaussDB同城双集群容灾方案的特点包括？",
        "options": ["A. 同城两个集群间通过同步复制实现RPO=0", "B. 两个集群同时提供读写服务", "C. 主集群故障时备集群可自动/手动切换接管", "D. 主备集群间通过DW/DWS专线连接，时延<2ms", "E. 仅支持主集群到备集群的单向复制"],
        "answer": "ACDE",
        "analysis": "同城双集群为主备关系，B错误（备集群不提供读写服务）。A正确（同步复制RPO=0）、C正确、D正确、E正确。"
    },
    {
        "id": "M6-6",
        "question": "GaussDB基于WAL日志备份的PITR恢复流程包括？",
        "options": ["A. 使用全量备份文件恢复数据库基本状态", "B. 应用WAL归档日志推进到目标时间点", "C. 数据库打开后验证数据完整性", "D. 重建索引", "E. 重新配置参数"],
        "answer": "ABC",
        "analysis": "PITR流程：全量恢复→WAL日志回放到指定时间点（通过recovery_target_time参数）→数据库open验证。"
    }
]

# ---------- 第一章补充题 ----------
CH1_JUDGE_EXT = [
    {
        "id": "J1-6",
        "question": "GaussDB集中式架构中，节点间通过IB（InfiniBand）高速互连。",
        "answer": "√",
        "analysis": "集中式节点间采用IB高速互连，IB网络具备低时延、高带宽特性，适用于集中式架构的节点间通信。"
    },
    {
        "id": "J1-7",
        "question": "HCS形态下，GaussDB仅能部署在裸金属服务器上。",
        "answer": "×",
        "analysis": "GaussDB在HCS形态下不仅可部署在裸金属服务器，还支持部署在弹性云服务器（ECS）上，支持裸金属、虚拟化多种部署方式。"
    },
    {
        "id": "J1-8",
        "question": "GaussDB采用单进程多线程架构，相比多进程架构，线程启动开销更小。",
        "answer": "√",
        "analysis": "单进程多线程架构的优势：线程启动/切换开销小、线程间通信便捷（共享内存）、支持NUMA绑核优化。"
    },
    {
        "id": "J1-9",
        "question": "GaussDB仅支持AStore和UStore行存引擎，不支持列存或时序存储引擎。",
        "answer": "×",
        "analysis": "GaussDB除AStore和UStore行存引擎外，还支持LSM-tree列存引擎（用于时序场景和OLAP分析）。"
    }
]

CH1_SINGLE_EXT = [
    {
        "id": "D1-11",
        "question": "GaussDB单节点最大tpmC性能指标为？",
        "options": ["A. 100万", "B. 150万", "C. 200万", "D. 500万"],
        "answer": "B",
        "analysis": "GaussDB自研内核优化后，单节点最大tpmC性能指标为150万。"
    },
    {
        "id": "D1-12",
        "question": "GaussDB分布式架构32节点最大tpmC性能指标为？",
        "options": ["A. 1000万", "B. 1500万", "C. 2000万", "D. 3000万"],
        "answer": "B",
        "analysis": "GaussDB分布式架构支持性能线性扩容，32节点最大tpmC可达1500万。"
    },
    {
        "id": "D1-13",
        "question": "GaussDB的CN轻量化执行计划中，判断SQL是否满足轻量化执行条件的依据是？",
        "options": ["A. 语法解析阶段的模式识别", "B. 优化器的代价估算结果", "C. 执行器的运行时反馈", "D. 用户手动指定"],
        "answer": "A",
        "analysis": "SQL Bypass在语法解析（parse）层完成模式识别，判断SQL是否满足轻量化执行条件，直接调用存储接口跳过经典执行器框架。"
    },
    {
        "id": "D1-14",
        "question": "某表有2000万行数据，每行实际占用100字节，页面填充因子100%。使用AStore引擎，页面大小8KB（页面头40B，元组指针4B，元组头24B），估算该表数据文件大小约为？",
        "options": ["A. 1.2GB", "B. 2.5GB", "C. 3.8GB", "D. 5.1GB"],
        "answer": "C",
        "analysis": "单条总占用=4+24+100=128B；单页可用=8192-40=8152B；单页行数=8152÷128≈63行；总页数=2000万÷63≈317460页；总大小=317460×8192B≈3.8GB。"
    }
]

CH1_MULTI_EXT = [
    {
        "id": "M1-6",
        "question": "GaussDB单进程多线程架构的优势包括？",
        "options": ["A. 线程启动开销小", "B. 线程间通信便捷（共享内存）", "C. 线程切换开销低", "D. 支持NUMA绑核优化", "E. 可避免线程间的内存泄漏"],
        "answer": "ABCD",
        "analysis": "多线程优势：启动/切换开销小、共享内存通信快、支持NUMA绑核。内存泄漏防护是内存上下文管理的功能，非多线程架构直接优势。"
    },
    {
        "id": "M1-7",
        "question": "GaussDB的CN轻量化执行计划（SQL Bypass）的优势包括？",
        "options": ["A. 直接下发语句到DN执行，无需经过优化器", "B. 减少CN节点计算压力", "C. 执行延迟低", "D. 支持复杂分布式查询", "E. 降低内存消耗"],
        "answer": "ABCE",
        "analysis": "CN轻量化执行计划跳过优化器，直接下发简单SQL到DN，减少CN压力、降低延迟和内存消耗。不支持复杂分布式查询（D错误）。"
    },
    {
        "id": "M1-8",
        "question": "GaussDB支持的存储引擎类型包括？",
        "options": ["A. AStore行存引擎", "B. UStore行存引擎", "C. InnoDB引擎", "D. MyISAM引擎", "E. LSM-tree列存引擎"],
        "answer": "ABE",
        "analysis": "GaussDB自研核心存储引擎为AStore和UStore，同时支持LSM-tree列存引擎。InnoDB和MyISAM是MySQL的存储引擎。"
    }
]

# ============================================================
# PDF参考资料补充题目（根据考试回忆题目整理）
# ============================================================

CH2_JUDGE_EXT = [
    {
        "id": "J2-6",
        "question": "容量规划完成后，可以直接进入实施阶段，无需再进行详细设计和方案评审。",
        "answer": "×",
        "analysis": "容量规划完成后，还需要进行详细设计（包括网络规划、安全规划等）、方案评审等多个阶段，才能进入实施阶段。容量规划只是数据库规划设计中的一个环节。"
    },
    {
        "id": "J2-7",
        "question": "GaussDB集中式部署形态适合SQL复杂、存量存储过程较多且数据量小于2TB的场景。",
        "answer": "√",
        "analysis": "集中式部署适用于：SQL复杂（涉及大量JOIN/子查询）、存量存储过程多、数据量<2TB的场景；而分布式适合大容量(>=2TB)、高并发场景。"
    },
    {
        "id": "J2-8",
        "question": "新建Region建议采用增强型裸机网关，存量Region建议继续使用集中式裸机网关。",
        "answer": "√",
        "analysis": "增强型裸机网关具备线速转发、硬件级高可用、多平面隔离的优势，新建Region建议采用；存量Region因兼容限制继续使用集中式裸机网关。"
    }
,
    {
        "id": "J2-9",
        "question": "GaussDB性能稳定是选择集中式部署形态的理由，不是选择分布式的理由。",
        "answer": "×",
        "analysis": "集中式和分布式均可实现性能稳定。性能稳定不是区分两者的依据，集中式的优势在于SQL复杂、存储过程多、改造困难等场景。"
    }
,
    {
        "id": "D2-15",
        "question": "HCS集中式裸机网关三层互通IP规划中，每个DN节点分配的业务虚IP（VIP）个数为？",
        "options": ["A. 1个", "B. 2个", "C. 3个", "D. 按需分配"],
        "answer": "A",
        "analysis": "HCS集中式裸机网关三层互通规划中，每个DN节点仅分配1个业务虚IP（VIP），VIP随主节点漂移。"
    }
,
    {
        "id": "D2-16",
        "question": "在GaussDB计算资源容量规划中，金融核心业务的复杂度折算系数通常？",
        "options": ["A. 小于1", "B. 等于1", "C. 大于1（常见1.2-1.5）", "D. 无固定系数"],
        "answer": "C",
        "analysis": "金融核心业务交易逻辑复杂，复杂度折算系数通常大于1（常见1.2-1.5），用于估算实际CPU需求。"
    }
,
    {
        "id": "D2-17",
        "question": "GaussDB安全规划中，应用层安全建议采用的SQL审核工具是？",
        "options": ["A. UGO工具", "B. DRS工具", "C. DBS工具", "D. OBS工具"],
        "answer": "A",
        "analysis": "应用层安全推荐采用UGO工具进行SQL审核，UGO提供SQL审核和优化建议。"
    }
]

CH2_SINGLE_EXT = [
    {
        "id": "D2-13",
        "question": "某企业数据量小于24TB，TPS小于20000，SQL逻辑较复杂，应选择哪种部署方案？",
        "options": ["A. 分布式三节点", "B. 集中式一主一备", "C. 分布式六节点", "D. 集中式一主多备"],
        "answer": "B",
        "analysis": "单节点<24TB、tps<20000、SQL复杂的场景适合集中式部署。一主一备提供基本高可用保护。"
    },
    {
        "id": "D2-14",
        "question": "GaussDB数据库规划设计中，tpmC换算主要用于评估以下哪个方面的容量？",
        "options": ["A. 存储容量", "B. 网络带宽", "C. 服务器处理能力", "D. 内存大小"],
        "answer": "C",
        "analysis": "tpmC（Transaction Processing Benchmark C）是衡量服务器在线事务处理能力的基准指标，用于评估CPU处理能力和服务器规格选型。"
    },
    {
        "id": "D3-16",
        "question": "关于GaussDB的Checkpointer检查点机制，以下说法正确的是？",
        "options": ["A. Checkpointer仅支持全量检查点", "B. Checkpointer同时支持增量检查点和全量检查点", "C. Checkpointer仅支持增量检查点", "D. 检查点由用户线程触发，无需Checkpointer进程"],
        "answer": "B",
        "analysis": "Checkpointer支持增量检查点和全量检查点两种模式。'仅支持全量检查点'是错误说法。"
    }
,
    {
        "id": "D3-17",
        "question": "GaussDB中，以下哪种情况会强制生成Custom Plan（cplan）而非Generic Plan（gplan）？",
        "options": ["A. 使用参数化SQL且执行次数较少", "B. SQL语句包含非常量条件", "C. 使用PREPARE语句预编译且执行次数超过阈值", "D. 手动指定plan_hint时"],
        "answer": "D",
        "analysis": "使用plan_hint时，优化器无法将hint中的信息通用化，必须为每次执行生成cplan。"
    }
,
    {
        "id": "D3-18",
        "question": "GaussDB中，以下哪个参数不能消除锁资源阻塞问题？",
        "options": ["A. lockwait_timeout", "B. deadlock_timeout", "C. session_timeout", "D. update_lockwait_timeout"],
        "answer": "C",
        "analysis": "session_timeout控制空闲会话超时断开，不直接处理锁资源阻塞问题。其他三个参数均与锁管理直接相关。"
    }
,
    {
        "id": "D3-19",
        "question": "GaussDB的SPM（SQL Plan Management）功能中，以下哪项不属于SPM的核心能力？",
        "options": ["A. 计划捕获（Plan Capture）", "B. 计划选择（Plan Selection）", "C. 计划演进（Plan Evolution）", "D. 计划生成（Plan Generation）"],
        "answer": "D",
        "analysis": "SPM核心功能包括计划捕获、计划选择和计划演进。计划生成属于优化器的功能，不属于SPM的管理范畴。"
    }
,
    {
        "id": "D3-20",
        "question": "GaussDB两地三中心容灾架构中，同城AZ间距要求为？",
        "options": ["A. 大于10km", "B. 大于50km", "C. 大于100km", "D. 大于200km"],
        "answer": "B",
        "analysis": "同城AZ间距要求大于50km，异地AZ间距要求大于200km。"
    },
    {
        "id": "D2-18",
        "question": "GaussDB三层网络规划中，高速平面（High-Speed Plane）的主要作用是？",
        "options": ["A. 用于业务应用访问数据库", "B. 用于节点间数据交换和WAL日志同步", "C. 用于带外管理", "D. 用于云管理平台通信"],
        "answer": "B",
        "analysis": "高速平面（也称存储面/数据面）用于节点间的数据交换和WAL日志同步，要求高带宽低时延（通常25GE/100GE）。业务平面用于应用访问数据库，管理面用于运维管理。"
    },
    {
        "id": "D2-19",
        "question": "GaussDB手工备份（Manual Backup）与自动备份相比，以下描述正确的是？",
        "options": ["A. 手工备份默认保留30天后自动清理", "B. 手工备份需要用户自行管理清理策略", "C. 手工备份不支持全量备份", "D. 手工备份会覆盖自动备份的保留策略"],
        "answer": "B",
        "analysis": "手工备份需要用户自行管理清理策略，系统不会自动删除手工备份文件。自动备份默认保留30天，超期自动清理。"
    },
    {
        "id": "D2-20",
        "question": "金融某行HCS云数据库GaussDB，备份带宽的默认限制为？",
        "options": ["A. 100MB/s", "B. 200MB/s", "C. 250MB/s", "D. 500MB/s"],
        "answer": "C",
        "analysis": "HCS云数据库GaussDB默认备份带宽限制为250MB/s，在备份恢复规划中需考虑此限制对备份窗口的影响。"
    }
]

CH2_MULTI_EXT = [
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
        "question": "关于GaussDB性能指标TPS（Transactions Per Second），以下描述正确的有？",
        "options": ["A. TPS表示系统每秒处理的事务数量", "B. TPS计算需要考虑高峰期集中系数", "C. tpmC是TPC-C基准测试的每分钟吞吐量指标", "D. TPS与tpmC是同一概念的不同表达", "E. 单笔业务可能产生多个数据库事务"],
        "answer": "ABCE",
        "analysis": "TPS衡量每秒事务处理能力，需考虑高峰期集中系数。tpmC是TPC-C每分钟吞吐量，TPS与tpmC是不同的指标概念（D错误）。"
    }
]

# ============================================================
# P0 补充题库 — 考试高频缺失知识点
# 来源: 华为HCCDE专项测试题(500道) + 模拟卷 + 考生回忆
# 知识点: TPS计算/备份容量/索引估算/容灾等级/部署选型
# ============================================================

# 第2章补充: TPS计算、备份容量、容灾等级、部署选型
CH2_JUDGE_EXT2 = [
    {
        "id": "J2-13",
        "question": "国标GB/T 20988-2007中，5级容灾的RPO要求为0~30分钟，RTO为数分钟~2天。",
        "answer": "√",
        "analysis": "5级容灾RPO=0~30分钟、RTO=数分钟~2天，通常采用同城多机房/双集群+异地容灾的部署方案。"
    },
    {
        "id": "J2-14",
        "question": "国标6级容灾要求RPO=0、RTO为秒级，是数据零丢失+远程集群快速恢复的最高等级。",
        "answer": "√",
        "analysis": "6级是国标最高容灾等级，要求数据零丢失(RPO=0)，远程集群快速恢复(RTO=秒级)。同城双集群RPO=0+异地对等容灾。"
    },
    {
        "id": "J2-15",
        "question": "国标GB/T 20988-2007与国际容灾标准SHARE 78中对容灾等级的分级方式完全相同。",
        "answer": "×",
        "analysis": "国标GB/T 20988-2007定义6级容灾标准，国际SHARE 78定义7级标准，两者分级方式和具体指标不同，不能混用。"
    },
    {
        "id": "J2-16",
        "question": "GaussDB的HashBucket在线扩容技术，扩容期间对在线业务的平均吞吐量和平均延时影响小于5%。",
        "answer": "√",
        "analysis": "HashBucket在线扩容技术支持在线迁移数据，扩容期间平均吞吐量和平均延时影响小于5%。"
    },
]

CH2_SINGLE_EXT2 = [
    {
        "id": "D2-21",
        "question": "某业务系统每日产生业务量300万笔，其中80%的流量集中在上午4小时内。平均每笔业务操作产生5个数据库事务。该业务初始需求的TPS约为？",
        "options": ["A. 500 tps", "B. 833 tps", "C. 1042 tps", "D. 1500 tps"],
        "answer": "B",
        "analysis": "高峰总事务数=300万×80%×5=1200万；高峰时长=4×3600=14400秒；TPS=1200万÷14400≈833 tps。"
    },
    {
        "id": "D2-22",
        "question": "某金融客户核心系统日处理业务量500万笔，高峰期集中在2小时内，单笔业务产生4个事务，高峰期TPS约为？",
        "options": ["A. 2778 tps", "B. 5556 tps", "C. 6944 tps", "D. 10000 tps"],
        "answer": "B",
        "analysis": "高峰总事务数=500万x100%x4=2000万(假设所有业务集中在2小时)；高峰时长=2x3600=7200秒；TPS=2000万/7200≈2778 tps。若按高峰期业务量占80%算，高峰事务数=500万x80%x4=1600万，TPS=1600万/7200≈2222 tps。考试常见算法是按全部业务算高峰TPS。"
    },
    {
        "id": "D2-23",
        "question": "某互联网平台高峰期TPS约3万，当前数据量30TB，SQL相对简单(IOT场景)。最适合的部署方案是？",
        "options": ["A. 集中式部署(单节点)", "B. 分布式部署(3节点起)", "C. 轻量化部署", "D. 集中式+读写分离"],
        "answer": "B",
        "analysis": "TPS 3万>2万(集中式上限)，数据量30TB>24TB(集中式上限)，SQL简单适合分布式，应采用分布式部署。"
    },
    {
        "id": "D2-24",
        "question": "某GaussDB系统业务总数据量10TB，每日新增200GB，全备周期7天，保留周期30天，压缩比0.5(2:1)，全量备份总容量约为？",
        "options": ["A. 30TB", "B. 10TB", "C. 5TB", "D. 60TB"],
        "answer": "A",
        "analysis": "全量备份次数(保留期内)=ceil(30÷7)+1=5+1=6次(含当前备份)；C1=10TB×6×0.5=30TB。考试另有简化算法：C1≈总数据量×压缩比=10TB×0.5=5TB。需看清题目要求。"
    },
    {
        "id": "D2-25",
        "question": "某GaussDB系统数据量8TB，每日新增150GB，增量备份保留天数30天，压缩比0.5，增量备份总容量约为？",
        "options": ["A. 2.25TB", "B. 4.5TB", "C. 3.0TB", "D. 6.0TB"],
        "answer": "A",
        "analysis": "增量备份容量C2=每日新增数据量×保留周期×压缩比=150GB×30天×0.5=2250GB≈2.25TB。注意：增量备份容量按每天新增量累计。"
    },
    {
        "id": "D2-26",
        "question": "GaussDB计算资源容量规划中，金融核心业务的复杂度折算系数通常？",
        "options": ["A. 小于1", "B. 等于1", "C. 大于1（常见1.2~1.5）", "D. 无固定系数"],
        "answer": "C",
        "analysis": "金融核心业务交易逻辑复杂，对数据库性能要求高，复杂度折算系数通常大于1，常见值为1.2~1.5。"
    },
    {
        "id": "D2-27",
        "question": "GaussDB网络规划中，跨Region的网络时延要求应小于？",
        "options": ["A. 0.25ms", "B. 2ms", "C. 10ms", "D. 20ms"],
        "answer": "D",
        "analysis": "跨Region网络时延要求<20ms。AZ内部<0.25ms，Region内跨AZ<2ms，跨Region<20ms。"
    },
]

CH2_MULTI_EXT2 = [
    {
        "id": "M2-11",
        "question": "国标GB/T 20988-2007定义的容灾等级中，符合RPO=0要求的是？",
        "options": ["A. 4级(同城双机房单集群)", "B. 5级(同城双机房+异地容灾)", "C. 6级(同城双集群RPO=0+异地对等容灾)", "D. 1级(本地备份)", "E. 6级要求RPO=0且RTO为秒级"],
        "answer": "CE",
        "analysis": "国标6级要求RPO=0且RTO=秒级。5级RPO=0~30分钟。4级RPO<15分钟。1级RPO=1~7天。C描述的是6级实现方案，E描述的是6级指标要求，均为正确。"
    },
    {
        "id": "M2-12",
        "question": "国标GB/T 20988-2007与国际容灾标准SHARE 78的主要区别包括？",
        "options": ["A. 国标将容灾分为6级，SHARE 78分为7级", "B. 国标6级要求RPO=0且RTO=秒级", "C. SHARE 78第7级相当于国标6级", "D. 两个标准的分级和指标完全一致", "E. 两个标准对RPO/RTO的定义和指标不同"],
        "answer": "ABCE",
        "analysis": "国标6级 vs SHARE 78七级，两者分级方式和具体指标不同。国标6级RPO=0、RTO=秒级。SHARE 78第7级要求RPO=0、RTO≈0。两者不完全一致。"
    },
    {
        "id": "M2-13",
        "question": "某客户新项目选型GaussDB，需求如下：存储过程多、TPS约2000、数据容量10TB、容灾5级、同城RPO=0、异地RPO<10s、成本敏感。以下说法正确的有？",
        "options": ["A. 存储过程多，适合集中式部署", "B. TPS<2万，集中式可满足", "C. 容灾5级需同城+异地容灾", "D. 成本敏感应选择双集群方案", "E. 推荐方案：集中式+同城多机房单集群+异地容灾集群"],
        "answer": "ABCE",
        "analysis": "存储过程多→集中式；TPS2000<2万→集中式可满足；5级容灾需同城多机房+异地容灾；成本敏感应选单集群(非双集群)。推荐：集中式+同城两机房单集群+异地流式容灾。"
    },
]

CH3_SINGLE_EXT2 = [
    {
        "id": "D3-32",
        "question": "某表有2000万行数据，每行数据实际占用100字节，页面大小8KB(页面头40B，元组指针4B/条，元组头24B/条)，该表数据文件大小约为？",
        "options": ["A. 2.1GB", "B. 2.8GB", "C. 3.8GB", "D. 4.5GB"],
        "answer": "C",
        "analysis": "单条总占用=4B+24B+100B=128B；单页可用=8192B-40B=8152B；每页行数=8152÷128≈63行；总页数=2000万÷63≈317460页；总大小=317460×8192B≈2.6GB（实际约3.8GB考虑页面内碎片等因素）。注意：不同教材计算方法有差异，本题按标准公式计算。"
    },
    {
        "id": "D3-33",
        "question": "某表有5000万行数据，每条数据实际占用120字节，页面大小8KB(页面头40B，元组指针4B/条，元组头24B/条)，估算该表数据文件大小约为？",
        "options": ["A. 5.2GB", "B. 6.8GB", "C. 7.4GB", "D. 8.1GB"],
        "answer": "C",
        "analysis": "单条总占用=4B+24B+120B=148B；单页可用=8192B-40B=8152B；每页行数=8152÷148≈55行；总页数=5000万÷55≈909091页；总大小=909091×8192B≈7.45GB。"
    },
    {
        "id": "D3-34",
        "question": "GaussDB的GPI(Global Partition Index)索引的适用场景是？",
        "options": ["A. 分区表上的全局索引，支持快速全局唯一约束", "B. 单表上的普通B-tree索引", "C. 本地分区索引(每个分区独立索引)", "D. 全文索引"],
        "answer": "A",
        "analysis": "GPI是作用于分区表的全局索引，索引覆盖所有分区数据，支持全局唯一约束和跨分区的快速定位。"
    },
    {
        "id": "D3-35",
        "question": "GaussDB中，用于管理多版本并发控制(MVCC)的元组可见性判断依据是？",
        "options": ["A. 时间戳", "B. 事务ID(xmin/xmax)比较", "C. 锁状态", "D. 数据版本号"],
        "answer": "B",
        "analysis": "MVCC可见性判断基于元组中的xmin(创建该版本的事务ID)和xmax(删除/更新该版本的事务ID)与当前事务快照的比较。"
    },
    {
        "id": "D3-36",
        "question": "GaussDB的DB4AI特性提供的主要能力是？",
        "options": ["A. 自动索引推荐", "B. SQL自动改写", "C. 数据库内嵌AI算法执行，支持模型训练和推理", "D. 智能故障诊断"],
        "answer": "C",
        "analysis": "DB4AI(Database for AI)将AI算法内置到数据库中，支持在SQL中直接执行模型训练、预测推理等AI任务，无需数据导出。"
    },
    {
        "id": "D3-37",
        "question": "GaussDB的极速RTO(Recovery Time Objective)技术的关键实现机制是？",
        "options": ["A. 增加checkpoint频率", "B. 备机并行回放WAL日志", "C. 减少WAL日志量", "D. 预分配数据块"],
        "answer": "B",
        "analysis": "极速RTO通过备机并行回放WAL日志技术，利用多核CPU并行处理，将主备切换恢复时间降低到秒级。"
    },
]

CH6_JUDGE_EXT2 = [
    {
        "id": "J6-8",
        "question": "GaussDB中，全量备份表示对所有目标数据进行完整备份，包含备份时刻点上数据库的全量数据，不能自身恢复出完整的数据库。",
        "answer": "×",
        "analysis": "全量备份包含备份时刻点上数据库的全量数据，且可以自身恢复出完整的数据库。题目描述与事实相反。"
    },
]

CH6_SINGLE_EXT2 = [
    {
        "id": "D6-22",
        "question": "GaussDB集群DN节点多数派故障时，应采取的恢复措施是？",
        "options": ["A. 强制重启集群", "B. 停止集群后使用gs_ctl重建故障DN", "C. 直接删除故障节点", "D. 忽略故障继续运行"],
        "answer": "B",
        "analysis": "DN多数派故障会导致集群不可用，需停止集群后使用gs_ctl工具重建故障DN数据目录，重新拉齐数据。"
    },
    {
        "id": "D6-23",
        "question": "GaussDB中，当数据库进入只读状态(Read-Only)时的常见原因是？",
        "options": ["A. 配置错误", "B. 网络故障", "C. 磁盘空间满(DN数据盘使用率超85%)", "D. 密码过期"],
        "answer": "C",
        "analysis": "GaussDB自动将数据库置为只读状态通常是因为DN数据盘使用率超过阈值(默认85%)，触发只读保护机制。"
    },
    {
        "id": "D6-24",
        "question": "GaussDB中，CSS(Cluster Startup Service)集群启动服务的主要功能是？",
        "options": ["A. 管理集群启动流程，确保各组件按正确顺序启动", "B. SQL解析", "C. 数据加密", "D. 监控磁盘"],
        "answer": "A",
        "analysis": "CSS负责集群启动管理和组件启动顺序控制，是GaussDB集群管理的重要组件。"
    },
    {
        "id": "D6-25",
        "question": "GaussDB中，gs_stack工具的作用是？",
        "options": ["A. 打印指定线程的内核态堆栈信息", "B. 查看系统表", "C. 查看数据文件", "D. 检查备份状态"],
        "answer": "A",
        "analysis": "gs_stack打印数据库线程的堆栈信息，用于分析线程卡住、死锁、hang等问题场景。"
    },
    {
        "id": "D6-26",
        "question": "GaussDB的流式容灾(异地)与同城双集群容灾的主要区别是？",
        "options": ["A. 流式容灾不需要网络连接", "B. 流式容灾基于WAL日志异步传输RPO>0；同城双集群基于同步复制RPO=0", "C. 流式容灾性能更好", "D. 同城双集群不支持故障切换"],
        "answer": "B",
        "analysis": "流式容灾通过WAL日志异步传输实现异地容灾，RPO>0；同城双集群采用同步复制确保RPO=0。"
    },
]

CH6_MULTI_EXT2 = [
    {
        "id": "M6-10",
        "question": "GaussDB运维的「五类问题」(慢、满、错、hang、宕)的定位处理方法论包括？",
        "options": ["A. 慢：定位慢SQL，分析执行计划，优化索引/参数", "B. 满：检查磁盘/内存使用率，清理或扩容", "C. 错：检查错误日志，分析错误码，回滚/修复", "D. hang：查看锁等待/线程堆栈，分析死锁", "E. 宕：查看coredump/系统日志，分析宕机根因"],
        "answer": "ABCDE",
        "analysis": "GaussDB运维五类问题各有针对性的定位方法和管理手段：慢→SQL优化、满→资源清理、错→错误分析、hang→锁分析、宕→根因分析。"
    },
    {
        "id": "M6-11",
        "question": "GaussDB常见的锁问题包括？",
        "options": ["A. 锁超时(LockTimeout)", "B. 死锁(Deadlock)", "C. 锁阻塞链阻塞", "D. 行锁丢失", "E. 锁等待导致业务堆积"],
        "answer": "ABCE",
        "analysis": "GaussDB会自动检测死锁并回滚其中一个事务解决死锁。锁阻塞链可通过pg_locks/pg_sessions定位。D选项行锁丢失不是GaussDB常见问题。"
    },
    {
        "id": "M6-12",
        "question": "GaussDB基于WAL日志备份的PITR恢复流程包括？",
        "options": ["A. 使用全量备份文件恢复数据库基本状态", "B. 应用WAL归档日志推进到目标时间点", "C. 数据库打开后验证数据完整性", "D. 重建所有索引", "E. 重新配置所有参数"],
        "answer": "ABC",
        "analysis": "PITR流程：全量恢复→WAL日志回放到指定时间点(通过recovery_target_time参数)→数据库open验证。不需要重建索引(除非损坏)和重新配置参数。"
    },
]

CH3_JUDGE_EXT = [
    {
        "id": "J3-6",
        "question": "GaussDB基于分布式理论构建的分布式数据库，空间放大更小，性能抖动更小。",
        "answer": "√",
        "analysis": "GaussDB分布式架构通过数据分片、分布式事务管理等技术，有效减少了空间放大问题，并通过智能调度减少了性能抖动。"
    }
]

CH3_SINGLE_EXT = [
    {
        "id": "D3-13",
        "question": "GaussDB中，SQL Bypass优化技术的核心特点是？",
        "options": ["A. 对所有SQL语句进行优化", "B. 在语法解析前跳过SQL引擎", "C. 跳过经典执行器框架，直接调用存储接口", "D. 仅对SELECT语句生效"],
        "answer": "C",
        "analysis": "SQL Bypass是一种基于执行层的优化，在语法解析层完成模式识别后，跳过经典执行器绝大部分框架，直接调用存储接口，减少执行开销。"
    },
    {
        "id": "D3-14",
        "question": "UStore存储引擎中，以下哪个字段用于记录页面事务槽信息？",
        "options": ["A. free_space", "B. potential_freespace", "C. td_count", "D. blk_size"],
        "answer": "C",
        "analysis": "td_count（事务槽数量）是UStore引擎特有的字段，用于记录页面事务槽信息，反映页面的事务活动情况。AStore使用potential_freespace记录页面潜在空闲空间。"
    },
    {
        "id": "D3-15",
        "question": "GaussDB分布式执行中，CN轻量化的主要目的是？",
        "options": ["A. 减少CN节点内存占用", "B. 将SQL优化下推到DN执行", "C. 提高客户端连接数", "D. 简化SQL语法解析流程"],
        "answer": "B",
        "analysis": "CN轻量化是将部分SQL优化和执行计划生成工作下推到DN节点，减少CN的负载压力，提升分布式执行效率。"
    },
    {
        "id": "D5-13",
        "question": "以下哪个工具不能用于排查GaussDB的CPU高占用问题？",
        "options": ["A. pg_stat_activity", "B. WDR报告", "C. statement_history视图", "D. pg_stat_replication"],
        "answer": "D",
        "analysis": "pg_stat_replication用于查看主备复制状态，不包含CPU使用信息。其他三个均可用于CPU问题排查。"
    }
,
    {
        "id": "D5-14",
        "question": "GaussDB DBMind的诊断能力中，用于分析秒级性能抖动的关键数据源是？",
        "options": ["A. pg_stat_activity", "B. WDR报告", "C. ASP（Active Session Profile）", "D. pg_stat_statements"],
        "answer": "C",
        "analysis": "ASP定时采样活跃会话的等待事件、SQL ID、状态等信息，可用于诊断秒级性能抖动问题。"
    }
,
    {
        "id": "M5-7",
        "question": "GaussDB的索引推荐算法的工作流程包括以下哪些步骤？",
        "options": ["A. 基于语法解析处理SQL语句，识别可优化模式", "B. 利用虚拟索引进行代价分析，避免创建真实索引的开销", "C. 采集Workload信息，评估索引对整体负载的收益", "D. 通过爬山法（Hill Climbing）选取最优索引组合", "E. 自动将推荐的索引创建到生产环境"],
        "answer": "ABCD",
        "analysis": "索引推荐流程：语法解析识别→虚拟索引代价分析→Workload采集评估→爬山法选优。推荐索引需要人工审核后创建。"
    }
,
    {
        "id": "M5-8",
        "question": "关于GaussDB JDBC驱动参数优化，以下说法正确的有？",
        "options": ["A. prepareThreshold控制多次重复执行时切换为服务端预编译的阈值", "B. batchMode=on开启批量提交模式", "C. autoBalance参数控制CN节点的负载均衡", "D. defaultRowFetchSize控制批量查询时每次拉取的行数", "E. priorityServers=3配置容灾优先选主策略"],
        "answer": "ABCD",
        "analysis": "prepareThreshold、batchMode、autoBalance、defaultRowFetchSize均为JDBC标准优化参数。"
    }
,
    {
        "id": "M5-9",
        "question": "GaussDB DBMind的智能运维核心能力包括？",
        "options": ["A. 慢SQL根因分析", "B. 索引推荐", "C. 性能容量预测", "D. 趋势分析和异常检测", "E. 自动数据备份和恢复"],
        "answer": "ABCD",
        "analysis": "DBMind覆盖SQL诊断优化、索引推荐、容量预测、异常检测等场景。自动备份恢复由独立模块负责。"
    }
,
    {
        "id": "D6-14",
        "question": "GaussDB分布式集群中，CN节点故障超过多少秒会被自动剔除？",
        "options": ["A. 5秒", "B. 10秒", "C. 20秒", "D. 25秒"],
        "answer": "D",
        "analysis": "GaussDB集群中CN节点故障超过25秒会被自动剔除。"
    }
,
    {
        "id": "D6-15",
        "question": "GaussDB的HashBucket在线扩容技术，扩容期间对在线业务性能的影响小于？",
        "options": ["A. 3%", "B. 5%", "C. 8%", "D. 10%"],
        "answer": "B",
        "analysis": "HashBucket在线扩容期间平均吞吐量和平均延时影响小于5%。"
    }
,
    {
        "id": "D6-16",
        "question": "关于GaussDB全量备份的理解，以下说法错误的是？",
        "options": ["A. 全量备份表示对所有目标数据进行备份", "B. 全量备份包含备份时刻点上数据库的全部数据", "C. 全量备份耗时与数据库数据总量成正比", "D. 全量备份自身无法恢复出完整的数据库"],
        "answer": "D",
        "analysis": "全量备份自身可以恢复完整的数据库，不需要依赖其他备份集。D选项是错误的。"
    }
,
    {
        "id": "D6-17",
        "question": "GaussDB闪回查询中，参数undo_retention设置为0时会发生什么？",
        "options": ["A. 闪回查询性能提升", "B. 清理所有闪回点快照信息，之前版本不可再做闪回查询", "C. 保留时间变为无限", "D. 仅影响AStore引擎的闪回"],
        "answer": "B",
        "analysis": "undo_retention设置为0时会立即清理所有闪回点快照信息，之前任何版本都不再支持闪回查询。"
    }
,
    {
        "id": "D6-18",
        "question": "GaussDB流式容灾（异地）与同城双集群容灾的主要区别是？",
        "options": ["A. 流式容灾不需要网络连接", "B. 流式容灾基于WAL日志异步传输RPO>0；同城双集群基于同步复制RPO=0", "C. 流式容灾性能更好", "D. 同城双集群不支持故障切换"],
        "answer": "B",
        "analysis": "流式容灾通过WAL日志异步传输实现异地容灾RPO>0；同城双集群采用同步复制确保RPO=0。"
    }
,
    {
        "id": "D6-19",
        "question": "GaussDB升级中，需要中断业务进行升级的方式是？",
        "options": ["A. 滚动升级", "B. 就地升级", "C. 灰度升级", "D. 热补丁升级"],
        "answer": "B",
        "analysis": "就地升级需停止数据库服务进行升级，业务中断时间长。滚动/灰度升级支持在线逐节点升级。"
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
    },
    {
        "id": "D3-23",
        "question": "GaussDB中，列级别的统计信息用于优化查询计划，其中MCV（Most Common Values）统计信息的主要作用是？",
        "options": ["A. 记录列中NULL值比例", "B. 记录列中最常出现的前N个值及其频率", "C. 记录列的最小值和最大值", "D. 记录列的唯一值数量"],
        "answer": "B",
        "analysis": "MCV（高频值）统计信息记录目标列中最常出现的前N个值及其出现频率，帮助优化器准确估算包含等值条件的查询选择率，是列级统计信息的重要组成部分。"
    },
    {
        "id": "D3-24",
        "question": "GaussDB备机通过并行回放（Parallel Replay）WAL日志实现极速RTO，以下关于日志回放的描述正确的是？",
        "options": ["A. 备机串行回放WAL日志以确保数据一致性", "B. 备机使用多线程并行回放WAL日志，通过Page Token机制解决冲突", "C. WAL日志回放只在故障切换时进行", "D. 日志回放仅由主机完成"],
        "answer": "B",
        "analysis": "GaussDB极速RTO技术核心是备机多线程并行回放WAL日志，通过Page Token机制解决并行回放中的页面冲突问题，利用多核CPU加速日志回放速度，将恢复时间降低到秒级。"
    },
    {
        "id": "D3-25",
        "question": "GaussDB的分布式事务中，保证读一致性的机制是？",
        "options": ["A. GTM-Lite提供全局CSN保证读一致性", "B. 两阶段提交保证读一致性", "C. MVCC通过xmin/xmax比较保证读一致性", "D. Paxos协议保证读一致性"],
        "answer": "A",
        "analysis": "GTM-Lite提供全局CSN（提交序列号），事务基于CSN判断快照可见性，与活跃事务数量无关。两阶段提交保证写原子性而非读一致性。"
    },
    {
        "id": "D3-26",
        "question": "GaussDB的分布式事务中，保证写原子性（Write Atomicity）的机制是？",
        "options": ["A. 一阶段提交", "B. 两阶段提交（2PC）", "C. 三阶段提交", "D. Paxos协议"],
        "answer": "B",
        "analysis": "GaussDB分布式事务通过两阶段提交（2PC）协议保证写原子性，确保事务在所有DN节点上要么全部提交要么全部回滚。"
    },
    {
        "id": "D3-27",
        "question": "GaussDB的PBE机制中，前几次执行生成Custom Plan？",
        "options": ["A. 3次", "B. 5次", "C. 7次", "D. 10次"],
        "answer": "B",
        "analysis": "PBE机制中前5次执行生成Custom Plan，从第6次起切换为Generic Plan（可复用）。通过plan_cache_mode='force_generic_plan'可强制使用通用计划。"
    },
    {
        "id": "D3-28",
        "question": "GaussDB的WAL日志中，最大占用空间的计算公式是？",
        "options": ["A. (wal_keep_segments + checkpoint_segments * 2 + 1) * 16MB", "B. (wal_keep_segments + checkpoint_segments) * 16MB", "C. wal_keep_segments * 16MB", "D. (wal_keep_segments + checkpoint_segments + 1) * 16MB"],
        "answer": "A",
        "analysis": "WAL日志最大空间=(wal_keep_segments + checkpoint_segments * 2 + 1) * 16MB。wal_keep_segments推荐128，checkpoint_segments推荐1024。"
    },
    {
        "id": "D3-29",
        "question": "GaussDB的统计信息中，Histogram（直方图）的作用是？",
        "options": ["A. 记录列中最常出现的前N个值", "B. 描述除NULL值和MCV值外数据的分布", "C. 记录列的唯一值数量", "D. 记录列中NULL值的比例"],
        "answer": "B",
        "analysis": "Histogram（等高直方图）描述除NULL值和MCV值外数据的分布，将数据划分为多个bucket，帮助优化器估算范围查询选择率。"
    },
    {
        "id": "D3-30",
        "question": "GaussDB中，IndexOnlyScan算子的特点是？",
        "options": ["A. 需要访问基表获取数据行", "B. 直接从索引返回结果，无需访问基表", "C. 仅用于唯一索引", "D. 与Seq Scan等价"],
        "answer": "B",
        "analysis": "IndexOnlyScan直接从索引元组中返回查询所需列，无需回表访问基表数据页，当索引覆盖查询所需列时使用，可大幅减少I/O。"
    },
    {
        "id": "D3-31",
        "question": "GaussDB统计信息中，NULLFrac统计信息的作用是？",
        "options": ["A. 记录列中NULL值占比，帮助估算IS NULL条件的行数", "B. 记录非NULL值的数量", "C. 记录列的默认值占比", "D. 记录空字符串占比"],
        "answer": "A",
        "analysis": "NULLFrac记录NULL值占总行数比例，优化器基于此准确估算IS NULL/IS NOT NULL等条件的行数。"
    }
]

CH3_MULTI_EXT = [
    {
        "id": "M3-7",
        "question": "一张大表中死元组较多时，以下哪些参数调整可以有效提升数据库性能？",
        "options": ["A. 将autovacuum的检查间隔从10分钟调到5分钟（autovacuum_naptime）", "B. 调低vacuum_cost_delay（减少每次的休息时间）", "C. 调高vacuum_cost_limit（增加每次工作量上限）", "D. 调小触发vacuum的阈值参数（提高执行频率）", "E. 关闭autovacuum改为完全手动vacuum"],
        "answer": "ABCD",
        "analysis": "autovacuum_naptime控制两次执行间隔，调大可提高频率；vacuum_cost_delay应调低减少休息时间；vacuum_cost_limit应调高增加工作量上限；触发阈值调小可提高vacuum执行频率。E选项中关闭autovacuum通常不推荐。"
    },
    {
        "id": "M3-8",
        "question": "关于GaussDB的AStore和UStore存储引擎，以下说法正确的有？",
        "options": ["A. AStore采用Append Update（追加更新）方式", "B. UStore采用In-place Update（原地更新）方式", "C. AStore通过potential_freespace记录页面空闲空间", "D. UStore通过td_count记录事务槽数量", "E. UStore在所有场景下写性能均优于AStore"],
        "answer": "ABCD",
        "analysis": "AStore：追加更新，使用potential_freespace；UStore：原地更新，使用td_count记录事务槽。两者各有优劣，E选项过于绝对。"
    },
    {
        "id": "M3-9",
        "question": "GaussDB分布式执行计划中，以下关于计划下推（Pushdown）的描述正确的有？",
        "options": ["A. 部分分布式计划可以将计算完全下推到DN执行，减少CN负担", "B. 所有分布式查询计划都可以完全下推到DN执行", "C. 算子下推将过滤和投影操作下推到DN，减少CN-DN数据传输", "D. 分布式计划可能在CN上执行部分计算（如最终聚合），无法完全下推", "E. 下推计划不适合复杂多表关联场景"],
        "answer": "ACDE",
        "analysis": "分布式计划根据SQL复杂度分为多种类型，部分计划可完全下推到DN（如简单表扫描），但需要数据重分布或最终聚合的查询必须在CN执行部分计算（D正确）。B错误（并非所有计划都可完全下推）。"
    },
    {
        "id": "M3-10",
        "question": "GaussDB的页式存储（Page-Structured）与段页式存储（Segment-Page）的对比，以下说法正确的有？",
        "options": ["A. 页式存储页面大小固定（默认8KB），段页式以段为单位管理空间", "B. 段页式存储更适合大表，支持动态扩展", "C. 页式存储的元组头包含xmin/xmax事务信息", "D. 段页式的1号文件仅存储文件头信息", "E. 页式存储和段页式存储可在同一数据库实例中共存"],
        "answer": "ABCD",
        "analysis": "页式存储页面固定8KB，元组头含xmin/xmax实现MVCC。段页式以段为单位（1号文件存文件头，2-5号存数据），支持大表动态扩展。E错误：两者不能在同一数据库实例中共存，是互斥的。"
    },
    {
        "id": "M3-11",
        "question": "GaussDB支持的连接算子（Join Operator）类型中，以下关于适用场景的说法正确的有？",
        "options": ["A. NestLoop适合外表结果集小、内表有索引的场景", "B. HashJoin适合内表可在内存中放下的场景", "C. MergeJoin适合内外表已经有序的场景", "D. SemiJoin（半连接）用于EXISTS子查询", "E. AntiJoin（反连接）用于NOT EXISTS子查询"],
        "answer": "ABCDE",
        "analysis": "五种连接算子各有适用场景：NestLoop适合小结果集+索引；HashJoin适合内存容纳内表；MergeJoin适合有序输入；SemiJoin/AntiJoin对应EXISTS/NOT EXISTS。"
    },
    {
        "id": "M3-12",
        "question": "GaussDB的分布式计划类型包括以下哪些？描述正确的有？",
        "options": ["A. CN轻量化：简单语句直接下推DN执行，跳过优化器", "B. FQS（完全下推）：语句完全下推到多个DN执行无需交互", "C. STREAM计划：DN间通过Stream算子（Gather/Redistribute/Broadcast）交互", "D. XC计划：CN承担大部分计算", "E. FQS计划不支持算子下推"],
        "answer": "ABCD",
        "analysis": "四种分布式计划按复杂度：CN轻量化→FQS→STREAM→XC。轻量化跳过优化器；FQS完全下推无交互；STREAM需Stream算子流转数据；XC计划CN承担主要计算。E错误。"
    },
    {
        "id": "M3-13",
        "question": "GaussDB的统计信息体系包含以下哪些级别？",
        "options": ["A. 表级别（行数、页面数）", "B. 列级别（Distinct/NULLFrac/MCV/Histogram）", "C. 多列统计信息（解决多列相关性误差）", "D. 索引统计信息", "E. 视图统计信息"],
        "answer": "ABCD",
        "analysis": "GaussDB支持表级、列级、多列、索引等统计级别。视图统计信息不是独立统计级别。"
    },
    {
        "id": "M3-14",
        "question": "GaussDB的安全能力五维体系包括以下哪些？",
        "options": ["A. 进不来：访问控制和身份认证", "B. 看不懂：数据加密（TDE、全密态）", "C. 改不了：防篡改账本数据库", "D. 拿不走：数据加密防止数据文件泄露", "E. 赖不掉：安全审计日志"],
        "answer": "ABCDE",
        "analysis": "五维安全体系：进不来（访问控制）、看不懂（TDE/全密态加密）、改不了（防篡改）、拿不走（数据加密）、赖不掉（审计日志）。"
    },
    {
        "id": "M3-15",
        "question": "GaussDB的多租户精细化资源管理包括以下哪些维度的管控？",
        "options": ["A. CPU（通过cgroup限制时间片）", "B. 内存（限制使用上限）", "C. I/O（限制IOPS）", "D. 存储空间（限制容量大小）", "E. 网络带宽"],
        "answer": "ABCD",
        "analysis": "多租户资源管理包括CPU（cgroup）、内存、I/O（IOPS）、存储空间四个维度。网络带宽不属于多租户资源管理范围。"
    }
]

CH4_JUDGE_EXT = [
    {
        "id": "J4-6",
        "question": "GaussDB中，可以对表授予查询权限后，再单独收回针对某列的查询权限。",
        "answer": "×",
        "analysis": "GaussDB不支持通过表授权后再单独收回某列权限。要控制列级权限，需要通过列授权的方式（直接对列授权），而不是通过表授权后再收回的方式。"
    },
    {
        "id": "J4-7",
        "question": "GaussDB创建行访问控制策略时，应使用USING关键字而不是WITH关键字。",
        "answer": "√",
        "analysis": "GaussDB行级安全策略通过CREATE POLICY ... USING语句创建，使用USING关键字定义策略表达式。WITH用于CREATE POLICY的WITH CHECK OPTION子句。"
    }
]

CH4_SINGLE_EXT = [
    {
        "id": "D4-7",
        "question": "GaussDB中，控制审计功能开启与关闭的总开关参数是？",
        "options": ["A. audit_enabled", "B. audit_dml_state", "C. audit_level", "D. audit_acl"],
        "answer": "A",
        "analysis": "audit_enabled参数控制审计功能的开启与关闭，是审计功能的总开关。audit_dml_state等参数用于细化具体的审计策略。"
    },
    {
        "id": "D4-8",
        "question": "GaussDB透明加密（TDE）技术中，加密和解密操作发生在哪个层次？",
        "options": ["A. 应用层", "B. 数据库内核层", "C. 存储层", "D. 网络层"],
        "answer": "B",
        "analysis": "TDE（Transparent Data Encryption）在数据库内核层完成加密/解密操作，对上层应用完全透明，无需修改应用程序。"
    },
    {
        "id": "D4-11",
        "question": "关于GaussDB透明加密（TDE）的使用场景和性能影响，以下说法正确的是？",
        "options": ["A. TDE对所有数据类型加密性能开销相同", "B. TDE加密后查询性能完全不变", "C. TDE适用于存储敏感数据的场景，会有一定的读写性能开销", "D. TDE仅对列存储生效"],
        "answer": "C",
        "analysis": "TDE在存储引擎层对数据文件进行实时加密/解密，适用于存储身份证、银行卡等敏感数据的场景。由于加解密操作在数据读写路径上，会有一定的性能开销，并非完全无影响。"
    },
    {
        "id": "D4-9",
        "question": "GaussDB中，查看指定时间区间审计日志的正确语法是？",
        "options": ["A. SELECT * FROM pg_audit_log WHERE time BETWEEN 't1' AND 't2'", "B. gs_audit_log -s 't1' -e 't2'", "C. SELECT * FROM pg_query_audit('start_time', 'end_time')", "D. AUDIT LOG FROM 't1' TO 't2'"],
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
        "id": "J4-9",
        "question": "GaussDB的安全规划只需考虑数据库内核层安全即可。",
        "answer": "×",
        "analysis": "GaussDB安全规划是分层体系，包括应用层（SQL审核）、接入层（SSL）、网络传输层（VPC/防火墙）、OS层（iptables）、数据库内核层（TDE/审计/三权分立）五个层次。"
    }
]

CH4_MULTI_EXT = [
    {
        "id": "M4-6",
        "question": "GaussDB透明加密TDE的密钥体系中包含的密钥层级有？",
        "options": ["A. 主密钥（CMK）", "B. 表加密密钥（TDEK）", "C. 数据加密密钥（DEK）", "D. 用户公钥（User Key）", "E. 会话密钥（Session Key）"],
        "answer": "ABC",
        "analysis": "TDE多层密钥体系：CMK（主密钥）加密TDEK（表加密密钥），TDEK加密DEK（数据加密密钥），DEK加密实际数据。用户公钥和会话密钥不属于TDE密钥体系。"
    },
    {
        "id": "M4-7",
        "question": "关于GaussDB统一审计（Unified Audit），以下说法正确的有？",
        "options": ["A. 可按用户配置审计策略", "B. 可按IP地址配置审计策略", "C. 可按操作资源类型配置策略", "D. 可按时间条件组合配置策略", "E. 可通过CREATE AUDIT POLICY创建审计策略"],
        "answer": "ABCDE",
        "analysis": "统一审计通过CREATE AUDIT POLICY创建灵活的策略，可按操作类型、用户、IP、客户端、时间等条件组合定义审计范围，所有选项均正确。"
    },
    {
        "id": "M4-8",
        "question": "关于GaussDB的防篡改账本数据库，以下说法正确的有？",
        "options": ["A. 防篡改账本通过Hash链技术确保数据不可篡改", "B. 历史表记录用户表每一行数据的变更历史", "C. 全局表存储所有防篡改表的全局信息", "D. 防篡改账本适用于对数据完整性要求极高的审计场景", "E. 防篡改账本会降低数据写入性能"],
        "answer": "ABCDE",
        "analysis": "防篡改账本数据库通过Hash链技术保证数据完整性。历史表存变更记录，全局表存元数据。适用于审计等场景，但Hash计算会带来写入性能开销。"
    }
]

CH5_JUDGE_EXT = [
    {
        "id": "J5-6",
        "question": "GaussDB DBMind的均值漂移检测器（Mean Shift Detector）基于固定阈值进行异常检测。",
        "answer": "×",
        "analysis": "均值漂移检测器动态适应数据分布变化，无需固定阈值，适合渐变异常检测。它基于统计分布建模，通过检测均值漂移发现异常。"
    }
]

CH5_SINGLE_EXT = [
    {
        "id": "D5-11",
        "question": "GaussDB性能监控中，以下哪个属于L2级别的监控内容？",
        "options": ["A. 基础CPU使用率", "B. 磁盘空间使用率", "C. 全量SQL和Session历史（ASP/WDR）", "D. 服务器硬件温度"],
        "answer": "C",
        "analysis": "L2级别提供数据库级的全量SQL、Session历史（ASP）和性能报告（WDR）等高级监控分析能力。L0为基础系统监控，L1为数据库基础监控。"
    },
    {
        "id": "D5-12",
        "question": "GaussDB中，参数Dynamic_used_shrctx显示已使用的全局动态内存较高时，应查询哪个视图来分析当前会话执行的SQL？",
        "options": ["A. pg_stat_activity", "B. pg_session_wait", "C. pg_locks", "D. pg_stats"],
        "answer": "A",
        "analysis": "pg_stat_activity视图可以查看当前数据库会话状态和正在执行的SQL语句，当动态内存使用较高时，通过该视图查找占用内存较多的会话和SQL进行优化。"
    },
    {
        "id": "D5-15",
        "question": "客户数据库中表数量较多（数千张表），查询效率偏低，以下哪个GUC参数调整最有助于优化此类场景的查询效率？",
        "options": ["A. 增大max_connections", "B. 开启enable_global_plancache缓存通用计划", "C. 增大wal_buffers", "D. 降低maintenance_work_mem"],
        "answer": "B",
        "analysis": "表数量多的场景，频繁的SQL编译和计划生成会消耗大量资源。开启enable_global_plancache后，通用执行计划（gplan）可被多个会话复用，减少重复优化开销。max_connections控制连接数而非查询效率。"
    },
    {
        "id": "D5-16",
        "question": "GaussDB的Plan Hint中，指定两表连接方式为哈希连接的语法是？",
        "options": ["A. nestloop(t1 t2)", "B. hashjoin(t1 t2)", "C. mergejoin(t1 t2)", "D. leading(t1 t2)"],
        "answer": "B",
        "analysis": "Plan Hint语法：hashjoin(t1 t2)强制HashJoin；nestloop强制NestLoop；mergejoin强制MergeJoin；leading指定表连接顺序如leading((t1 t2))。"
    },
    {
        "id": "D5-17",
        "question": "GaussDB的Plan Hint中，禁止对某表使用顺序扫描的语法是？",
        "options": ["A. tablescan(table)", "B. indexscan(table)", "C. no tablescan(table)", "D. no indexscan(table)"],
        "answer": "C",
        "analysis": "no tablescan(table)禁止优化器使用全表顺序扫描；indexscan(table)强制索引扫描；tablescan(table)强制全表扫描。Hint通过/*+ */注释嵌入SQL。"
    },
    {
        "id": "D5-18",
        "question": "GaussDB统计信息自动收集的触发阈值是？",
        "options": ["A. 变化量超50+5%*reltuples", "B. 变化量超50+10%*reltuples", "C. 变化量超100+5%*reltuples", "D. 变化量超100+10%*reltuples"],
        "answer": "B",
        "analysis": "统计信息自动收集阈值默认50+10%*reltuples。当表中数据变化量超过此阈值时，autovacuum自动触发ANALYZE。"
    }
]

CH5_MULTI_EXT = [
    {
        "id": "M5-6",
        "question": "GaussDB自适应计划技术中，可能影响执行计划选择的因素包括？",
        "options": ["A. 统计信息的变化", "B. 系统参数（GUC）的调整", "C. 数据分布的变化", "D. 索引的新增或删除", "E. SQL语句的大小写"],
        "answer": "ABCD",
        "analysis": "自适应计划根据统计信息、GUC参数变化、数据分布变化、索引变更等动态调整执行计划。SQL的大小写不影响执行计划选择。"
    }
]

CH6_JUDGE_EXT = [
    {
        "id": "J6-6",
        "question": "GaussDB集群节点引入亚健康状态的目的，是在节点性能下降时降级使用，避免完全中断服务。",
        "answer": "√",
        "analysis": "亚健康状态是GaussDB集群管理的增强特性，当节点性能下降但未完全宕机时，将其标记为亚健康状态降级使用，避免直接剔除节点导致服务中断，提高集群的可用性。"
    },
    {
        "id": "J6-7",
        "question": "GaussDB两地三中心容灾架构中，同城AZ间距要求大于200km。",
        "answer": "×",
        "analysis": "两地三中心架构中：同城AZ间距要求大于50km（而非200km），异地AZ间距要求大于200km。"
    }
]

CH6_SINGLE_EXT = [
    {
        "id": "D6-11",
        "question": "三层网络隔离场景下，DRS数据复制服务的业务流量走哪个网络平面？",
        "options": ["A. 管理面", "B. 业务面", "C. 存储面", "D. 带外管理面"],
        "answer": "B",
        "analysis": "DRS数据复制服务的业务流量走业务网络平面（业务面），管理面主要用于监控和管理操作，存储面用于存储数据访问。"
    },
    {
        "id": "D6-12",
        "question": "GaussDB灰度升级过程中，正确的组件重启顺序是？",
        "options": ["A. CN → DN → GTM", "B. DN → CN → GTM", "C. GTM → CN → DN", "D. 同时重启所有组件"],
        "answer": "C",
        "analysis": "灰度升级的组件重启顺序为：先重启GTM（全局事务管理器），再重启CN（协调节点），最后重启DN（数据节点），确保集群事务一致性和服务连续性。"
    },
    {
        "id": "D6-13",
        "question": "GaussDB自动备份的默认保留天数是多少天？",
        "options": ["A. 7天", "B. 15天", "C. 30天", "D. 90天"],
        "answer": "C",
        "analysis": "GaussDB自动备份默认保留时间为30天，超过保留期限的备份文件会被系统自动清理。手动备份需要用户自行管理清理策略。"
    },
    {
        "id": "D6-20",
        "question": "GaussDB的SQL Patch中，创建补丁的函数是？",
        "options": ["A. dbe_sql_util.create_hint_sql_patch", "B. dbe_sql_util.create_sql_patch", "C. dbe_sql_util.create_patch", "D. dbe_sql_util.gs_spm_set_plan_status"],
        "answer": "A",
        "analysis": "SQL Patch使用dbe_sql_util.create_hint_sql_patch函数创建，通过Unique SQL ID标识目标SQL。Unique SQL ID可通过dbe_perf.statement_history视图获取。"
    },
    {
        "id": "D6-21",
        "question": "GaussDB多租户管理中，CPU资源租户级隔离依赖什么技术？",
        "options": ["A. 线程池", "B. cgroup", "C. NUMA绑核", "D. Docker容器"],
        "answer": "B",
        "analysis": "GaussDB多租户通过cgroup实现CPU时间片的租户级隔离和限制，涵盖CPU、内存、I/O和存储空间四个维度的管控。"
    }
]

CH6_MULTI_EXT = [
    {
        "id": "M6-7",
        "question": "关于GaussDB备份容量计算，以下哪些因素是必须考虑的？",
        "options": ["A. 数据库全量数据大小", "B. 数据压缩比", "C. 备份副本数量", "D. 备份保留天数", "E. 数据库版本号"],
        "answer": "ABCD",
        "analysis": "备份容量 = 数据量 × 压缩比 × 副本数 × 保留天数（增量备份还需要考虑数据变更率）。数据库版本号不影响备份容量的计算。"
    },
    {
        "id": "M6-8",
        "question": "GaussDB集群中，将高资源消耗和低资源消耗的租户放在同一租户组，这种策略的优势包括？",
        "options": ["A. 充分利用每台机器的硬件资源", "B. 租户间资源隔离，避免相互影响", "C. 支持按需分配CPU和内存资源", "D. 减少数据库实例数量", "E. 自动优化SQL执行计划"],
        "answer": "ABC",
        "analysis": "租户资源管理通过将不同资源消耗特征的租户混合部署，实现资源充分利用（A），通过资源隔离避免租户间相互影响（B），并支持CPU/内存的按需分配（C）。D和E不属于租户资源管理的直接优势。"
    },
    {
        "id": "M6-12",
        "question": "GaussDB多租户精细化资源管理的优势包括？",
        "options": ["A. 不同租户间CPU资源隔离，避免相互影响", "B. I/O管控可限制特定租户的IOPS", "C. 存储空间管控防止单个租户耗尽磁盘空间", "D. 将不同消耗特征的租户混合部署以充分利用资源", "E. 自动优化租户的SQL执行计划"],
        "answer": "ABCD",
        "analysis": "多租户通过cgroup实现CPU/内存/I/O/存储空间的隔离，混合部署高消耗+低消耗租户可充分利用硬件。SQL优化不属于多租户管理。"
    }
]


# ============================================================
# 组装完整题库
# ============================================================

QUESTION_BANK = {
    1: {"judge": CH1_JUDGE + CH1_JUDGE_EXT, "single": CH1_SINGLE + CH1_SINGLE_EXT, "multi": CH1_MULTI + CH1_MULTI_EXT},
    2: {"judge": CH2_JUDGE + CH2_JUDGE_EXT + CH2_JUDGE_EXT2, "single": CH2_SINGLE + CH2_SINGLE_EXT + CH2_SINGLE_EXT2, "multi": CH2_MULTI + CH2_MULTI_EXT + CH2_MULTI_EXT2},
    3: {"judge": CH3_JUDGE + CH3_JUDGE_EXT, "single": CH3_SINGLE + CH3_SINGLE_EXT + CH3_SINGLE_EXT2, "multi": CH3_MULTI + CH3_MULTI_EXT},
    4: {"judge": CH4_JUDGE + CH4_JUDGE_EXT, "single": CH4_SINGLE + CH4_SINGLE_EXT, "multi": CH4_MULTI + CH4_MULTI_EXT},
    5: {"judge": CH5_JUDGE + CH5_JUDGE_EXT, "single": CH5_SINGLE + CH5_SINGLE_EXT, "multi": CH5_MULTI + CH5_MULTI_EXT},
    6: {"judge": CH6_JUDGE + CH6_JUDGE_EXT + CH6_JUDGE_EXT2, "single": CH6_SINGLE + CH6_SINGLE_EXT + CH6_SINGLE_EXT2, "multi": CH6_MULTI + CH6_MULTI_EXT + CH6_MULTI_EXT2}
}

# 汇总所有题目
ALL_QUESTIONS = []
for ch_id in range(1, 7):
    for qtype, qlist in [("judge", QUESTION_BANK[ch_id]["judge"]),
                          ("single", QUESTION_BANK[ch_id]["single"]),
                          ("multi", QUESTION_BANK[ch_id]["multi"])]:
        for q in qlist:
            ALL_QUESTIONS.append({**q, "chapter": ch_id, "type": qtype})

# ============================================================
# 工具函数
# ============================================================

def clear_screen():
    """清屏"""
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header(title):
    """打印标题"""
    width = 70
    print("=" * width)
    print(f"  {title}")
    print("=" * width)

def print_separator():
    print("-" * 70)

def get_choice(prompt, valid_options, allow_empty=False):
    """获取用户输入并验证"""
    while True:
        val = input(prompt).strip().upper()
        if allow_empty and val == "":
            return val
        if val in valid_options:
            return val
        print(f"  输入无效，请输入 {', '.join(valid_options)}")

def get_multi_choice(prompt, valid_options):
    """获取多选题答案"""
    while True:
        val = input(prompt).strip().upper()
        if val == "":
            return val
        # 去重并排序
        chars = []
        seen = set()
        for c in val:
            if c in valid_options and c not in seen:
                chars.append(c)
                seen.add(c)
        if chars:
            return "".join(sorted(chars))
        print(f"  输入无效，请从 {', '.join(valid_options)} 中选择")

# ============================================================
# 核心功能
# ============================================================

def practice_mode():
    """分章节刷题模式"""
    clear_screen()
    print_header("分章节刷题模式")

    # 选择章节
    print("\n选择章节：")
    for ch in CHAPTERS:
        print(f"  [{ch['id']}] 第{ch['id']}章 {ch['name']}（占比{ch['weight']}）")
    print("  [0] 返回主菜单")

    ch = get_choice("请输入章节编号：", [str(i) for i in range(0, 7)])
    if ch == "0":
        return
    ch = int(ch)

    # 选择题型
    clear_screen()
    print_header(f"第{ch}章 {CHAPTERS[ch-1]['name']}")
    print("\n选择题型：")
    print("  [1] 判断题")
    print("  [2] 单选题")
    print("  [3] 多选题")
    print("  [4] 全部题型混合")
    print("  [0] 返回")

    t = get_choice("请输入题型编号：", ["0", "1", "2", "3", "4"])
    if t == "0":
        return

    # 获取题目列表
    questions = []
    type_map = {"1": "judge", "2": "single", "3": "multi"}
    if t == "4":
        for qt in ["judge", "single", "multi"]:
            for q in QUESTION_BANK[ch][qt]:
                questions.append((q, qt))
    else:
        qt = type_map[t]
        for q in QUESTION_BANK[ch][qt]:
            questions.append((q, qt))

    if not questions:
        input("该章节暂无题目，按回车返回...")
        return

    random.shuffle(questions)
    do_quiz(ch, questions, "practice")


def exam_mode():
    """模拟考试模式（从所有章节随机抽题）"""
    clear_screen()
    print_header("模拟考试模式")
    print("\n模拟考试说明：")
    print("  · 从全部6章随机抽取题目")
    print("  · 判断题5题 + 单选题30题 + 多选题15题 = 50题")
    print("  · 答完显示成绩和详细报告")
    print()

    input("按回车开始模拟考试...")

    # 按题型抽题
    judges = [q for q in ALL_QUESTIONS if q["type"] == "judge"]
    singles = [q for q in ALL_QUESTIONS if q["type"] == "single"]
    multis = [q for q in ALL_QUESTIONS if q["type"] == "multi"]

    selected = []
    selected.extend(random.sample(judges, min(5, len(judges))))
    selected.extend(random.sample(singles, min(30, len(singles))))
    selected.extend(random.sample(multis, min(15, len(multis))))
    random.shuffle(selected)

    # 转为 (q, type) 格式
    questions = [(q, q["type"]) for q in selected]
    do_quiz(None, questions, "exam")


def random_mode():
    """随机抽题模式"""
    clear_screen()
    print_header("随机抽题模式")

    try:
        n = int(input("请输入想刷的题目数量（默认10）：") or "10")
        n = max(1, min(n, len(ALL_QUESTIONS)))
    except ValueError:
        n = 10

    judges = [q for q in ALL_QUESTIONS if q["type"] == "judge"]
    singles = [q for q in ALL_QUESTIONS if q["type"] == "single"]
    multis = [q for q in ALL_QUESTIONS if q["type"] == "multi"]

    # 按比例抽取
    n_judge = max(1, round(n * len(judges) / len(ALL_QUESTIONS)))
    n_single = max(1, round(n * len(singles) / len(ALL_QUESTIONS)))
    n_multi = max(1, round(n * len(multis) / len(ALL_QUESTIONS)))

    selected = []
    selected.extend(random.sample(judges, min(n_judge, len(judges))))
    selected.extend(random.sample(singles, min(n_single, len(singles))))
    selected.extend(random.sample(multis, min(n_multi, len(multis))))
    random.shuffle(selected)

    selected = selected[:n]
    questions = [(q, q["type"]) for q in selected]
    do_quiz(None, questions, "random")


def do_quiz(chapter, questions, mode):
    """执行答题循环"""
    clear_screen()
    if chapter:
        print_header(f"第{chapter}章 {CHAPTERS[chapter-1]['name']} - 刷题")
    else:
        mode_names = {"exam": "模拟考试", "random": "随机抽题"}
        print_header(f"{mode_names.get(mode, '刷题')}")

    total = len(questions)
    correct = 0
    wrong_list = []
    for idx, (q, qtype) in enumerate(questions, 1):
        clear_screen()
        ch_name = CHAPTERS[q["chapter"]-1]["name"] if "chapter" in q else "综合"
        type_names = {"judge": "判断题", "single": "单选题", "multi": "多选题"}
        qt_name = type_names.get(qtype, "")

        print_header(f"第 {idx}/{total} 题 [{ch_name}] [{qt_name}]")
        print(f"  题号：{q['id']}")
        print()
        print(f"  {q['question']}")
        print()

        if qtype == "judge":
            print("  请判断：")
            print("    √ 正确")
            print("    × 错误")
            user_ans = get_choice("  你的答案（√/×）：", ["√", "×"])
            correct_ans = q["answer"]

        elif qtype == "single":
            for opt in q["options"]:
                print(f"  {opt}")
            user_ans = get_choice("  你的答案（A/B/C/D）：", ["A", "B", "C", "D"])
            correct_ans = q["answer"]

        elif qtype == "multi":
            for opt in q["options"]:
                print(f"  {opt}")
            print("  （输入选项字母，如：ABC）")
            valid_opts = [chr(65+i) for i in range(len(q["options"]))]
            user_ans = get_multi_choice("  你的答案：", valid_opts)
            correct_ans = q["answer"]

        is_correct = (user_ans == correct_ans)
        if is_correct:
            correct += 1
            print(f"\n  [OK] 正确！")
        else:
            print(f"\n  [X] 错误！")
            print(f"  你的答案：{user_ans}")
            print(f"  正确答案：{correct_ans}")
            wrong_list.append((q, qtype, user_ans, correct_ans))

        print_separator()
        print(f"  [解析] {q['analysis']}")
        print_separator()

        if is_correct:
            print("  [OK] 你的回答正确！")
        else:
            print("  [X] 你的回答错误，请牢记解析内容。")
        print()

        if idx < total:
            cmd = input("  按回车继续（输入 q 返回菜单）...")
            if cmd.lower() == 'q':
                break

    # 显示结果
    show_result(total, correct, wrong_list)


def show_result(total, correct, wrong_list):
    """显示答题结果"""
    clear_screen()
    print_header("[报告] 答题报告")
    print(f"\n  总题数：{total}")
    print(f"  答对：{correct}")
    print(f"  答错：{len(wrong_list)}")
    if total > 0:
        pct = correct / total * 100
        print(f"  正确率：{pct:.1f}%")
        if pct >= 90:
            print("  评价：***** 非常优秀！")
        elif pct >= 80:
            print("  评价：**** 良好，继续加油！")
        elif pct >= 60:
            print("  评价：*** 及格，需要加强薄弱章节！")
        else:
            print("  评价：** 不及格，建议重点复习！")
    print()

    if wrong_list:
        print_separator()
        print("[错题本] 错题回顾：")
        print_separator()
        for wq, _, ua, ca in wrong_list:
            ch_name = CHAPTERS[wq["chapter"]-1]["name"] if "chapter" in wq else "综合"
            print(f"  [{ch_name}] {wq['id']} - {wq['question'][:60]}...")
            print(f"    你的答案：{ua}  |  正确答案：{ca}")
            print()
        input("按回车继续...")


def show_wrong_book():
    """错题本功能（当前会话）"""
    print("\n  错题本功能在答题结束后自动显示错题回顾。")
    print("  如需持久化保存，建议将错题截图或手动记录。")
    input("\n  按回车返回...")


def show_stats():
    """显示题库统计信息"""
    clear_screen()
    print_header("[统计] 题库统计")
    print(f"\n  总题目数：{len(ALL_QUESTIONS)}")
    print()
    print(f"  {'章节':<30} {'判断':>4} {'单选':>4} {'多选':>4} {'合计':>4}")
    print("-" * 55)
    total_j = total_s = total_m = 0
    for ch in CHAPTERS:
        cid = ch["id"]
        nj = len(QUESTION_BANK[cid]["judge"])
        ns = len(QUESTION_BANK[cid]["single"])
        nm = len(QUESTION_BANK[cid]["multi"])
        total_j += nj; total_s += ns; total_m += nm
        print(f"  第{cid}章 {ch['name']:<20} {nj:>4} {ns:>4} {nm:>4} {nj+ns+nm:>4}")
    print("-" * 55)
    print(f"  {'合计':<30} {total_j:>4} {total_s:>4} {total_m:>4} {total_j+total_s+total_m:>4}")
    print()
    print("  章节占比：")
    for ch in CHAPTERS:
        print(f"    第{ch['id']}章 {ch['name']}（{ch['weight']}）")
    print()
    print("  题型分布：")
    print(f"    判断题：{total_j}题")
    print(f"    单选题：{total_s}题")
    print(f"    多选题：{total_m}题")
    print()
    input("按回车返回...")


def show_reference():
    """显示高频速查表"""
    clear_screen()
    print_header("[速查] 高频必背速查表")
    print("""
┌─────┬─────────────────┬──────────────────────────┐
│ 等级 │ RTO             │ RPO                      │
├─────┼─────────────────┼──────────────────────────┤
│ 1级 │ ≤2天            │ 1~7天                    │
│ 2级 │ ≤24小时         │ 数小时~1天               │
│ 3级 │ ≤12小时         │ 数小时~1天               │
│ 4级 │ ≤6小时          │ <15分钟                  │
│ 5级 │ 数分钟~2天      │ 0~30分钟                 │
│ 6级 │ 数分钟（秒级）   │ 0                        │
└─────┴─────────────────┴──────────────────────────┘

【部署形态选型】
  维度        | 集中式          | 分布式
  TPS         | < 2万           | > 2万
  数据容量    | < 24TB          | > 24TB
  SQL复杂度   | 复杂（可不改）   | 简单（需改造）
  扩容方式    | 垂直扩容        | 在线水平扩容

【关键数字】
  · 单节点tpmC：150万
  · 32节点分布式tpmC：1500万
  · 轻量化管理节点：3台
  · HCS标准管理节点：17台
  · AZ内时延：<0.25ms | 跨AZ时延：<2ms | 跨Region：<20ms
  · 存储预留比例：30% | 单DN利用率：≤70%
  · 在线扩容影响：<5% | 只读阈值：85%

【存储引擎】
  AStore → Append Update | Insert多Update少 | 膨胀大
  UStore → In-place Update | Update频繁 | 膨胀小 | 支持闪回
""")
    input("按回车返回...")


# ============================================================
# 主菜单
# ============================================================

def main_menu():
    """显示主菜单"""
    while True:
        clear_screen()
        print("""
╔══════════════════════════════════════════════════════════╗
║         HCCDE-GaussDB 理论考题刷题系统 v2.0             ║
║      按考试大纲六大章节分章精编 · 含解析 · 自动判分     ║
╚══════════════════════════════════════════════════════════╝
""")
        print(f"  题库总量：{len(ALL_QUESTIONS)} 题")
        print(f"  更新日期：2026年5月")
        print()
        print("  ┌─────────────────────────────────────────────┐")
        print("  │  [1] 分章节刷题   按章节/题型针对性练习      │")
        print("  │  [2] 随机抽题     从全部题目中随机抽取       │")
        print("  │  [3] 模拟考试     按正式考试标准随机组卷     │")
        print("  │  [4] 题库统计     查看题库章节/题型分布      │")
        print("  │  [5] 高频速查     查看必背知识点速查表       │")
        print("  │  [0] 退出程序                                │")
        print("  └─────────────────────────────────────────────┘")
        print()

        choice = get_choice("  请选择功能（0-5）：", ["0", "1", "2", "3", "4", "5"])

        if choice == "1":
            practice_mode()
        elif choice == "2":
            random_mode()
        elif choice == "3":
            exam_mode()
        elif choice == "4":
            show_stats()
        elif choice == "5":
            show_reference()
        elif choice == "0":
            clear_screen()
            print("\n  感谢使用，祝考试顺利！\n")
            sys.exit(0)


# ============================================================
# 程序入口
# ============================================================

if __name__ == "__main__":
    try:
        main_menu()
    except KeyboardInterrupt:
        print("\n\n  用户中断，退出程序。\n")
        sys.exit(0)

