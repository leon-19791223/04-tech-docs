#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HCCDE-GaussDB 考试验证系统
参考考试宝App设计 - 章节练习、模拟考试、错题重练、考试大纲
"""
import sys
import os
import json
import random
import tkinter as tk
from tkinter import ttk, messagebox

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    from hccde_quiz import CHAPTERS, QUESTION_BANK, ALL_QUESTIONS
except ImportError:
    messagebox.showerror("[错误]", "无法加载题库文件 hccde_quiz.py")
    sys.exit(1)

# ── 配色（简洁专业风格）──
C_PRIMARY = "#2b5f8a"      # 主色 - 稳重的专业蓝
C_PRIMARY_DARK = "#1a3f5c" # 深蓝
C_PRIMARY_LIGHT = "#eef3f8" # 浅蓝背景
C_ACCENT = "#3b8fc2"       # 强调色
C_GRAY = "#666"
C_GRAY_LIGHT = "#f2f4f8"
C_GRAY_BG = "#f8f9fc"
C_WHITE = "#ffffff"
C_GREEN = "#2a9d64"        # 绿色
C_RED = "#d9304f"          # 红色
C_YELLOW = "#e8a820"       # 黄色
C_ORANGE = "#d97c15"       # 橙色
C_BORDER = "#dce3ed"
C_TEXT = "#1e2a3a"
C_TEXT_SUB = "#66758f"     # 次级文字

# ── 各章节配色 ──
CHAPTER_COLORS = {
    1: "#2b5f8a",   # 蓝
    2: "#27ae60",   # 绿
    3: "#e67e22",   # 橙
    4: "#e74c3c",   # 红
    5: "#8e44ad",   # 紫
    6: "#16a085",   # 青
}

# ── 向后兼容别名 ──
C_BLUE = C_PRIMARY
C_BLUE_DARK = C_PRIMARY_DARK
C_BLUE_LIGHT = C_PRIMARY_LIGHT
C_CYAN = C_ACCENT
C_CYAN_DARK = C_ACCENT
C_BLUE_MID = C_PRIMARY

# ── 数据持久化目录 ──
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
os.makedirs(DATA_DIR, exist_ok=True)
DATA_FILE = os.path.join(DATA_DIR, "user_data.json")

def load_user_data():
    """从JSON文件加载用户数据（错题本、答题记录）。"""
    if not os.path.exists(DATA_FILE):
        return {"wrong_book": [], "perf_data": []}
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"wrong_book": [], "perf_data": []}

def save_user_data(wrong_book, perf_data):
    """保存用户数据到JSON文件。"""
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump({"wrong_book": wrong_book, "perf_data": perf_data}, f,
                      ensure_ascii=False, indent=2)
    except Exception:
        pass

# ── 字体 ──
F_TITLE = ("微软雅黑", 16, "bold")
F_SUB = ("微软雅黑", 13, "bold")
F_BODY = ("微软雅黑", 11)
F_SMALL = ("微软雅黑", 9)
F_BTN = ("微软雅黑", 10)

TYPE_NAMES = {"judge": "[判断]", "single": "[单选]", "multi": "[多选]"}

# ── 考点知识体系 ──
# Each chapter has sub-topics with keyword lists for auto-tagging questions
CHAPTER_TOPICS = {
    1: {
        "name": "软件体系架构",
        "topics": [
            ("五高两易", ["五高两易", "高可用", "高性能", "高安全", "高弹性", "高并发", "易部署", "易迁移"]),
            ("分布式架构", ["GTM", "CN", "DN", "CMS", "分布式", "协调节点", "全局事务"]),
            ("存储引擎", ["AStore", "UStore", "存储引擎", "Append Update", "In-place Update"]),
            ("高并发技术", ["线程池", "SQL Bypass", "Plan Cache", "高并发连接"]),
            ("高可用技术", ["极速RTO", "ALT", "并行回放", "WAL日志", "主备切换", "RTO"]),
            ("执行框架", ["Stream", "分布式执行", "SQL下推"]),
        ]
    },
    2: {
        "name": "数据库规划设计",
        "topics": [
            ("部署形态", ["集中式", "分布式部署", "部署形态", "轻量化", "HCS"]),
            ("容灾方案", ["容灾", "两地三中心", "AZ", "RPO", "RTO", "同城", "异地"]),
            ("硬件规划", ["tpmC", "节点", "TPC-C", "硬件", "服务器"]),
            ("网络规划", ["时延", "带宽", "AZ内", "跨AZ", "网络"]),
        ]
    },
    3: {
        "name": "数据库内核原理",
        "topics": [
            ("事务管理", ["事务", "MVCC", "隔离级别", "提交", "回滚", "并发控制"]),
            ("锁机制", ["锁", "死锁", "行锁", "表锁", "意向锁", "等待"]),
            ("索引原理", ["索引", "B树", "B+", "聚簇", "非聚簇", "唯一索引"]),
            ("SQL引擎", ["SQL引擎", "解析", "优化", "执行计划", "重写", "代价"]),
            ("WAL与Checkpoint", ["WAL", "Checkpoint", "日志", "XLOG", "REDO"]),
            ("内存管理", ["内存", "缓存", "Buffer", "Pool", "Shared Buffer"]),
        ]
    },
    4: {
        "name": "安全管理",
        "topics": [
            ("认证与鉴权", ["认证", "鉴权", "登录", "密码", "SSL", "证书"]),
            ("数据加密", ["加密", "TDE", "透明加密", "密钥", "密文"]),
            ("审计", ["审计", "audit", "日志审计", "行为审计"]),
            ("权限管理", ["权限", "角色", "GRANT", "REVOKE", "用户", "授权"]),
            ("安全加固", ["安全", "加固", "基线", "合规", "防火墙"]),
        ]
    },
    5: {
        "name": "性能调优",
        "topics": [
            ("执行计划", ["执行计划", "EXPLAIN", "全表扫描", "索引扫描", "代价估算"]),
            ("索引优化", ["索引优化", "索引选择", "复合索引", "覆盖索引"]),
            ("参数调优", ["参数", "GUC", "work_mem", "shared_buffers", "配置"]),
            ("SQL优化", ["SQL优化", "SQL改写", "关联查询", "子查询", "JOIN"]),
            ("统计信息", ["统计信息", "ANALYZE", "采样", "直方图", "基线"]),
        ]
    },
    6: {
        "name": "运维与故障处理",
        "topics": [
            ("备份恢复", ["备份", "恢复", "全量备份", "增量备份", "PITR", "RESTORE"]),
            ("监控告警", ["监控", "告警", "Prometheus", "Grafana", "指标"]),
            ("升级扩容", ["升级", "扩容", "扩缩容", "节点扩容", "版本升级"]),
            ("故障处理", ["故障", "宕机", "重建", "修复", "Failover", "切换"]),
            ("主备复制", ["主备", "复制", "流复制", "同步", "异步", "延迟"]),
        ]
    }
}


def get_question_topics(q):
    """Match question text/analysis to knowledge topics. Returns list of topic names."""
    text = q["question"] + " " + q.get("analysis", "")
    ch = q.get("chapter", 0)
    if ch not in CHAPTER_TOPICS:
        return []
    matched = []
    for topic_name, keywords in CHAPTER_TOPICS[ch]["topics"]:
        for kw in keywords:
            if kw.lower() in text.lower():
                matched.append(topic_name)
                break
    return matched if matched else [CHAPTER_TOPICS[ch]["topics"][0][0]]


def get_chapter_counts():
    result = {}
    for ch in CHAPTERS:
        cid = ch["id"]
        nj = len(QUESTION_BANK[cid]["judge"])
        ns = len(QUESTION_BANK[cid]["single"])
        nm = len(QUESTION_BANK[cid]["multi"])
        result[cid] = {"judge": nj, "single": ns, "multi": nm, "total": nj + ns + nm}
    return result


CHAPTER_COUNTS = get_chapter_counts()


def parse_option_text(opt):
    """Parse 'X. text' into (letter, text)"""
    s = opt.strip()
    if len(s) >= 2 and s[1] == '.':
        return s[0], s[2:].strip()
    return "", s


class ExamApp:
    def __init__(self):
        self.win = tk.Tk()
        self.win.title("HCCDE-GaussDB 考试验证系统")
        self.win.geometry("1100x720+150+30")
        self.win.minsize(900, 620)
        self.win.grid_columnconfigure(0, weight=1)
        self.win.grid_rowconfigure(1, weight=1)

        # State
        saved = load_user_data()
        self.wrong_book = saved.get("wrong_book", [])
        self.perf_data = saved.get("perf_data", [])
        self.questions = []
        self.idx = 0
        self.correct_count = 0
        self.wrong_list = []
        self.exam_answers = {}
        self.exam_marked = set()
        self.current_mode = None
        self.current_chapter = 0
        self.current_qtype = "all"
        self.timer_remaining = 0
        self.timer_running = False
        self.timer_job = None
        self.exam_duration_minutes = 30
        self.answered_lbl = None
        self._back_target = None

        self._build_topbar()
        self.container = tk.Frame(self.win, bg=C_GRAY_BG)
        self.container.pack(fill="both", expand=True)
        self._show_splash()

    # ────────────────────────────────────────
    # TOP BAR
    # ────────────────────────────────────────
    def _build_topbar(self):
        bar = tk.Frame(self.win, bg=C_PRIMARY, height=56)
        bar.pack(fill="x")
        bar.pack_propagate(False)

        # Bottom accent border
        tk.Frame(self.win, bg=C_ACCENT, height=2).pack(fill="x")

        self.back_btn = tk.Button(
            bar, text="< 返回", font=F_BODY,
            fg="#a0b8d0", bg=C_PRIMARY, bd=0,
            activebackground=C_PRIMARY_DARK,
            activeforeground=C_WHITE,
            command=self._on_back, state="disabled"
        )
        self.back_btn.pack(side="left", padx=6)

        self.title_lbl = tk.Label(
            bar, text="HCCDE-GaussDB 考试验证系统",
            font=F_SUB, fg=C_WHITE, bg=C_PRIMARY
        )
        self.title_lbl.pack(side="left", padx=12)

        self.status_lbl = tk.Label(
            bar, text="", font=F_SMALL, fg="#8aafcf", bg=C_PRIMARY
        )
        self.status_lbl.pack(side="right", padx=15)

        self.timer_lbl = tk.Label(
            bar, text="", font=("Consolas", 14, "bold"),
            fg=C_WHITE, bg=C_PRIMARY
        )
        # hidden by default

    # ────────────────────────────────────────
    # HELPERS
    # ────────────────────────────────────────
    def _clear(self):
        for w in self.container.winfo_children():
            w.destroy()

    def _on_back(self):
        self._stop_timer()
        if hasattr(self, '_back_target') and self._back_target:
            t = self._back_target
            self._back_target = None
            t()

    def _make_card(self, parent, **kwargs):
        """Create a simple card frame (no binding — call _bind_card after populating children)."""
        card = tk.Frame(
            parent, bg=C_WHITE, cursor="hand2",
            highlightbackground=C_BORDER, highlightthickness=1, **kwargs
        )
        return card

    def _bind_click(self, widget, callback):
        """Recursively bind <Button-1> to widget and all descendants."""
        if isinstance(widget, (tk.Button, tk.Radiobutton, tk.Checkbutton,
                              ttk.Button, tk.Entry, tk.Text, ttk.Combobox)):
            return
        widget.bind("<Button-1>", lambda e: callback())
        try:
            widget.config(cursor="hand2")
        except Exception:
            pass
        for child in widget.winfo_children():
            self._bind_click(child, callback)

    def _bind_card(self, card, callback):
        """Bind click callback to a card and all its descendants."""
        self._bind_click(card, callback)

    def _make_scrollable(self, parent):
        """Create a scrollable canvas+scrollbar in parent. Returns (cv, sb, sf)."""
        outer = tk.Frame(parent, bg=C_GRAY_BG)
        outer.pack(fill="both", expand=True)

        cv = tk.Canvas(outer, bg=C_GRAY_BG, highlightthickness=0)
        sb = ttk.Scrollbar(outer, orient="vertical", command=cv.yview)
        sb.pack(side="right", fill="y")
        cv.pack(side="left", fill="both", expand=True)

        sf = tk.Frame(cv, bg=C_GRAY_BG)
        win_id = cv.create_window((0, 0), window=sf, anchor="nw")

        def _on_cv_cfg(e):
            cv.itemconfig(win_id, width=e.width)
        cv.bind("<Configure>", _on_cv_cfg)
        sf.bind("<Configure>", lambda e: cv.configure(scrollregion=cv.bbox("all")))
        cv.configure(yscrollcommand=sb.set)

        def _mw(e):
            cv.yview_scroll(int(-1 * (e.delta / 120)), "units")
        cv.bind("<MouseWheel>", _mw)
        sf.bind("<MouseWheel>", _mw)

        return cv, sb, sf

    def _auto_save(self):
        """持久化保存用户数据到JSON文件。"""
        save_user_data(self.wrong_book, self.perf_data)

    def _set_back(self, target):
        self._back_target = target
        self.back_btn.config(state="normal" if target else "disabled")

    def _update_title(self, text, status=""):
        self.title_lbl.config(text=text)
        self.status_lbl.config(text=status)

    def _stop_timer(self):
        self.timer_running = False
        if self.timer_job:
            try:
                self.win.after_cancel(self.timer_job)
            except Exception:
                pass
            self.timer_job = None
        self.timer_lbl.pack_forget()

    def _get_ww(self, base=800):
        """Responsive wraplength for practice mode."""
        try:
            w = self.win.winfo_width()
            return max(450, min(base, w - 120))
        except Exception:
            return base

    def _get_ww_sm(self, base=600):
        """Responsive wraplength for exam mode (narrower layout)."""
        try:
            w = self.win.winfo_width()
            return max(300, min(base, w - 320))
        except Exception:
            return base

    # ────────────────────────────────────────
    # SPLASH
    # ────────────────────────────────────────
    def _show_splash(self):
        self._clear()
        self._update_title("", "")
        self._set_back(None)

        c = tk.Frame(self.container, bg=C_PRIMARY)
        c.pack(fill="both", expand=True)

        total_q = sum(c["total"] for c in CHAPTER_COUNTS.values())

        # Centered content
        wrap = tk.Frame(c, bg=C_PRIMARY)
        wrap.place(relx=0.5, rely=0.45, anchor="center")

        # Logo icon block
        logo_f = tk.Frame(wrap, bg=C_WHITE, width=80, height=80, highlightthickness=0)
        logo_f.pack(pady=(0, 15))
        logo_f.pack_propagate(False)
        tk.Label(
            logo_f, text="H", font=("微软雅黑", 36, "bold"),
            fg=C_PRIMARY, bg=C_WHITE
        ).pack(expand=True)

        tk.Label(
            wrap, text="HCCDE-GaussDB", font=("微软雅黑", 26, "bold"),
            fg=C_WHITE, bg=C_PRIMARY
        ).pack()
        tk.Label(
            wrap, text="理论考试验证系统", font=("微软雅黑", 13),
            fg="#8aafcf", bg=C_PRIMARY
        ).pack(pady=(5, 20))

        # Info row
        info_f = tk.Frame(wrap, bg=C_PRIMARY_DARK, padx=20, pady=8)
        info_f.pack()
        tk.Label(
            info_f, text=f"题库 {total_q} 题  |  6 章节  |  3 题型",
            font=("微软雅黑", 10), fg="#8aafcf", bg=C_PRIMARY_DARK
        ).pack()

        # Loading bar
        bar_bg = tk.Frame(wrap, bg=C_PRIMARY_DARK, height=4, width=260)
        bar_bg.pack(pady=(25, 5))
        bar_bg.pack_propagate(False)
        bar_fg = tk.Frame(bar_bg, bg=C_ACCENT, height=4, width=0)
        bar_fg.pack(side="left")

        # Animate the loading bar then show home
        def _animate(step=0):
            w = int(260 * step / 100)
            bar_fg.config(width=w)
            if step < 100:
                self.win.after(12, lambda: _animate(step + 2))
            else:
                self.win.after(300, self._show_home)
        self.win.after(200, _animate)

    # ────────────────────────────────────────
    # HOME
    # ────────────────────────────────────────
    def _show_home(self):
        self._clear()
        self._stop_timer()
        total_q = sum(c["total"] for c in CHAPTER_COUNTS.values())
        self._update_title(
            "HCCDE-GaussDB",
            f"题库 {total_q} 题 | 6 章节 | 3 题型"
        )
        self._set_back(None)

        # Center content wrapper
        wrap = tk.Frame(self.container, bg=C_GRAY_BG)
        wrap.place(relx=0.5, rely=0.42, anchor="center")

        tk.Label(
            wrap, text="HCCDE-GaussDB",
            font=("微软雅黑", 24, "bold"), fg=C_PRIMARY, bg=C_GRAY_BG
        ).pack()
        tk.Label(
            wrap, text="理论考试验证系统",
            font=("微软雅黑", 13), fg=C_TEXT_SUB, bg=C_GRAY_BG
        ).pack(pady=(2, 20))

        cards = [
            ("章节练习", "分章节选题练习", C_PRIMARY, self._show_chapter_select),
            ("随机练习", "跨章节随机抽题", C_CYAN, self._show_random_practice),
            ("模拟考试", "限时组卷模拟", C_GREEN, self._show_exam_setup),
            ("错题重练", f"已收 {len(self.wrong_book)} 题", C_ORANGE, self._show_wrong_review),
            ("智能分析", "诊断+复习建议", C_RED, self._show_ai_analysis),
            ("考试大纲", "考点速查", C_TEXT_SUB, self._show_syllabus),
        ]

        grid = tk.Frame(wrap, bg=C_GRAY_BG)
        grid.pack(pady=5)
        n_cols = 3
        for i, (title, desc, color, cmd) in enumerate(cards):
            r, c = divmod(i, n_cols)
            card = self._make_card(grid, padx=16, pady=12)
            card.grid(row=r, column=c, padx=8, pady=8, sticky="nsew")
            card.config(width=190, height=90)
            card.grid_propagate(False)

            # Left color bar
            tk.Frame(card, bg=color, width=5, height=90).pack(side="left", fill="y")

            # Content
            inner = tk.Frame(card, bg=C_WHITE)
            inner.pack(side="left", fill="both", expand=True, padx=10, pady=8)
            tk.Label(
                inner, text=title, font=("微软雅黑", 14, "bold"),
                fg=C_TEXT, bg=C_WHITE
            ).pack(anchor="w")
            tk.Label(
                inner, text=desc, font=F_SMALL,
                fg=C_TEXT_SUB, bg=C_WHITE, justify="left"
            ).pack(anchor="w", pady=(2, 0))
            self._bind_card(card, cmd)

        for i in range(n_cols):
            grid.grid_columnconfigure(i, weight=1)
        grid.grid_rowconfigure(0, weight=1)
        grid.grid_rowconfigure(1, weight=1)

        # Bottom hint
        tk.Label(
            wrap, text=f"共 {total_q} 道题目 | 含完整解析 | 自动判分"
                      f" | 考试: 60题/90min",
            font=F_SMALL, fg=C_TEXT_SUB, bg=C_GRAY_BG
        ).pack(pady=(15, 0))

    # ────────────────────────────────────────
    # CHAPTER SELECT
    # ────────────────────────────────────────
    def _show_chapter_select(self):
        self._clear()
        self._update_title("章节练习", "请选择章节")
        self._set_back(self._show_home)

        tk.Label(
            self.container, text="选择章节",
            font=("微软雅黑", 18, "bold"), fg=C_PRIMARY, bg=C_GRAY_BG
        ).pack(pady=(30, 5))
        tk.Label(
            self.container, text="点击章节进入练习，可选择题型模式",
            font=F_BODY, fg=C_TEXT_SUB, bg=C_GRAY_BG
        ).pack()

        # Scrollable content area
        _, _, sf = self._make_scrollable(self.container)

        for ch in CHAPTERS:
            cid = ch["id"]
            cnt = CHAPTER_COUNTS[cid]
            color = CHAPTER_COLORS.get(cid, C_PRIMARY)
            card = self._make_card(sf, padx=16, pady=14, width=540, height=100)
            card.pack(pady=7)
            card.pack_propagate(False)

            # ── Colored chapter logo icon ──
            icon_f = tk.Frame(card, bg=color, width=56, height=56, highlightthickness=0)
            icon_f.pack(side="left", padx=(14, 14), pady=8)
            icon_f.pack_propagate(False)
            tk.Label(
                icon_f, text=str(cid), font=("微软雅黑", 22, "bold"),
                fg=C_WHITE, bg=color
            ).pack(expand=True)

            # ── Content area ──
            inner = tk.Frame(card, bg=C_WHITE)
            inner.pack(side="left", fill="both", expand=True)

            tk.Label(
                inner, text=f"第{cid}章  {ch['name']}",
                font=("微软雅黑", 14, "bold"), fg=C_TEXT, bg=C_WHITE
            ).pack(anchor="w", pady=(2, 4))

            # Type count badges
            bf = tk.Frame(inner, bg=C_WHITE)
            bf.pack(anchor="w")
            for text, badge_color in [
                (f"判断题 {cnt['judge']}", C_PRIMARY),
                (f"单选题 {cnt['single']}", C_GREEN),
                (f"多选题 {cnt['multi']}", C_ORANGE),
            ]:
                tk.Label(
                    bf, text=text, font=("微软雅黑", 8),
                    fg=badge_color, bg=C_PRIMARY_LIGHT, padx=6, pady=1
                ).pack(side="left", padx=2)

            # Bottom row
            bot = tk.Frame(inner, bg=C_WHITE)
            bot.pack(fill="x", pady=(4, 0))
            tk.Label(
                bot, text=f"共 {cnt['total']} 题", font=F_SMALL,
                fg=C_TEXT_SUB, bg=C_WHITE
            ).pack(side="left")
            tk.Label(
                bot, text=f"考纲占比 {ch['weight']}", font=F_SMALL,
                fg=C_TEXT_SUB, bg=C_WHITE
            ).pack(side="right")

            # ── Right arrow indicator ──
            tk.Label(
                card, text="›", font=("微软雅黑", 26, "bold"),
                fg=C_BORDER, bg=C_WHITE
            ).pack(side="right", padx=(5, 10))

            self._bind_card(card, lambda cid=cid: self._show_type_select(cid))

        # Bottom spacer
        tk.Label(sf, text="", bg=C_GRAY_BG).pack(pady=10)

    # ────────────────────────────────────────
    # TYPE SELECT
    # ────────────────────────────────────────
    def _show_type_select(self, chapter_id):
        self._clear()
        ch = next(c for c in CHAPTERS if c["id"] == chapter_id)
        ch_color = CHAPTER_COLORS.get(chapter_id, C_PRIMARY)
        self._update_title(f"第{chapter_id}章  {ch['name']}", "选择题型")
        self._set_back(self._show_chapter_select)
        cnt = CHAPTER_COUNTS[chapter_id]

        # Header with chapter color accent
        hdr_frame = tk.Frame(self.container, bg=C_GRAY_BG)
        hdr_frame.pack(pady=(25, 5))
        tk.Label(
            hdr_frame, text=f"第{chapter_id}章  {ch['name']}",
            font=("微软雅黑", 18, "bold"), fg=C_PRIMARY, bg=C_GRAY_BG
        ).pack(side="left")
        tk.Label(
            hdr_frame, text=f"  {ch.get('weight', '')}", font=F_SMALL,
            fg=ch_color, bg=C_PRIMARY_LIGHT, padx=8, pady=2
        ).pack(side="left", padx=10)

        tk.Label(
            self.container,
            text=f"共 {cnt['total']} 道题目  |  考纲占比 {ch['weight']}",
            font=F_BODY, fg=C_TEXT_SUB, bg=C_GRAY_BG
        ).pack()

        wrap = tk.Frame(self.container, bg=C_GRAY_BG)
        wrap.place(relx=0.5, rely=0.35, anchor="center")

        types = [
            ("全部题目",
             f"判断{cnt['judge']} + 单选{cnt['single']} + 多选{cnt['multi']} = {cnt['total']}题",
             C_PRIMARY, lambda: self._show_practice(chapter_id, "all")),
            ("判断题", f"{cnt['judge']}道", C_PRIMARY,
             lambda: self._show_practice(chapter_id, "judge")),
            ("单选题", f"{cnt['single']}道", C_GREEN,
             lambda: self._show_practice(chapter_id, "single")),
            ("多选题", f"{cnt['multi']}道", C_ORANGE,
             lambda: self._show_practice(chapter_id, "multi")),
        ]

        for title, desc, color, cmd in types:
            card = self._make_card(wrap, padx=18, pady=14, width=420, height=80)
            card.pack(pady=7)
            card.pack_propagate(False)

            # Left accent bar
            tk.Frame(card, bg=color, width=5, height=46).pack(side="left", fill="y")

            inner = tk.Frame(card, bg=C_WHITE)
            inner.pack(side="left", fill="both", expand=True, padx=12, pady=4)
            tk.Label(
                inner, text=title, font=("微软雅黑", 13, "bold"),
                fg=C_TEXT, bg=C_WHITE
            ).pack(anchor="w")
            tk.Label(
                inner, text=desc, font=F_SMALL, fg=C_TEXT_SUB, bg=C_WHITE
            ).pack(anchor="w")
            self._bind_card(card, cmd)

    # ────────────────────────────────────────
    # RANDOM PRACTICE
    # ────────────────────────────────────────
    def _show_random_practice(self):
        self._clear()
        self._stop_timer()
        self._update_title("随机练习", "跨章节随机抽题")
        self._set_back(self._show_home)

        _, _, sf = self._make_scrollable(self.container)

        tk.Label(
            sf, text="随机练习", font=("微软雅黑", 18, "bold"),
            fg=C_CYAN, bg=C_GRAY_BG
        ).pack(pady=(30, 20))

        # Question count
        g1 = tk.LabelFrame(
            sf, text=" 题目数量 ", font=F_SUB,
            bg=C_WHITE, fg=C_CYAN, padx=20, pady=15
        )
        g1.pack(fill="x", padx=40, pady=8)
        self.rand_count = tk.StringVar(value="20")
        for val in ("10", "20", "30", "50"):
            tk.Radiobutton(
                g1, text=f"{val} 题", variable=self.rand_count,
                value=val, font=F_BTN, bg=C_WHITE
            ).pack(side="left", padx=15, pady=5)

        # Type filter
        g2 = tk.LabelFrame(
            sf, text=" 题型过滤 ", font=F_SUB,
            bg=C_WHITE, fg=C_CYAN, padx=20, pady=15
        )
        g2.pack(fill="x", padx=40, pady=8)
        self.rand_type = tk.StringVar(value="all")
        for val, text in [("all", "全部题型"), ("judge", "仅判断"),
                          ("single", "仅单选"), ("multi", "仅多选")]:
            tk.Radiobutton(
                g2, text=text, variable=self.rand_type,
                value=val, font=F_BTN, bg=C_WHITE
            ).pack(side="left", padx=15, pady=5)

        # Start button
        btn = tk.Button(
            sf, text="开始练习", font=("微软雅黑", 14, "bold"),
            bg=C_CYAN, fg=C_WHITE, padx=50, pady=8, relief="flat", cursor="hand2",
            activebackground=C_PRIMARY, activeforeground=C_WHITE,
            command=self._start_random_practice
        )
        btn.pack(pady=30)
        btn.bind("<Enter>", lambda e: btn.config(bg=C_PRIMARY))
        btn.bind("<Leave>", lambda e: btn.config(bg=C_CYAN))

    def _start_random_practice(self):
        count = int(self.rand_count.get())
        qtype = self.rand_type.get()

        pool = []
        for q in ALL_QUESTIONS:
            if qtype == "all" or q["type"] == qtype:
                pool.append((q, q["type"]))

        if not pool:
            messagebox.showinfo("提示", "该条件暂无题目")
            return

        random.shuffle(pool)
        selected = pool[:min(count, len(pool))]

        self._clear()
        self._stop_timer()
        self.current_mode = "practice"
        self.current_chapter = 0
        self.current_qtype = qtype
        self.correct_count = 0
        self.wrong_list = []
        self.questions = selected
        self.idx = 0
        self._update_title("随机练习", f"共 {len(selected)} 题")
        self._set_back(self._show_home)
        self._build_practice_ui()

    # ────────────────────────────────────────
    # PRACTICE MODE
    # ────────────────────────────────────────
    def _show_practice(self, chapter_id, qtype):
        self._clear()
        self._stop_timer()
        self.current_mode = "practice"
        self.current_chapter = chapter_id
        self.current_qtype = qtype
        self.correct_count = 0
        self.wrong_list = []
        self.idx = 0

        questions = []
        if chapter_id == 0:
            for q in ALL_QUESTIONS:
                if qtype == "all" or q["type"] == qtype:
                    questions.append((q, q["type"]))
        else:
            for qt in (["judge", "single", "multi"] if qtype == "all" else [qtype]):
                for q in QUESTION_BANK[chapter_id][qt]:
                    questions.append((q, qt))

        if not questions:
            messagebox.showinfo("提示", "该章节暂无题目")
            self._show_type_select(chapter_id)
            return

        random.shuffle(questions)
        self.questions = questions
        ch_name = next(c["name"] for c in CHAPTERS if c["id"] == chapter_id)
        self._update_title(f"章节练习 - 第{chapter_id}章 {ch_name}",
                           f"共 {len(questions)} 题")
        self._set_back(lambda: self._show_type_select(chapter_id))
        self._build_practice_ui()

    def _build_practice_ui(self):
        self._clear()

        # Top progress bar
        self.progress_frame = tk.Frame(self.container, bg=C_WHITE, height=8)
        self.progress_frame.pack(fill="x")
        self.progress_bar = tk.Frame(
            self.progress_frame, bg=C_BLUE, height=8, width=0
        )
        self.progress_bar.pack(side="left")

        self.q_area = tk.Frame(self.container, bg=C_GRAY_BG)
        self.q_area.pack(fill="both", expand=True, padx=30, pady=15)
        self._render_practice_question()

    def _render_practice_question(self):
        for w in self.q_area.winfo_children():
            w.destroy()

        if self.idx >= len(self.questions):
            self._show_practice_result()
            return

        q, qtype = self.questions[self.idx]
        total = len(self.questions)

        pct = self.idx / total * 100
        self.progress_bar.config(width=int(pct * 10.5))

        header = tk.Frame(self.q_area, bg=C_GRAY_BG)
        header.pack(fill="x", pady=(0, 10))
        tk.Label(
            header, text=f"第 {self.idx+1}/{total} 题",
            font=("微软雅黑", 12, "bold"), fg=C_BLUE, bg=C_GRAY_BG
        ).pack(side="left")

        tc = {"judge": C_BLUE, "single": C_GREEN, "multi": C_ORANGE}
        tk.Label(
            header, text=TYPE_NAMES[qtype], font=F_SMALL,
            fg=C_WHITE, bg=tc[qtype], padx=8, pady=2
        ).pack(side="left", padx=10)

        # Question card with top accent bar
        q_card = tk.Frame(
            self.q_area, bg=C_WHITE,
            highlightbackground=C_BORDER, highlightthickness=1
        )
        q_card.pack(fill="x", pady=5)
        tk.Frame(q_card, bg=C_ACCENT, height=3).pack(fill="x")

        # Topic badge
        topics = get_question_topics(q)
        if topics:
            t_frame = tk.Frame(q_card, bg=C_WHITE)
            t_frame.pack(fill="x", padx=20, pady=(12, 0))
            tk.Label(
                t_frame, text="考点", font=("微软雅黑", 8),
                fg=C_WHITE, bg=C_PRIMARY, padx=5, pady=1
            ).pack(side="left")
            tk.Label(
                t_frame, text=topics[0], font=("微软雅黑", 8),
                fg=C_PRIMARY, bg=C_PRIMARY_LIGHT, padx=7, pady=1
            ).pack(side="left", padx=5)

        tk.Label(
            q_card, text=q["question"], font=F_BODY,
            wraplength=self._get_ww(), justify="left", bg=C_WHITE,
            padx=20, pady=20
        ).pack(anchor="w")

        # Options
        opt_frame = tk.Frame(self.q_area, bg=C_GRAY_BG)
        opt_frame.pack(fill="x", pady=10)

        self.ans_var = tk.StringVar(value="")
        self.multi_vars = {}

        if qtype == "judge":
            for val, txt in [("√", "正确"), ("×", "错误")]:
                btn = tk.Radiobutton(
                    opt_frame, text=f"  {txt}", variable=self.ans_var,
                    value=val, font=F_BODY, bg=C_WHITE,
                    indicatoron=0, width=18, padx=15, pady=8,
                    selectcolor=C_CYAN, activebackground=C_BLUE_LIGHT
                )
                btn.pack(side="left", padx=15)
        elif qtype == "single":
            sing_frames = []
            for opt in q.get("options", []):
                letter, text = parse_option_text(opt)
                f = tk.Frame(
                    opt_frame, bg=C_WHITE, highlightbackground=C_BORDER,
                    highlightthickness=2, cursor="hand2"
                )
                f.pack(fill="x", pady=5)
                badge = tk.Label(
                    f, text=letter, font=("Consolas", 12, "bold"),
                    fg=C_WHITE, bg=C_PRIMARY, width=3, height=1
                )
                badge.pack(side="left", padx=10, pady=10)
                rb = tk.Radiobutton(
                    f, text=text, variable=self.ans_var, value=letter,
                    font=F_BODY, bg=C_WHITE, activebackground=C_PRIMARY_LIGHT
                )
                rb.pack(side="left", padx=5, fill="x", expand=True)
                for wgt in (f, badge):
                    wgt.bind("<Button-1>", lambda e, v=letter: self.ans_var.set(v))
                sing_frames.append((letter, f))
            # Update border when selection changes
            def _upd_sing(*_):
                sel = self.ans_var.get()
                for l, fr in sing_frames:
                    fr.config(highlightbackground=C_ACCENT if l == sel else C_BORDER,
                              highlightthickness=2)
            self.ans_var.trace_add("write", _upd_sing)
        else:  # multi
            for opt in q.get("options", []):
                letter, text = parse_option_text(opt)
                var = tk.BooleanVar()
                self.multi_vars[letter] = var
                f = tk.Frame(
                    opt_frame, bg=C_WHITE, highlightbackground=C_BORDER,
                    highlightthickness=2, cursor="hand2"
                )
                f.pack(fill="x", pady=5)
                badge = tk.Label(
                    f, text=letter, font=("Consolas", 12, "bold"),
                    fg=C_WHITE, bg=C_PRIMARY, width=3, height=1
                )
                badge.pack(side="left", padx=10, pady=10)
                txt_lbl = tk.Label(
                    f, text=text, font=F_BODY, bg=C_WHITE, anchor="w"
                )
                txt_lbl.pack(side="left", padx=5, fill="x", expand=True)

                def _mtog(ev, v=letter, b=badge, vv=var, fr=f):
                    new = not vv.get()
                    vv.set(new)
                    b.config(bg=C_PRIMARY_DARK if new else C_PRIMARY)
                    fr.config(highlightbackground=C_ACCENT if new else C_BORDER)
                for wgt in (f, badge, txt_lbl):
                    wgt.bind("<Button-1>", _mtog, add="+")

        # Submit button
        btn_frame = tk.Frame(self.q_area, bg=C_GRAY_BG)
        btn_frame.pack(pady=20)
        submit_btn = tk.Button(
            btn_frame, text="确认答案", font=("微软雅黑", 12, "bold"),
            bg=C_PRIMARY, fg=C_WHITE, padx=50, pady=8,
            relief="flat", cursor="hand2",
            activebackground=C_PRIMARY_DARK,
            activeforeground=C_WHITE,
            command=self._check_practice_answer
        )
        submit_btn.pack()
        # Hover effect
        def _on_enter(e): submit_btn.config(bg=C_ACCENT)
        def _on_leave(e): submit_btn.config(bg=C_PRIMARY)
        submit_btn.bind("<Enter>", _on_enter)
        submit_btn.bind("<Leave>", _on_leave)

    def _check_practice_answer(self):
        q, qtype = self.questions[self.idx]

        if qtype == "multi":
            selected = "".join(sorted(
                k for k, v in self.multi_vars.items() if v.get()
            ))
            if not selected:
                messagebox.showinfo("提示", "请至少选择一个选项")
                return
            user_ans = selected
        else:
            user_ans = self.ans_var.get()
            if not user_ans:
                messagebox.showinfo("提示", "请选择一个答案")
                return

        correct = q["answer"]
        is_correct = (user_ans == correct)
        self.perf_data.append((q, qtype, is_correct))

        if is_correct:
            self.correct_count += 1
        else:
            self.wrong_list.append((q, qtype, user_ans, correct))
            # 去重：同一题不重复收录
            qid = q.get("id", "")
            if not any(w[0].get("id", "") == qid for w in self.wrong_book):
                self.wrong_book.append((q, qtype, user_ans, correct))
        self._auto_save()

        self._show_practice_feedback(is_correct, user_ans, correct)

    def _advance_practice(self):
        """Go to next practice question."""
        self.idx += 1
        if self.idx < len(self.questions):
            self._render_practice_question()
        else:
            self._show_practice_result()

    def _finish_practice(self):
        """Finish practice and show results."""
        self.idx += 1
        self._show_practice_result()

    def _show_practice_feedback(self, is_correct, user_ans, correct_ans):
        for w in self.q_area.winfo_children():
            w.destroy()

        q, qtype = self.questions[self.idx]
        color = C_GREEN if is_correct else C_RED
        text = "回答正确 !" if is_correct else "回答错误"
        symbol = "✓" if is_correct else "✗"

        # Big result banner with symbol
        banner = tk.Frame(self.q_area, bg=color)
        banner.pack(fill="x", ipady=10)
        tk.Label(
            banner, text=symbol, font=("微软雅黑", 20, "bold"),
            fg=C_WHITE, bg=color
        ).pack(side="left", padx=(20, 5))
        tk.Label(
            banner, text=text, font=("微软雅黑", 14, "bold"),
            fg=C_WHITE, bg=color
        ).pack(side="left")

        # Answer comparison card with left color bar
        ans_card = tk.Frame(
            self.q_area, bg=C_WHITE,
            highlightbackground=color, highlightthickness=1
        )
        ans_card.pack(fill="x", pady=(15, 5))
        tk.Frame(ans_card, bg=color, width=5).pack(side="left", fill="y")

        inner = tk.Frame(ans_card, bg=C_WHITE)
        inner.pack(side="left", fill="both", expand=True, padx=15, pady=12)

        if not is_correct:
            tk.Label(
                inner, text=f"你的答案: {user_ans}", font=F_BODY,
                fg=C_RED, bg=C_WHITE
            ).pack(anchor="w")
            tk.Label(
                inner, text=f"正确答案: {correct_ans}", font=F_BODY,
                fg=C_GREEN, bg=C_WHITE
            ).pack(anchor="w", pady=(2, 0))
        else:
            tk.Label(
                inner, text=f"答案: {correct_ans}", font=F_BODY,
                fg=C_GREEN, bg=C_WHITE
            ).pack(anchor="w")

        # Analysis card with top accent bar
        af = tk.Frame(
            self.q_area, bg=C_WHITE,
            highlightbackground=C_BORDER, highlightthickness=1
        )
        af.pack(fill="x", pady=10)
        tk.Frame(af, bg=C_ACCENT, height=2).pack(fill="x")

        ah = tk.Frame(af, bg=C_WHITE)
        ah.pack(fill="x", padx=15, pady=(10, 0))
        tk.Label(
            ah, text="解析", font=("微软雅黑", 9, "bold"),
            fg=C_WHITE, bg=C_PRIMARY, padx=6, pady=2
        ).pack(side="left")

        tk.Label(
            af, text=q["analysis"], font=F_SMALL, fg=C_TEXT,
            wraplength=self._get_ww(), justify="left", bg=C_WHITE,
            padx=15
        ).pack(anchor="w", pady=(8, 12))

        # Manual navigation buttons
        nav_f = tk.Frame(self.q_area, bg=C_GRAY_BG)
        nav_f.pack(pady=15)

        is_last = (self.idx + 1 >= len(self.questions))

        if not is_last:
            btn_next = tk.Button(
                nav_f, text="下一题  >", font=("微软雅黑", 12, "bold"),
                bg=C_PRIMARY, fg=C_WHITE, padx=40, pady=8,
                relief="flat", cursor="hand2",
                activebackground=C_ACCENT, activeforeground=C_WHITE,
                command=self._advance_practice
            )
            btn_next.pack(side="left", padx=5)
            def _ne(e): btn_next.config(bg=C_ACCENT)
            def _nl(e): btn_next.config(bg=C_PRIMARY)
            btn_next.bind("<Enter>", _ne)
            btn_next.bind("<Leave>", _nl)
        else:
            btn_finish = tk.Button(
                nav_f, text="查看结果报告", font=("微软雅黑", 12, "bold"),
                bg=C_GREEN, fg=C_WHITE, padx=40, pady=8,
                relief="flat", cursor="hand2",
                activebackground="#218c53", activeforeground=C_WHITE,
                command=self._finish_practice
            )
            btn_finish.pack(side="left", padx=5)
            def _fe(e): btn_finish.config(bg="#218c53")
            def _fl(e): btn_finish.config(bg=C_GREEN)
            btn_finish.bind("<Enter>", _fe)
            btn_finish.bind("<Leave>", _fl)

    def _show_practice_result(self):
        self._clear()
        self._set_back(self._show_home)

        total = len(self.questions)
        correct = self.correct_count
        wrong = len(self.wrong_list)
        pct = correct / total * 100 if total > 0 else 0

        self._update_title("练习结果", f"正确率 {pct:.0f}%")

        # ── Layout: scrollable area + bottom buttons ──
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_rowconfigure(1, weight=0)
        self.container.grid_columnconfigure(0, weight=1)

        # Buttons at bottom (row 1)
        btn_frame = tk.Frame(self.container, bg=C_GRAY_BG)
        btn_frame.grid(row=1, column=0, sticky="ew", pady=10)

        # Scrollable content wrapper (row 0)
        outer = tk.Frame(self.container, bg=C_GRAY_BG)
        outer.grid(row=0, column=0, sticky="nsew")
        outer.grid_rowconfigure(0, weight=1)
        outer.grid_columnconfigure(0, weight=1)
        outer.grid_columnconfigure(1, weight=0)

        cv = tk.Canvas(outer, bg=C_GRAY_BG, highlightthickness=0)
        sb = ttk.Scrollbar(outer, orient="vertical", command=cv.yview)
        cv.grid(row=0, column=0, sticky="nsew")
        sb.grid(row=0, column=1, sticky="ns")

        sf = tk.Frame(cv, bg=C_GRAY_BG)
        win_id = cv.create_window((0, 0), window=sf, anchor="nw")

        def _on_cv_cfg(e):
            cv.itemconfig(win_id, width=e.width)
        cv.bind("<Configure>", _on_cv_cfg)

        sf.bind("<Configure>", lambda e: cv.configure(scrollregion=cv.bbox("all")))
        cv.configure(yscrollcommand=sb.set)

        # Mousewheel
        def _mw_pr(e): cv.yview_scroll(int(-1 * (e.delta / 120)), "units")
        cv.bind("<MouseWheel>", _mw_pr)
        sf.bind("<MouseWheel>", _mw_pr)

        # ── Content goes into sf ──
        tk.Label(
            sf, text="练习报告",
            font=("微软雅黑", 18, "bold"), fg=C_BLUE, bg=C_GRAY_BG
        ).pack(pady=(30, 15))

        stat_frame = tk.Frame(
            sf, bg=C_WHITE, highlightbackground=C_BORDER,
            highlightthickness=1
        )
        stat_frame.pack(fill="x", padx=40, pady=5, ipady=5)
        tk.Frame(stat_frame, bg=C_BLUE, height=3).pack(fill="x")

        stat_inner = tk.Frame(stat_frame, bg=C_WHITE)
        stat_inner.pack(expand=True, pady=15)

        for label, value, clr in [
            ("总题数", str(total), C_TEXT),
            ("答对", str(correct), C_GREEN),
            ("答错", str(wrong), C_RED),
            ("正确率", f"{pct:.1f}%", C_BLUE),
        ]:
            f = tk.Frame(stat_inner, bg=C_WHITE)
            f.pack(side="left", padx=25, expand=True)
            tk.Label(
                f, text=value, font=("微软雅黑", 24, "bold"),
                fg=clr, bg=C_WHITE
            ).pack()
            tk.Label(f, text=label, font=F_SMALL, fg="#888", bg=C_WHITE).pack()

        if pct >= 90:
            level, lc = "非常优秀 !", C_GREEN
        elif pct >= 80:
            level, lc = "良好，继续加油 !", C_BLUE
        elif pct >= 60:
            level, lc = "及格，需要加强薄弱章节", C_ORANGE
        else:
            level, lc = "不及格，建议重点复习", C_RED
        tk.Label(
            sf, text=level, font=("微软雅黑", 12, "bold"),
            fg=lc, bg=C_GRAY_BG
        ).pack(pady=10)

        if self.wrong_list:
            tk.Label(
                sf, text="错题回顾",
                font=("微软雅黑", 12, "bold"), fg=C_BLUE, bg=C_GRAY_BG
            ).pack(pady=(15, 5))

            for wq, wt, ua, ca in self.wrong_list:
                card = tk.Frame(
                    sf, bg=C_WHITE, highlightbackground=C_BORDER,
                    highlightthickness=1
                )
                card.pack(fill="x", padx=40, pady=3)
                tk.Frame(card, bg=C_RED, width=4).pack(side="left", fill="y")
                c_inner = tk.Frame(card, bg=C_WHITE)
                c_inner.pack(side="left", fill="both", expand=True, padx=10, pady=6)
                tk.Label(
                    c_inner,
                    text=f"[{TYPE_NAMES[wt]}] {wq['question'][:60]}{'...' if len(wq['question'])>60 else ''}",
                    font=F_SMALL, fg=C_TEXT, bg=C_WHITE,
                    wraplength=700, justify="left"
                ).pack(anchor="w")
                tk.Label(
                    c_inner,
                    text=f"你的答案: {ua}  |  正确答案: {ca}",
                    font=("微软雅黑", 9, "bold"), fg=C_RED, bg=C_WHITE
                ).pack(anchor="w")

            tk.Label(sf, text="", bg=C_GRAY_BG).pack(pady=5)

        # Populate buttons
        btn1 = tk.Button(
            btn_frame, text="继续练习", font=F_BTN,
            bg=C_BLUE, fg=C_WHITE, padx=20, pady=5, relief="flat", cursor="hand2",
            activebackground=C_ACCENT, activeforeground=C_WHITE,
            command=lambda: self._show_type_select(self.current_chapter)
        )
        btn1.pack(side="left", padx=10)
        btn1.bind("<Enter>", lambda e: btn1.config(bg=C_ACCENT))
        btn1.bind("<Leave>", lambda e: btn1.config(bg=C_BLUE))
        if self.wrong_list:
            btn2 = tk.Button(
                btn_frame, text="重练错题", font=F_BTN,
                bg=C_ORANGE, fg=C_WHITE, padx=20, pady=5, relief="flat", cursor="hand2",
                activebackground="#c06a10", activeforeground=C_WHITE,
                command=self._retry_wrong
            )
            btn2.pack(side="left", padx=10)
            btn2.bind("<Enter>", lambda e: btn2.config(bg="#c06a10"))
            btn2.bind("<Leave>", lambda e: btn2.config(bg=C_ORANGE))

    def _retry_wrong(self):
        if not self.wrong_list:
            messagebox.showinfo("提示", "没有错题")
            return
        self._clear()
        self._stop_timer()
        self.current_mode = "practice"
        self.correct_count = 0
        self.questions = [(q, t) for q, t, _, _ in self.wrong_list]
        self.wrong_list = []
        self.idx = 0
        self._update_title("错题重练", f"共 {len(self.questions)} 题")
        self._set_back(self._show_home)
        self._build_practice_ui()

    # ────────────────────────────────────────
    # EXAM SETUP
    # ────────────────────────────────────────
    def _show_exam_setup(self):
        self._clear()
        self._stop_timer()
        self._update_title("模拟考试", "设置考试参数")
        self._set_back(self._show_home)

        # Scrollable content
        _, _, sf = self._make_scrollable(self.container)

        tk.Label(
            sf, text="模拟考试设置",
            font=("微软雅黑", 18, "bold"), fg=C_BLUE, bg=C_GRAY_BG
        ).pack(pady=(30, 20))

        # Chapter range
        g1 = tk.LabelFrame(
            sf, text=" 章节范围 ", font=F_SUB,
            bg=C_WHITE, fg=C_BLUE, padx=20, pady=15
        )
        g1.pack(fill="x", padx=40, pady=8)
        self.exam_chapter = tk.StringVar(value="0")
        opts = [("0", "全部章节")] + [
            (str(c["id"]), f"第{c['id']}章  {c['name']}")
            for c in CHAPTERS
        ]
        for val, text in opts:
            tk.Radiobutton(
                g1, text=text, variable=self.exam_chapter,
                value=val, font=F_BTN, bg=C_WHITE
            ).pack(anchor="w", padx=20, pady=1)

        # Question count
        g2 = tk.LabelFrame(
            sf, text=" 题目数量 ", font=F_SUB,
            bg=C_WHITE, fg=C_BLUE, padx=20, pady=15
        )
        g2.pack(fill="x", padx=40, pady=8)
        self.exam_count = tk.StringVar(value="60")
        for val in ("15", "30", "50", "60", "80"):
            tk.Radiobutton(
                g2, text=f"{val} 题", variable=self.exam_count,
                value=val, font=F_BTN, bg=C_WHITE
            ).pack(side="left", padx=15, pady=5)

        # Duration
        g3 = tk.LabelFrame(
            sf, text=" 考试时长 ", font=F_SUB,
            bg=C_WHITE, fg=C_BLUE, padx=20, pady=15
        )
        g3.pack(fill="x", padx=40, pady=8)
        self.exam_duration_var = tk.StringVar(value="90")
        for val, text in [("15", "15 分钟"), ("30", "30 分钟"),
                          ("45", "45 分钟"), ("60", "60 分钟"),
                          ("90", "90 分钟"), ("120", "120 分钟")]:
            tk.Radiobutton(
                g3, text=text, variable=self.exam_duration_var,
                value=val, font=F_BTN, bg=C_WHITE
            ).pack(side="left", padx=15, pady=5)

        self.start_exam_btn = tk.Button(
            sf, text="开始考试", font=("微软雅黑", 14, "bold"),
            bg=C_BLUE, fg=C_WHITE, padx=50, pady=8, relief="flat", cursor="hand2",
            activebackground=C_ACCENT, activeforeground=C_WHITE,
            command=self._start_exam
        )
        self.start_exam_btn.pack(pady=30)
        self.start_exam_btn.bind("<Enter>", lambda e: self.start_exam_btn.config(bg=C_ACCENT))
        self.start_exam_btn.bind("<Leave>", lambda e: self.start_exam_btn.config(bg=C_BLUE))

    def _start_exam(self):
        ch = int(self.exam_chapter.get())
        count = int(self.exam_count.get())
        duration = int(self.exam_duration_var.get())
        self.exam_duration_minutes = duration

        judges = [
            q for q in ALL_QUESTIONS
            if q["type"] == "judge" and (ch == 0 or q["chapter"] == ch)
        ]
        singles = [
            q for q in ALL_QUESTIONS
            if q["type"] == "single" and (ch == 0 or q["chapter"] == ch)
        ]
        multis = [
            q for q in ALL_QUESTIONS
            if q["type"] == "multi" and (ch == 0 or q["chapter"] == ch)
        ]

        if not judges and not singles and not multis:
            messagebox.showinfo("提示", "该范围暂无题目")
            return

        total_avail = len(judges) + len(singles) + len(multis)
        n_judge = max(1, round(count * len(judges) / total_avail)) if judges else 0
        n_single = max(1, round(count * len(singles) / total_avail)) if singles else 0
        n_multi = max(1, round(count * len(multis) / total_avail)) if multis else 0

        selected = []
        if judges:
            selected.extend(
                [(q, "judge") for q in random.sample(judges, min(n_judge, len(judges)))]
            )
        if singles:
            selected.extend(
                [(q, "single") for q in random.sample(singles, min(n_single, len(singles)))]
            )
        if multis:
            selected.extend(
                [(q, "multi") for q in random.sample(multis, min(n_multi, len(multis)))]
            )
        random.shuffle(selected)
        selected = selected[:count]

        self.questions = selected
        self.exam_answers = {}
        self.exam_marked = set()
        self.idx = 0
        self.correct_count = 0
        self.wrong_list = []
        self.current_mode = "exam"
        self.current_chapter = ch

        self._show_exam_ui(duration)

    def _show_exam_ui(self, duration_minutes):
        self._clear()
        self._update_title("模拟考试", f"共 {len(self.questions)} 题")
        self._set_back(None)

        # Timer
        self.timer_lbl.pack(side="right", padx=15)
        self.timer_remaining = duration_minutes * 60
        self.timer_running = True
        self._update_timer()

        # Main 3-column
        main = tk.Frame(self.container, bg=C_GRAY_BG)
        main.pack(fill="both", expand=True)

        # Left: answer card (scrollable for 60+ questions)
        left = tk.Frame(
            main, bg=C_WHITE, width=210,
            highlightbackground=C_BORDER, highlightthickness=1
        )
        left.pack(side="left", fill="y", padx=(10, 5), pady=10)
        left.pack_propagate(False)
        left.grid_rowconfigure(1, weight=1)
        left.grid_columnconfigure(0, weight=1)

        tk.Label(
            left, text="答题卡", font=("微软雅黑", 11, "bold"),
            fg=C_BLUE, bg=C_WHITE
        ).grid(row=0, column=0, pady=(10, 5))

        # Scrollable card grid
        card_cv = tk.Canvas(left, bg=C_WHITE, highlightthickness=0, width=200)
        card_cv.grid(row=1, column=0, sticky="nsew", padx=4)
        card_sb = ttk.Scrollbar(left, orient="vertical", command=card_cv.yview)
        card_sb.grid(row=1, column=1, sticky="ns")
        card_cv.configure(yscrollcommand=card_sb.set)

        card_inner = tk.Frame(card_cv, bg=C_WHITE)
        card_win = card_cv.create_window((0, 0), window=card_inner, anchor="nw")

        def _on_card_cfg(e):
            card_cv.itemconfig(card_win, width=e.width - 4)
        card_cv.bind("<Configure>", _on_card_cfg)
        def _card_mw(e):
            card_cv.yview_scroll(int(-1 * (e.delta / 120)), "units")
        card_cv.bind("<MouseWheel>", _card_mw)
        card_inner.bind("<Configure>", lambda e: card_cv.configure(scrollregion=card_cv.bbox("all")))

        self.card_frame = card_inner
        self.card_cells = []
        n_per_row = 5
        for i in range(len(self.questions)):
            r, c = divmod(i, n_per_row)
            if c == 0:
                row_f = tk.Frame(card_inner, bg=C_WHITE)
                row_f.pack()
            cell = tk.Frame(
                row_f, width=30, height=30,
                bg=C_GRAY_LIGHT, highlightbackground=C_BORDER,
                highlightthickness=1, cursor="hand2"
            )
            cell.pack(side="left", padx=2, pady=2)
            cell.pack_propagate(False)
            lbl = tk.Label(cell, text=str(i + 1), font=("微软雅黑", 8),
                           bg=C_GRAY_LIGHT, fg=C_TEXT)
            lbl.pack(expand=True)
            cell.bind("<Button-1>", lambda e, idx=i: self._exam_goto(idx))
            lbl.bind("<Button-1>", lambda e, idx=i: self._exam_goto(idx))
            self.card_cells.append((cell, lbl))

        # Legend
        leg = tk.Frame(left, bg=C_WHITE)
        leg.grid(row=2, column=0, columnspan=2, pady=(8, 6))
        for text, color in [("未答", C_GRAY_LIGHT), ("已答", C_BLUE),
                            ("标记", C_YELLOW)]:
            f = tk.Frame(leg, bg=C_WHITE)
            f.pack(side="left", padx=4)
            tk.Label(f, bg=color, width=2).pack(side="left")
            tk.Label(f, text=text, font=F_SMALL, fg="#888",
                     bg=C_WHITE).pack(side="left", padx=2)

        # Center: question area
        center = tk.Frame(main, bg=C_GRAY_BG)
        center.pack(side="left", fill="both", expand=True, padx=5, pady=10)
        self.exam_q_area = tk.Frame(center, bg=C_GRAY_BG)
        self.exam_q_area.pack(fill="both", expand=True)
        self.answered_lbl = None

        # Bottom nav
        nav = tk.Frame(
            self.container, bg=C_WHITE, height=50,
            highlightbackground=C_BORDER, highlightthickness=1
        )
        nav.pack(fill="x")
        nav.pack_propagate(False)

        self.nav_prev = tk.Button(
            nav, text="< 上一题", font=F_BTN,
            bg=C_WHITE, fg=C_BLUE, bd=1, relief="flat", cursor="hand2",
            activebackground=C_PRIMARY_LIGHT,
            command=lambda: self._exam_navigate(-1)
        )
        self.nav_prev.pack(side="left", padx=10, pady=8)
        self.nav_prev.bind("<Enter>", lambda e: self.nav_prev.config(bg=C_PRIMARY_LIGHT))
        self.nav_prev.bind("<Leave>", lambda e: self.nav_prev.config(bg=C_WHITE))

        self.nav_mark = tk.Button(
            nav, text="标记本题", font=F_BTN,
            bg=C_YELLOW, fg=C_TEXT, bd=1, relief="flat", cursor="hand2",
            command=self._exam_toggle_mark
        )
        self.nav_mark.pack(side="left", padx=5, pady=8)

        self.nav_next = tk.Button(
            nav, text="下一题 >", font=F_BTN,
            bg=C_WHITE, fg=C_BLUE, bd=1, relief="flat", cursor="hand2",
            activebackground=C_PRIMARY_LIGHT,
            command=self._exam_next_or_submit
        )
        self.nav_next.pack(side="left", padx=5, pady=8)
        self.nav_next.bind("<Enter>", lambda e: self.nav_next.config(bg=C_PRIMARY_LIGHT))
        self.nav_next.bind("<Leave>", lambda e: self.nav_next.config(bg=C_WHITE))

        self.submit_exam_btn = tk.Button(
            nav, text="交卷", font=("微软雅黑", 11, "bold"),
            bg=C_RED, fg=C_WHITE, bd=0, padx=25, pady=5, cursor="hand2",
            activebackground="#b02a3f", activeforeground=C_WHITE,
            command=self._exam_confirm_submit
        )
        self.submit_exam_btn.pack(side="right", padx=15, pady=8)
        self.submit_exam_btn.bind("<Enter>", lambda e: self.submit_exam_btn.config(bg="#b02a3f"))
        self.submit_exam_btn.bind("<Leave>", lambda e: self.submit_exam_btn.config(bg=C_RED))

        self._render_exam_question()

    # ────────────────────────────────────────
    # EXAM TIMER
    # ────────────────────────────────────────
    def _update_timer(self):
        if not self.timer_running:
            return
        mins = self.timer_remaining // 60
        secs = self.timer_remaining % 60
        self.timer_lbl.config(text=f"{mins:02d}:{secs:02d}")
        if self.timer_remaining <= 0:
            self.timer_running = False
            self._exam_auto_submit()
            return
        if self.timer_remaining < 300:
            self.timer_lbl.config(fg=C_YELLOW)
        self.timer_remaining -= 1
        self.timer_job = self.win.after(1000, self._update_timer)

    # ────────────────────────────────────────
    # EXAM QUESTION RENDERING
    # ────────────────────────────────────────
    def _render_exam_question(self):
        for w in self.exam_q_area.winfo_children():
            w.destroy()

        if self.idx >= len(self.questions):
            return

        # Update nav button: "提交试卷" on last question
        is_last = (self.idx >= len(self.questions) - 1)
        if is_last:
            self.nav_next.config(text="提交试卷", fg=C_WHITE, bg=C_RED)
        else:
            self.nav_next.config(text="下一题 >", fg=C_BLUE, bg=C_WHITE)

        q, qtype = self.questions[self.idx]
        total = len(self.questions)

        header = tk.Frame(self.exam_q_area, bg=C_GRAY_BG)
        header.pack(fill="x", pady=(0, 10))
        tk.Label(
            header, text=f"第 {self.idx+1}/{total} 题",
            font=("微软雅黑", 12, "bold"), fg=C_BLUE, bg=C_GRAY_BG
        ).pack(side="left")

        tc = {"judge": C_BLUE, "single": C_GREEN, "multi": C_ORANGE}
        tk.Label(
            header, text=TYPE_NAMES[qtype], font=F_SMALL,
            fg=C_WHITE, bg=tc[qtype], padx=8, pady=2
        ).pack(side="left", padx=10)

        if self.idx in self.exam_marked:
            tk.Label(
                header, text=" [已标记]", font=F_SMALL,
                fg=C_ORANGE, bg=C_GRAY_BG
            ).pack(side="left")

        self.answered_lbl = tk.Label(
            header, text=f"已答 {len(self.exam_answers)}/{total}",
            font=F_SMALL, fg="#888", bg=C_GRAY_BG
        )
        self.answered_lbl.pack(side="right")

        # Question card
        q_card = tk.Frame(
            self.exam_q_area, bg=C_WHITE,
            highlightbackground=C_BORDER, highlightthickness=1
        )
        q_card.pack(fill="x", pady=5)
        tk.Frame(q_card, bg=C_ACCENT, height=3).pack(fill="x")

        # Topic badge
        topics = get_question_topics(q)
        if topics:
            t_frame = tk.Frame(q_card, bg=C_WHITE)
            t_frame.pack(fill="x", padx=15, pady=(10, 0))
            tk.Label(
                t_frame, text="考点", font=("微软雅黑", 8),
                fg=C_WHITE, bg=C_BLUE, padx=4, pady=1
            ).pack(side="left")
            tk.Label(
                t_frame, text=topics[0], font=("微软雅黑", 8),
                fg=C_BLUE, bg=C_BLUE_LIGHT, padx=6, pady=1
            ).pack(side="left", padx=4)

        tk.Label(
            q_card, text=q["question"], font=F_BODY,
            wraplength=self._get_ww_sm(), justify="left", bg=C_WHITE,
            padx=20, pady=20
        ).pack(anchor="w")

        # Options
        opt_frame = tk.Frame(self.exam_q_area, bg=C_GRAY_BG)
        opt_frame.pack(fill="x", pady=10)

        self.exam_ans_var = tk.StringVar(value="")
        self.exam_multi_vars = {}
        saved_ans = self.exam_answers.get(self.idx, "")

        if qtype == "judge":
            for val, txt in [("√", "正确"), ("×", "错误")]:
                f = tk.Frame(
                    opt_frame, bg=C_WHITE, highlightbackground=C_BORDER,
                    highlightthickness=1, cursor="hand2"
                )
                f.pack(fill="x", pady=4, padx=10)
                rb = tk.Radiobutton(
                    f, text=f"  {txt}", variable=self.exam_ans_var,
                    value=val, font=F_BODY, bg=C_WHITE,
                    selectcolor=C_CYAN, activebackground=C_BLUE_LIGHT
                )
                rb.pack(side="left", padx=10, pady=8)
                if val == saved_ans:
                    self.exam_ans_var.set(val)
                f.bind("<Button-1>", lambda e, v=val: self._exam_select(v))
        elif qtype == "single":
            exam_sing_frames = []
            for opt in q.get("options", []):
                letter, text = parse_option_text(opt)
                f = tk.Frame(
                    opt_frame, bg=C_WHITE, highlightbackground=C_BORDER,
                    highlightthickness=2, cursor="hand2"
                )
                f.pack(fill="x", pady=5)
                badge = tk.Label(
                    f, text=letter, font=("Consolas", 12, "bold"),
                    fg=C_WHITE, bg=C_BLUE, width=3, height=1
                )
                badge.pack(side="left", padx=10, pady=10)
                rb = tk.Radiobutton(
                    f, text=text, variable=self.exam_ans_var,
                    value=letter, font=F_BODY, bg=C_WHITE,
                    activebackground=C_BLUE_LIGHT
                )
                rb.pack(side="left", padx=5, fill="x", expand=True)
                if letter == saved_ans:
                    self.exam_ans_var.set(letter)
                f.bind("<Button-1>", lambda e, v=letter: self._exam_select(v))
                badge.bind("<Button-1>", lambda e, v=letter: self._exam_select(v))
                exam_sing_frames.append((letter, f))
            # Update border when selection changes
            def _upd_exam_sing(*_):
                sel = self.exam_ans_var.get()
                for l, fr in exam_sing_frames:
                    fr.config(highlightbackground=C_ACCENT if l == sel else C_BORDER,
                              highlightthickness=2)
            self.exam_ans_var.trace_add("write", _upd_exam_sing)
        else:  # multi
            for opt in q.get("options", []):
                letter, text = parse_option_text(opt)
                var = tk.BooleanVar()
                self.exam_multi_vars[letter] = var
                f = tk.Frame(
                    opt_frame, bg=C_WHITE, highlightbackground=C_BORDER,
                    highlightthickness=2, cursor="hand2"
                )
                f.pack(fill="x", pady=4)
                badge = tk.Label(
                    f, text=letter, font=("Consolas", 12, "bold"),
                    fg=C_WHITE, bg=C_PRIMARY, width=3, height=1
                )
                badge.pack(side="left", padx=10, pady=10)
                txt_lbl = tk.Label(
                    f, text=text, font=F_BODY, bg=C_WHITE, anchor="w"
                )
                txt_lbl.pack(side="left", padx=5, fill="x", expand=True)

                # Auto-update badge+frame color when var changes
                def _emupd(*_a, vv=var, bb=badge, ff=f):
                    new = vv.get()
                    bb.config(bg=C_PRIMARY_DARK if new else C_PRIMARY)
                    ff.config(highlightbackground=C_ACCENT if new else C_BORDER)
                var.trace_add("write", _emupd)

                if letter in saved_ans:
                    var.set(True)

                toggle_lambda = lambda e, v=letter: self._exam_toggle_multi(v)
                for wgt in (f, badge, txt_lbl):
                    wgt.bind("<Button-1>", toggle_lambda, add="+")

        # Save answer automatically (for single/judge via trace)
        if qtype != "multi":
            self.exam_ans_var.trace_add(
                "write", lambda *args: self._exam_save_answer()
            )

    def _exam_select(self, value):
        self.exam_ans_var.set(value)

    def _exam_toggle_multi(self, letter):
        if letter in self.exam_multi_vars:
            self.exam_multi_vars[letter].set(
                not self.exam_multi_vars[letter].get()
            )
        self._exam_save_answer()

    def _exam_save_answer(self):
        q, qtype = self.questions[self.idx]
        if qtype == "multi":
            ans = "".join(sorted(
                k for k, v in self.exam_multi_vars.items() if v.get()
            ))
        else:
            ans = self.exam_ans_var.get()

        if ans:
            self.exam_answers[self.idx] = ans
        elif self.idx in self.exam_answers:
            del self.exam_answers[self.idx]

        self._update_card_colors()
        if self.answered_lbl:
            self.answered_lbl.config(
                text=f"已答 {len(self.exam_answers)}/{len(self.questions)}"
            )

    def _update_card_colors(self):
        for i in range(len(self.questions)):
            cell, lbl = self.card_cells[i]
            if i in self.exam_marked:
                bg, fg = C_YELLOW, C_TEXT
            elif i in self.exam_answers:
                bg, fg = C_BLUE, C_WHITE
            else:
                bg, fg = C_GRAY_LIGHT, C_TEXT
            cell.config(bg=bg)
            lbl.config(bg=bg, fg=fg)

    def _exam_next_or_submit(self):
        """Navigate next or submit if last question."""
        if self.idx >= len(self.questions) - 1:
            self._exam_confirm_submit()
        else:
            self._exam_navigate(1)

    def _exam_navigate(self, delta):
        ni = self.idx + delta
        if 0 <= ni < len(self.questions):
            self.idx = ni
            self._render_exam_question()

    def _exam_goto(self, idx):
        if 0 <= idx < len(self.questions):
            self.idx = idx
            self._render_exam_question()

    def _exam_toggle_mark(self):
        if self.idx in self.exam_marked:
            self.exam_marked.remove(self.idx)
        else:
            self.exam_marked.add(self.idx)
        self._update_card_colors()
        self._render_exam_question()

    def _exam_confirm_submit(self):
        answered = len(self.exam_answers)
        total = len(self.questions)
        missing = total - answered
        msg = f"你已答 {answered}/{total} 题"
        if missing > 0:
            msg += f"\n还有 {missing} 题未作答"
        msg += "\n\n确定要交卷吗？"
        if messagebox.askyesno("确认交卷", msg):
            self._exam_grade()

    def _exam_auto_submit(self):
        self.timer_running = False
        messagebox.showinfo("时间到", "考试时间已到，系统将自动交卷")
        self._exam_grade()

    def _exam_grade(self):
        self._stop_timer()

        correct = 0
        wrong_list = []

        for i, (q, qtype) in enumerate(self.questions):
            user_ans = self.exam_answers.get(i, "")
            correct_ans = q["answer"]
            if user_ans == correct_ans:
                correct += 1
                self.perf_data.append((q, qtype, True))
            else:
                wrong_list.append((q, qtype, user_ans, correct_ans))
                qid = q.get("id", "")
                if not any(w[0].get("id", "") == qid for w in self.wrong_book):
                    self.wrong_book.append((q, qtype, user_ans, correct_ans))
                self.perf_data.append((q, qtype, False))
        self._auto_save()

        self.correct_count = correct
        self.wrong_list = wrong_list
        self._show_exam_result()

    # ────────────────────────────────────────
    # EXAM RESULT
    # ────────────────────────────────────────
    def _show_exam_result(self):
        self._clear()
        self._set_back(self._show_home)

        total = len(self.questions)
        correct = self.correct_count
        wrong = len(self.wrong_list)
        pct = correct / total * 100 if total > 0 else 0

        self._update_title("考试成绩", f"正确率 {pct:.0f}%")

        # ── Layout: scrollable area + bottom buttons ──
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_rowconfigure(1, weight=0)
        self.container.grid_columnconfigure(0, weight=1)

        # Buttons at bottom (row 1)
        bf = tk.Frame(self.container, bg=C_GRAY_BG)
        bf.grid(row=1, column=0, sticky="ew", pady=10)

        # Scrollable content wrapper (row 0)
        outer = tk.Frame(self.container, bg=C_GRAY_BG)
        outer.grid(row=0, column=0, sticky="nsew")
        outer.grid_rowconfigure(0, weight=1)
        outer.grid_columnconfigure(0, weight=1)
        outer.grid_columnconfigure(1, weight=0)

        cv = tk.Canvas(outer, bg=C_GRAY_BG, highlightthickness=0)
        sb = ttk.Scrollbar(outer, orient="vertical", command=cv.yview)
        cv.grid(row=0, column=0, sticky="nsew")
        sb.grid(row=0, column=1, sticky="ns")

        sf = tk.Frame(cv, bg=C_GRAY_BG)
        win_id = cv.create_window((0, 0), window=sf, anchor="nw")

        def _on_cv_cfg(e):
            cv.itemconfig(win_id, width=e.width)
        cv.bind("<Configure>", _on_cv_cfg)

        sf.bind("<Configure>", lambda e: cv.configure(scrollregion=cv.bbox("all")))
        cv.configure(yscrollcommand=sb.set)

        # Mousewheel
        def _mw_er(e): cv.yview_scroll(int(-1 * (e.delta / 120)), "units")
        cv.bind("<MouseWheel>", _mw_er)
        sf.bind("<MouseWheel>", _mw_er)

        # ── Content goes into sf ──
        tk.Label(
            sf, text="考试成绩单",
            font=("微软雅黑", 20, "bold"), fg=C_BLUE, bg=C_GRAY_BG
        ).pack(pady=(25, 15))

        # Stats
        sf_stat = tk.Frame(
            sf, bg=C_WHITE, highlightbackground=C_BORDER,
            highlightthickness=1
        )
        sf_stat.pack(fill="x", padx=40, pady=5, ipady=5)
        tk.Frame(sf_stat, bg=C_GREEN, height=3).pack(fill="x")

        stat_inner = tk.Frame(sf_stat, bg=C_WHITE)
        stat_inner.pack(expand=True, pady=15)

        for label, value, clr in [
            ("总题数", str(total), C_TEXT),
            ("答对", str(correct), C_GREEN),
            ("答错", str(wrong), C_RED),
            ("正确率", f"{pct:.1f}%", C_BLUE),
        ]:
            f = tk.Frame(stat_inner, bg=C_WHITE)
            f.pack(side="left", padx=25, expand=True)
            tk.Label(
                f, text=value, font=("微软雅黑", 28, "bold"),
                fg=clr, bg=C_WHITE
            ).pack()
            tk.Label(f, text=label, font=F_BODY, fg="#888", bg=C_WHITE).pack()

        # Duration
        elapsed = self.exam_duration_minutes - self.timer_remaining // 60
        tk.Label(
            sf,
            text=f"考试时长: {self.exam_duration_minutes}分钟  |  用时: {elapsed}分钟",
            font=F_SMALL, fg="#888", bg=C_GRAY_BG
        ).pack()

        # Rating
        if pct >= 90:
            level, lc = "优秀 !", C_GREEN
        elif pct >= 80:
            level, lc = "良好，保持状态 !", C_BLUE
        elif pct >= 60:
            level, lc = "及格，需加强薄弱章节", C_ORANGE
        else:
            level, lc = "不及格，建议系统复习", C_RED
        tk.Label(
            sf, text=level, font=("微软雅黑", 14, "bold"),
            fg=lc, bg=C_GRAY_BG
        ).pack(pady=(10, 15))

        # Chapter analysis bar chart
        self._render_chart(parent=sf)

        # Wrong list (no separate scroll, uses page scroll)
        if self.wrong_list:
            tk.Label(
                sf, text="错题详情",
                font=("微软雅黑", 12, "bold"), fg=C_BLUE, bg=C_GRAY_BG
            ).pack(pady=(15, 5))

            for wq, wt, ua, ca in self.wrong_list:
                card = tk.Frame(
                    sf, bg=C_WHITE, highlightbackground=C_BORDER,
                    highlightthickness=1
                )
                card.pack(fill="x", padx=40, pady=3)
                tk.Frame(card, bg=C_RED, width=4).pack(side="left", fill="y")
                c_inner = tk.Frame(card, bg=C_WHITE)
                c_inner.pack(side="left", fill="both", expand=True, padx=10, pady=6)
                txt = wq["question"]
                tk.Label(
                    c_inner, text=f"[{TYPE_NAMES[wt]}] {txt[:65]}{'...' if len(txt)>65 else ''}",
                    font=F_SMALL, fg=C_TEXT, bg=C_WHITE,
                    wraplength=700, justify="left"
                ).pack(anchor="w")
                tk.Label(
                    c_inner,
                    text=f"你的答案: {ua}  |  正确答案: {ca}",
                    font=("微软雅黑", 9, "bold"), fg=C_RED, bg=C_WHITE
                ).pack(anchor="w")

            # Bottom spacer for scroll
            tk.Label(sf, text="", bg=C_GRAY_BG).pack(pady=5)

        # Populate buttons (bf already packed at bottom above)
        btn1 = tk.Button(
            bf, text="返回首页", font=F_BTN, bg=C_BLUE, fg=C_WHITE,
            padx=20, pady=5, relief="flat", cursor="hand2",
            activebackground=C_ACCENT, activeforeground=C_WHITE,
            command=self._show_home
        )
        btn1.pack(side="left", padx=10)
        btn1.bind("<Enter>", lambda e: btn1.config(bg=C_ACCENT))
        btn1.bind("<Leave>", lambda e: btn1.config(bg=C_BLUE))
        if self.wrong_list:
            btn2 = tk.Button(
                bf, text="重练错题", font=F_BTN, bg=C_ORANGE, fg=C_WHITE,
                padx=20, pady=5, relief="flat", cursor="hand2",
                activebackground="#c06a10", activeforeground=C_WHITE,
                command=self._retry_wrong
            )
            btn2.pack(side="left", padx=10)
            btn2.bind("<Enter>", lambda e: btn2.config(bg="#c06a10"))
            btn2.bind("<Leave>", lambda e: btn2.config(bg=C_ORANGE))
        btn3 = tk.Button(
            bf, text="AI智能分析", font=F_BTN, bg=C_BLUE_DARK, fg=C_WHITE,
            padx=20, pady=5, relief="flat", cursor="hand2",
            activebackground=C_ACCENT, activeforeground=C_WHITE,
            command=self._show_ai_analysis
        )
        btn3.pack(side="left", padx=10)
        btn3.bind("<Enter>", lambda e: btn3.config(bg=C_ACCENT))
        btn3.bind("<Leave>", lambda e: btn3.config(bg=C_BLUE_DARK))

    def _render_chart(self, parent=None):
        """Horizontal bar chart of per-chapter accuracy"""
        if parent is None:
            parent = self.container
        ch_data = {}
        for i, (q, _) in enumerate(self.questions):
            ch = q.get("chapter", 0)
            if ch not in ch_data:
                ch_data[ch] = {"total": 0, "correct": 0}
            ch_data[ch]["total"] += 1
            if self.exam_answers.get(i, "") == q["answer"]:
                ch_data[ch]["correct"] += 1

        if not ch_data:
            return

        cf = tk.Frame(
            parent, bg=C_WHITE, highlightbackground=C_BORDER,
            highlightthickness=1
        )
        cf.pack(fill="x", padx=40, pady=5, ipady=10)

        tk.Label(
            cf, text="章节正确率分析", font=("微软雅黑", 11, "bold"),
            fg=C_BLUE, bg=C_WHITE
        ).pack(pady=(10, 10))

        cv = tk.Canvas(
            cf, bg=C_WHITE, highlightthickness=0,
            height=25 * len(ch_data) + 15
        )
        cv.pack(fill="x", padx=20)

        ch_names = {c["id"]: c["name"][:10] for c in CHAPTERS}
        y = 10
        bw = 420
        for ch_id in sorted(ch_data.keys()):
            d = ch_data[ch_id]
            pct = d["correct"] / d["total"] * 100 if d["total"] > 0 else 0
            name = ch_names.get(ch_id, f"第{ch_id}章")

            cv.create_text(10, y + 8, text=name, anchor="w",
                           font=("微软雅黑", 9), fill=C_TEXT)
            cv.create_rectangle(110, y, 110 + bw, y + 18,
                                outline="", fill=C_GRAY_LIGHT)
            fw = int(bw * pct / 100)
            bar_color = C_GREEN if pct >= 80 else (
                C_YELLOW if pct >= 60 else C_RED
            )
            cv.create_rectangle(110, y, 110 + fw, y + 18,
                                outline="", fill=bar_color)
            cv.create_text(
                110 + bw + 8, y + 8,
                text=f"{d['correct']}/{d['total']} ({pct:.0f}%)",
                anchor="w", font=("微软雅黑", 9), fill=C_TEXT
            )
            y += 23

    # ────────────────────────────────────────
    # WRONG REVIEW
    # ────────────────────────────────────────
    def _show_wrong_review(self):
        self._clear()
        self._stop_timer()
        self._update_title("错题重练", f"共 {len(self.wrong_book)} 题")
        self._set_back(self._show_home)

        if not self.wrong_book:
            tk.Label(
                self.container, text="暂无错题记录",
                font=("微软雅黑", 14, "bold"), fg="#888", bg=C_GRAY_BG
            ).pack(pady=50)
            tk.Label(
                self.container,
                text="完成练习后，答错的题目会自动收录到这里",
                font=F_BODY, fg="#aaa", bg=C_GRAY_BG
            ).pack()
            return

        tk.Label(
            self.container, text=f"错题本 ({len(self.wrong_book)} 题)",
            font=("微软雅黑", 16, "bold"), fg=C_BLUE, bg=C_GRAY_BG
        ).pack(pady=(20, 5))

        _, _, sf = self._make_scrollable(self.container)

        for wq, wt, ua, ca in self.wrong_book:
            card = tk.Frame(
                sf, bg=C_WHITE, highlightbackground=C_BORDER,
                highlightthickness=1
            )
            card.pack(fill="x", pady=4)
            ch_name = ""
            for c in CHAPTERS:
                if c["id"] == wq.get("chapter", 0):
                    ch_name = f"第{c['id']}章 "
                    break
            txt = wq["question"]
            tk.Label(
                card,
                text=f"{ch_name}[{TYPE_NAMES[wt]}] "
                     f"{txt[:70]}{'...' if len(txt)>70 else ''}",
                font=F_SMALL, fg=C_TEXT, bg=C_WHITE,
                wraplength=750, justify="left"
            ).pack(padx=12, pady=(8, 2), anchor="w")
            tk.Label(
                card, text=f"你的答案: {ua}  |  正确答案: {ca}",
                font=("微软雅黑", 9, "bold"), fg=C_RED, bg=C_WHITE
            ).pack(padx=12, anchor="w")
            tk.Label(
                card, text=f"[解析] {wq['analysis'][:80]}{'...' if len(wq['analysis'])>80 else ''}",
                font=F_SMALL, fg="#888", bg=C_WHITE, wraplength=750, justify="left"
            ).pack(padx=12, pady=(2, 8), anchor="w")

        bf = tk.Frame(self.container, bg=C_GRAY_BG)
        bf.pack(side="bottom", pady=15, fill="x")
        tk.Button(
            bf, text="重练所有错题", font=("微软雅黑", 12, "bold"),
            bg=C_ORANGE, fg=C_WHITE, padx=30, pady=6,
            command=self._start_wrong_quiz
        ).pack(side="left", padx=10)
        tk.Button(
            bf, text="清空错题本", font=F_BTN,
            bg=C_WHITE, fg=C_RED, padx=15, pady=4,
            command=self._clear_wrong_book
        ).pack(side="left", padx=10)

    def _start_wrong_quiz(self):
        if not self.wrong_book:
            messagebox.showinfo("提示", "错题本为空")
            return
        self._clear()
        self._stop_timer()
        self.current_mode = "practice"
        self.correct_count = 0
        self.questions = [(q, t) for q, t, _, _ in self.wrong_book]
        self.wrong_list = []
        self.idx = 0
        self._update_title("错题重练", f"共 {len(self.questions)} 题")
        self._set_back(self._show_home)
        self._build_practice_ui()

    def _clear_wrong_book(self):
        if messagebox.askyesno("确认", "确定要清空错题本吗？"):
            self.wrong_book = []
            self._auto_save()
            self._show_wrong_review()

    # ────────────────────────────────────────
    # SYLLABUS
    # ────────────────────────────────────────
    def _show_syllabus(self):
        self._clear()
        self._stop_timer()
        self._update_title("考试大纲", "考点权重 | 容灾等级 | 必背数字")
        self._set_back(self._show_home)

        _, _, sf = self._make_scrollable(self.container)

        def sec(title):
            tk.Label(
                sf, text=title, font=("微软雅黑", 14, "bold"),
                fg=C_BLUE, bg=C_GRAY_BG
            ).pack(pady=(15, 8), anchor="w", padx=30)

        def line(text, color=C_TEXT):
            tk.Label(
                sf, text=text, font=F_BODY, fg=color, bg=C_GRAY_BG,
                wraplength=800, justify="left"
            ).pack(anchor="w", padx=40, pady=1)

        # 1. Chapter weights
        sec("1. 考纲章节权重")
        hdr = f"{'章节':<25} {'权重':<8} {'判断':<6} {'单选':<6} {'多选':<6} {'合计':<6}"
        sep = "  " + "-" * 55
        line(hdr, C_BLUE)
        line(sep, "#ccc")
        tj = ts = tm = 0
        for ch in CHAPTERS:
            cid = ch["id"]
            cnt = CHAPTER_COUNTS[cid]
            tj += cnt["judge"]; ts += cnt["single"]; tm += cnt["multi"]
            line(
                f"  第{cid}章 {ch['name']:<18} {ch['weight']:<8} "
                f"{cnt['judge']:<6} {cnt['single']:<6} {cnt['multi']:<6} {cnt['total']:<6}"
            )
        line(sep, "#ccc")
        line(
            f"  {'合计':<30} {tj:<6} {ts:<6} {tm:<6} {tj+ts+tm:<6}"
        )

        # 2. DR levels
        sec("2. 容灾等级标准")
        dr = [
            ("6级", "RPO=0", "RTO=数分钟"),
            ("5级", "RPO=0~30分钟", "RTO=数分钟~2天"),
            ("4级", "RPO<15分钟", "RTO<=6小时"),
            ("3级", "RPO=数小时~1天", "RTO<=12小时"),
            ("2级", "RPO=数小时~1天", "RTO<=24小时"),
            ("1级", "RPO=1~7天", "RTO<=2天"),
        ]
        line(f"{'等级':<8} {'RPO':<22} {'RTO':<20}", C_BLUE)
        line(sep, "#ccc")
        for lv, rpo, rto in dr:
            line(f"  {lv:<8} {rpo:<22} {rto:<20}")

        # 3. Key numbers
        sec("3. 必背数字")
        for kn in [
            "单节点tpmC: 150万",
            "32节点tpmC: 1500万",
            "轻量化管理节点: 3台",
            "HCS标准管理节点: 17台",
            "AZ内时延: <0.25ms",
            "跨AZ时延: <2ms",
            "两地三中心: 同城AZ间距>50km, 异地AZ间距>200km",
        ]:
            line(f"  * {kn}")

        # 4. Deployment
        sec("4. 部署方案选择")
        for dg in [
            "集中式: SQL复杂、存量存储过程多、数据量<2TB",
            "分布式: 大容量(>=2TB)、高并发、扩展性要求高",
            "主备模式: 要求高可用、读写分离",
            "一主多备: 读负载大、需要多副本",
            "两地三中心: 金融级容灾要求",
        ]:
            line(f"  * {dg}")

        # 5. Formulas
        sec("5. 常用公式")
        for fm in [
            "TPS = 高峰期事务量 / (高峰期时长 * 60)",
            "索引空间 = 表大小 * 索引个数 * 0.5",
            "备份容量 = 数据量 * 压缩比 * 副本数 * 保留天数",
        ]:
            line(f"  * {fm}")

        line("")

    # ────────────────────────────────────────
    # AI INTELLIGENT ANALYSIS
    # ────────────────────────────────────────
    def _show_ai_analysis(self):
        self._clear()
        self._stop_timer()
        self._update_title("AI 智能分析", "基于答题数据的智能诊断报告")
        self._set_back(self._show_home)

        if not self.perf_data:
            tk.Label(
                self.container, text="暂无答题数据",
                font=("微软雅黑", 14, "bold"), fg="#888", bg=C_GRAY_BG
            ).pack(pady=50)
            tk.Label(
                self.container,
                text="完成练习或模拟考试后，这里将生成智能分析报告",
                font=F_BODY, fg="#aaa", bg=C_GRAY_BG
            ).pack()
            tk.Label(
                self.container,
                text="包括：掌握程度评估、薄弱环节识别、复习建议等",
                font=F_SMALL, fg="#bbb", bg=C_GRAY_BG
            ).pack()
            return

        # Calculate per-chapter stats
        ch_data = {c["id"]: {"total": 0, "correct": 0, "name": c["name"],
                             "weight": c["weight"]} for c in CHAPTERS}
        type_data = {"judge": {"total": 0, "correct": 0},
                     "single": {"total": 0, "correct": 0},
                     "multi": {"total": 0, "correct": 0}}
        topic_data = {}

        for q, qtype, is_correct in self.perf_data:
            ch = q.get("chapter", 0)
            if ch in ch_data:
                ch_data[ch]["total"] += 1
                if is_correct:
                    ch_data[ch]["correct"] += 1
            if qtype in type_data:
                type_data[qtype]["total"] += 1
                if is_correct:
                    type_data[qtype]["correct"] += 1
            # Topic tracking
            topics = get_question_topics(q)
            for t in topics:
                if t not in topic_data:
                    topic_data[t] = {"total": 0, "correct": 0, "chapter": ch}
                topic_data[t]["total"] += 1
                if is_correct:
                    topic_data[t]["correct"] += 1

        total_q = sum(d["total"] for d in ch_data.values())
        total_correct = sum(d["correct"] for d in ch_data.values())
        overall_pct = total_correct / total_q * 100 if total_q > 0 else 0

        # Scrollable content
        _, _, sf = self._make_scrollable(self.container)

        def sec(title):
            tk.Label(sf, text=title, font=("微软雅黑", 14, "bold"),
                    fg=C_BLUE, bg=C_GRAY_BG).pack(pady=(12, 5), anchor="w", padx=30)

        def info(text, color=C_TEXT, sz=F_BODY):
            tk.Label(sf, text=text, font=sz, fg=color, bg=C_GRAY_BG,
                    wraplength=800, justify="left").pack(anchor="w", padx=40, pady=1)

        # ── 1. Overall Score ──
        sec("1. 综合评估")
        score_color = C_GREEN if overall_pct >= 80 else (C_YELLOW if overall_pct >= 60 else C_RED)
        score_text = "优秀" if overall_pct >= 80 else ("良好" if overall_pct >= 60 else "待加强")
        info(f"综合掌握度: {overall_pct:.1f}%  ({score_text})", score_color, ("微软雅黑", 18, "bold"))
        info(f"已答题: {total_q}   |   正确: {total_correct}   |   正确率: {overall_pct:.1f}%")
        info("")

        # ── 2. Chapter Analysis ──
        sec("2. 章节掌握度分析")
        for ch in CHAPTERS:
            cid = ch["id"]
            d = ch_data[cid]
            if d["total"] == 0:
                continue
            pct = d["correct"] / d["total"] * 100
            bar_color = C_GREEN if pct >= 80 else (C_YELLOW if pct >= 60 else C_RED)
            status = "稳定" if pct >= 80 else ("需加强" if pct >= 60 else "薄弱")

            row = tk.Frame(sf, bg=C_GRAY_BG)
            row.pack(fill="x", padx=40, pady=3)

            tk.Label(row, text=f"第{cid}章", font=F_SMALL, fg=C_TEXT,
                    bg=C_GRAY_BG, width=6, anchor="w").pack(side="left")
            tk.Label(row, text=f"{pct:.0f}%", font=("微软雅黑", 9, "bold"),
                    fg=bar_color, bg=C_GRAY_BG, width=5, anchor="e").pack(side="left")

            # Bar
            bar_bg = tk.Frame(row, bg=C_GRAY_LIGHT, height=14, width=300)
            bar_bg.pack(side="left", padx=5)
            bar_bg.pack_propagate(False)
            bw = max(int(300 * pct / 100), 1)
            tk.Frame(bar_bg, bg=bar_color, height=14, width=bw).pack(side="left")

            tk.Label(row, text=f"{d['correct']}/{d['total']}  {status}",
                    font=F_SMALL, fg="#888", bg=C_GRAY_BG).pack(side="left", padx=5)

        # ── 3. Topic Weakness ──
        sec("")
        sec("3. 薄弱考点识别 (AI诊断)")
        weak_topics = [(t, d) for t, d in topic_data.items()
                       if d["total"] >= 2 and d["correct"] / d["total"] < 0.6]
        weak_topics.sort(key=lambda x: x[1]["correct"] / x[1]["total"])

        if weak_topics:
            info("以下考点掌握不足，建议重点复习:", C_RED, F_BODY)
            for t, d in weak_topics:
                pct = d["correct"] / d["total"] * 100
                ch_name = CHAPTER_TOPICS.get(d["chapter"], {}).get("name", "")
                info(f"  * [{ch_name}] {t}: 正确率 {pct:.0f}% ({d['correct']}/{d['total']}题)", C_RED)
        else:
            strong = sum(1 for d in ch_data.values() if d["total"] > 0 and d["correct"]/d["total"] >= 0.8)
            if strong >= 3:
                info("所有考点掌握良好，继续保持!", C_GREEN)
            else:
                info("暂无足够数据识别薄弱环节，继续练习更多题目", "#888")

        # ── 4. Type Performance ──
        sec("")
        sec("4. 题型掌握分析")
        for qt_key, qt_name in [("judge", "判断题"), ("single", "单选题"), ("multi", "多选题")]:
            d = type_data[qt_key]
            if d["total"] == 0:
                info(f"  {qt_name}: 暂无数据", "#bbb")
                continue
            pct = d["correct"] / d["total"] * 100
            tc = C_GREEN if pct >= 80 else (C_YELLOW if pct >= 60 else C_RED)
            info(f"  {qt_name}: {pct:.0f}% ({d['correct']}/{d['total']}题)", tc)

        # ── 5. Recommendations ──
        sec("")
        sec("5. 智能复习建议")
        weak_chs = [(ch, ch_data[ch["id"]]) for ch in CHAPTERS
                    if ch_data[ch["id"]]["total"] > 0
                    and ch_data[ch["id"]]["correct"] / ch_data[ch["id"]]["total"] < 0.6]
        weak_chs.sort(key=lambda x: x[1]["correct"] / x[1]["total"])

        if weak_topics:
            info("重点复习薄弱考点，优先从以下章节入手：")
            for ch, d in weak_chs[:3]:
                pct = d["correct"] / d["total"] * 100
                info(f"  * 第{ch['id']}章 {ch['name']} (正确率 {pct:.0f}%)")
            info("建议针对薄弱考点中的关键词，回顾教材相关章节")
        elif total_q >= 10:
            info("各章节掌握较为均衡，建议:")
            info("  * 保持日常练习节奏")
            info("  * 尝试模拟考试检验综合能力")
            info("  * 挑战更多多选题提升得分率")
        else:
            info("继续练习积累数据，系统将为你生成个性化复习建议")

        # ── 6. Score Prediction ──
        sec("")
        sec("6. 考试预测")
        if total_q >= 15:
            # Weighted by exam syllabus weights
            weighted = 0
            total_weight = 0
            for ch in CHAPTERS:
                cid = ch["id"]
                d = ch_data[cid]
                w = int(ch["weight"].replace("%", ""))
                if d["total"] > 0:
                    weighted += d["correct"] / d["total"] * w
                total_weight += w
            predicted = weighted / total_weight * 100 if total_weight > 0 else 0
            pred_color = C_GREEN if predicted >= 80 else (C_YELLOW if predicted >= 60 else C_RED)
            pred_text = "通过" if predicted >= 60 else "待加强"
            info(f"预测考试成绩: {predicted:.1f}%  ({pred_text})", pred_color, ("微软雅黑", 14, "bold"))
            if predicted < 60:
                info("建议重点复习薄弱章节后再参加考试")

            # Weakest chapter highlight
            if weak_chs:
                worst = weak_chs[0]
                info(f"最大提分空间: 第{worst[0]['id']}章 {worst[0]['name']}")
        else:
            info("完成更多题目后可获得考试预测 (建议至少15题)", "#888")

        info("")

        # ── Reset data button ──
        bf = tk.Frame(sf, bg=C_GRAY_BG)
        bf.pack(pady=10)
        tk.Button(
            bf, text="重置分析数据", font=F_SMALL,
            bg=C_WHITE, fg=C_RED, padx=15, pady=3,
            command=self._reset_perf_data
        ).pack()

    def _reset_perf_data(self):
        if messagebox.askyesno("确认", "确定要清空所有答题分析数据吗？"):
            self.perf_data = []
            self._auto_save()
            self._show_ai_analysis()

    # ────────────────────────────────────────
    # RUN
    # ────────────────────────────────────────
    def run(self):
        self.win.mainloop()


def _tk_error_handler(exc_type, exc_val, exc_tb):
    import traceback
    err_msg = ''.join(traceback.format_exception(exc_type, exc_val, exc_tb))
    with open(os.path.expanduser("~/hccde_error.log"), "w", encoding="utf-8") as f:
        f.write(err_msg)

if __name__ == "__main__":
    import tkinter as tk
    app = ExamApp()
    app.win.report_callback_exception = lambda exc, val, tb: _tk_error_handler(exc, val, tb)
    app.run()
