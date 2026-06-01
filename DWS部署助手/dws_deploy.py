#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DWS 部署交互助手 v0.1 — 配置中心 + 模板生成 原型
Usage:
  python dws_deploy.py init         交互式录入配置
  python dws_deploy.py generate     一键生成配置文件
  python dws_deploy.py check        前置环境检查
  python dws_deploy.py show         查看当前配置
  python dws_deploy.py template list   查看模板列表
  python dws_deploy.py template save <name>  保存模板
  python dws_deploy.py template load <name>  加载模板
"""
import argparse
import json
import os
import sys
import shutil
from datetime import datetime
from dataclasses import dataclass, field, asdict
from typing import List, Optional

# Windows GBK compat
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# ── rich 彩显（如不可用则降级）──
try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.prompt import Prompt, Confirm
    from rich.syntax import Syntax
    from rich import box
    from rich.progress import track
    RICH_AVAIL = True
except ImportError:
    RICH_AVAIL = False
    # 降级
    class Console:
        def print(self, *a, **kw):
            print(*a)

console = Console() if RICH_AVAIL else Console()

# ── 数据模型 ──
@dataclass
class NodeInfo:
    """节点信息"""
    ip: str = ""
    hostname: str = ""
    mem_gb: int = 256
    os_disk: str = "/dev/sda"
    meta_disks: List[str] = field(default_factory=list)   # 元数据盘
    data_disks: List[str] = field(default_factory=list)   # 数据盘

@dataclass
class ClusterConfig:
    """集群配置"""
    name: str = "dws-cluster"
    version: str = "9.1.0"
    os_type: str = "Kylin-V10-SP2"
    os_arch: str = "aarch64"
    iso_path: str = "/opt/Kylin-Server-10-SP2-aarch64-Release.iso"
    gaussdb_pkg: str = "/opt/GaussDB_MPPDB_9.1.0_EULER_ARM64.zip"
    nodes: List[NodeInfo] = field(default_factory=list)
    oms_float_ip: str = ""
    platform: str = "aarch64"
    created_at: str = ""
    updated_at: str = ""

    def validate(self) -> List[str]:
        """配置自校验，返回错误列表"""
        errors = []
        if not self.nodes:
            errors.append("[X] 节点列表为空")
        if len(self.nodes) < 3:
            errors.append(f"!️  DWS 最少需要 3 个节点，当前仅 {len(self.nodes)} 个")
        if not self.iso_path:
            errors.append("[X] ISO 镜像路径未配置")
        if not self.gaussdb_pkg:
            errors.append("[X] GaussDB 安装包路径未配置")
        if not self.oms_float_ip:
            errors.append("[X] OMS 浮动 IP 未配置")
        for i, n in enumerate(self.nodes):
            if not n.ip:
                errors.append(f"[X] 节点 {i+1} IP 未配置")
            if not n.hostname:
                errors.append(f"[X] 节点 {i+1} 主机名未配置")
        return errors


# ── 配置中心 ──
CONFIG_DIR = os.path.expanduser("~/.dws_deploy")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")
TEMPLATE_DIR = os.path.join(CONFIG_DIR, "templates")


def ensure_dirs():
    os.makedirs(CONFIG_DIR, exist_ok=True)
    os.makedirs(TEMPLATE_DIR, exist_ok=True)


def load_config() -> ClusterConfig:
    """加载当前配置"""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            # Convert dict nodes to NodeInfo objects
            if "nodes" in data:
                data["nodes"] = [NodeInfo(**n) if isinstance(n, dict) else n for n in data["nodes"]]
            return ClusterConfig(**data)
        except Exception as e:
            console.print(f"[yellow]! 配置加载失败: {e}，使用默认配置[/yellow]")
    return ClusterConfig()


def save_config(cfg: ClusterConfig):
    """保存配置"""
    ensure_dirs()
    cfg.updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(asdict(cfg), f, ensure_ascii=False, indent=2)
    console.print("[green]+ 配置已保存[/green]")


# ── 交互式录入 ──
def cmd_init():
    """交互式配置录入"""
    cfg = load_config()

    console.print(Panel.fit(" DWS 部署配置向导 ", style="bold blue"))
    console.print()

    # 基本信息
    cfg.name = Prompt.ask("集群名称", default=cfg.name)
    cfg.version = Prompt.ask("DWS 版本", default=cfg.version)
    cfg.os_type = Prompt.ask("操作系统类型", default=cfg.os_type)
    cfg.os_arch = Prompt.ask("CPU 架构 (aarch64/x86_64)", default=cfg.os_arch)
    cfg.platform = cfg.os_arch

    # 路径配置
    cfg.iso_path = Prompt.ask("ISO 镜像路径", default=cfg.iso_path)
    cfg.gaussdb_pkg = Prompt.ask("GaussDB 安装包路径", default=cfg.gaussdb_pkg)
    cfg.oms_float_ip = Prompt.ask("OMS 浮动 IP", default=cfg.oms_float_ip)

    # 节点数
    n_nodes = Prompt.ask("节点数量（生产最小 3）", default=str(max(len(cfg.nodes), 3)))
    n_nodes = int(n_nodes)

    console.print("\n[bold]--- 节点配置 ---[/bold]")
    cfg.nodes = []
    for i in range(n_nodes):
        console.print(f"\n[cyan]>> 节点 {i+1}/{n_nodes}[/cyan]")
        existing = cfg.nodes[i] if i < len(cfg.nodes) else NodeInfo()
        ip = Prompt.ask(f"  管理 IP", default=existing.ip)
        hn = Prompt.ask(f"  主机名", default=existing.hostname)
        mem = Prompt.ask(f"  内存 (GB)", default=str(existing.mem_gb))

        # 磁盘配置
        console.print("  [dim]磁盘配置（用逗号分隔多个设备，如 /dev/sdb,/dev/sdc）[/dim]")
        meta = Prompt.ask(f"  元数据盘", default=",".join(existing.meta_disks) if existing.meta_disks else "/dev/sdb,/dev/sdc")
        data = Prompt.ask(f"  数据盘", default=",".join(existing.data_disks) if existing.data_disks else "/dev/sdd,/dev/sde")

        node = NodeInfo(
            ip=ip, hostname=hn, mem_gb=int(mem),
            meta_disks=[d.strip() for d in meta.split(",") if d.strip()],
            data_disks=[d.strip() for d in data.split(",") if d.strip()],
        )
        cfg.nodes.append(node)

    cfg.created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    save_config(cfg)
    show_config(cfg)


# ── 配置展示 ──
def show_config(cfg=None):
    """显示当前配置"""
    if cfg is None:
        cfg = load_config()
    if RICH_AVAIL:
        table = Table(title=f"集群配置: {cfg.name}", box=box.ROUNDED)
        table.add_column("节点", style="cyan")
        table.add_column("IP", style="green")
        table.add_column("主机名")
        table.add_column("内存(GB)")
        table.add_column("元数据盘")
        table.add_column("数据盘")
        for i, n in enumerate(cfg.nodes):
            table.add_row(
                f"节点{i+1}", n.ip, n.hostname, str(n.mem_gb),
                ",".join(n.meta_disks), ",".join(n.data_disks)
            )
        console.print(table)
        console.print(f"[dim]DWS {cfg.version} | {cfg.os_type} {cfg.os_arch}[/dim]")
        console.print(f"[dim]ISO: {cfg.iso_path}[/dim]")
        console.print(f"[dim]GaussDB: {cfg.gaussdb_pkg}[/dim]")
        console.print(f"[dim]浮动IP: {cfg.oms_float_ip}[/dim]")
    else:
        print(json.dumps(asdict(cfg), ensure_ascii=False, indent=2))

    # 校验
    errors = cfg.validate()
    if errors:
        for e in errors:
            console.print(f"[yellow]{e}[/yellow]")


# ── 模板生成 ──
def cmd_generate():
    """一键生成配置文件"""
    cfg = load_config()
    errors = cfg.validate()
    if errors:
        console.print("[red][X] 配置有误，请先执行 init 完善配置:[/red]")
        for e in errors:
            console.print(f"  {e}")
        return

    out_dir = os.path.expanduser("~/dws_generated")
    os.makedirs(out_dir, exist_ok=True)
    console.print(f"\n[bold blue]生成配置文件到: {out_dir}[/bold blue]\n")

    # 1. /etc/hosts
    hosts_path = os.path.join(out_dir, "hosts.txt")
    with open(hosts_path, "w", encoding="utf-8") as f:
        f.write("# DWS Cluster Hosts - Generated by dws_deploy.py\n")
        f.write(f"# {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("127.0.0.1   localhost localhost.localdomain\n\n")
        for n in cfg.nodes:
            f.write(f"{n.ip}\t\t{n.hostname}\n")
    console.print(f"  [green]+[/green] hosts: {hosts_path}")

    # 2. preinstall.ini
    ini_path = os.path.join(out_dir, "preinstall.ini")
    ips = ",".join(n.ip for n in cfg.nodes)
    host_conf = ";".join(f"{n.ip}#{n.ip}#{n.hostname}" for n in cfg.nodes)
    parted_conf = ";".join(f"{n.ip}#host{i}.ini" for i, n in enumerate(cfg.nodes))

    with open(ini_path, "w", encoding="utf-8") as f:
        f.write("# DWS Preinstall Config - Generated by dws_deploy.py\n")
        f.write(f"# {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"oms_ip1={cfg.nodes[0].ip}\n")
        f.write(f"oms_ip2={cfg.nodes[1].ip if len(cfg.nodes) > 1 else cfg.nodes[0].ip}\n")
        f.write(f'g_hosts="{ips}"\n')
        f.write('g_user_name="root"\n')
        f.write("g_port=22\n")
        f.write(f"g_parted={len(cfg.nodes)}\n")
        f.write(f'g_parted_conf="{parted_conf}"\n')
        f.write("g_add_pkg=1\n")
        f.write(f'g_pkgs_dir="kylin-V10-SP2:{cfg.iso_path}"\n')
        f.write(f'g_log_file="/tmp/fi-preinstall.log"\n')
        f.write("g_debug=0\n")
        f.write(f'g_hostname_conf="{host_conf}"\n')
        f.write("g_swap_off=1\n")
        f.write(f'g_platform="{cfg.platform}"\n')
    console.print(f"  [green]+[/green] preinstall.ini: {ini_path}")

    # 3. /etc/fstab
    fstab_path = os.path.join(out_dir, "fstab.txt")
    with open(fstab_path, "w", encoding="utf-8") as f:
        f.write("# DWS fstab - Generated by dws_deploy.py\n")
        f.write("# 注意: 请替换 UUID 为实际值 (blkid)\n\n")
        if cfg.nodes:
            n = cfg.nodes[0]  # 使用第一个节点作为模板
            for i, disk in enumerate(n.meta_disks):
                f.write(f"# {disk}1  -> 元数据盘\n")
                f.write(f"UUID=REPLACE_UUID_{i+1}  /srv/BigData/dbdata_om  xfs  defaults,noatime,nodiratime  1 0\n\n" if i == 0 else
                        f"UUID=REPLACE_UUID_{i+1}  /srv/BigData/LocalBackup  xfs  defaults,noatime,nodiratime  1 0\n\n")
            for i, disk in enumerate(n.data_disks):
                f.write(f"# {disk}1  -> 数据盘 data{i+1}\n")
                f.write(f"UUID=REPLACE_UUID_{len(n.meta_disks)+i+1}  /srv/BigData/mppdb/data{i+1}  xfs  defaults,noatime,nodiratime  1 0\n\n")
    console.print(f"  [green]+[/green] fstab: {fstab_path}")

    # 4. 分区脚本
    script_path = os.path.join(out_dir, "partition.sh")
    with open(script_path, "w", encoding="utf-8") as f:
        f.write("#!/bin/bash\n")
        f.write(f"# DWS Partition Script - Generated by dws_deploy.py\n\n")
        if cfg.nodes:
            n = cfg.nodes[0]
            for disk in n.meta_disks + n.data_disks:
                f.write(f"echo '=== Partitioning {disk} ==='\n")
                f.write(f"parted -s {disk} mklabel gpt\n")
                f.write(f"parted -s {disk} mkpart logic xfs 100M 100%\n")
                f.write(f"mkfs.xfs -f {disk}1\n")
                f.write(f"echo ''\n")
        f.write("\necho '=== All partitions done ==='\n")
    os.chmod(script_path, 0o755)
    console.print(f"  [green]+[/green] partition.sh: {script_path}")

    # 5. grub 参数参考
    grub_path = os.path.join(out_dir, "grub_params.txt")
    with open(grub_path, "w", encoding="utf-8") as f:
        f.write("# DWS Grub Parameters - Reference\n")
        f.write("# 添加到 GRUB_CMDLINE_LINUX 后执行 grub2-mkconfig\n\n")
        f.write('GRUB_CMDLINE_LINUX="... transparent_hugepage=never \\\n')
        f.write('  intel_idle.max_cstate=1 processor.max_cstate=1 \\\n')
        f.write('  amd_iommu=on iommu=pt ..."\n\n')
        f.write("# 生成配置:\n")
        f.write("# grub2-mkconfig -o /boot/efi/EFI/kylin/grub.cfg\n")
    console.print(f"  [green]+[/green] grub_params: {grub_path}")

    console.print(f"\n[bold green][OK] 配置文件已生成到: {out_dir}[/bold green]")
    console.print(f"  请将 preinstall.ini 上传到 /opt/FusionInsight_SetupTool/preinstall/")
    console.print(f"  将 hosts.txt 内容添加到各节点 /etc/hosts")
    console.print(f"  分区脚本用: sh partition.sh")


# ── 前置检查 ──
def cmd_check():
    """前置环境检查"""
    cfg = load_config()
    if RICH_AVAIL:
        console.print(Panel.fit(" DWS 环境前置检查 ", style="bold yellow"))
    console.print()

    checks = [
        ("OS 版本检测", f"预期: {cfg.os_type}", "check_os", lambda: True),
        ("CPU 架构检测", f"预期: {cfg.os_arch}", "check_arch", lambda: True),
        ("内存容量检测", f"≥ 256GB 建议", "check_mem", lambda: True),
        ("磁盘数量检测", f"元数据盘≥2 + 数据盘≥2", "check_disk_cnt",
         lambda: all(len(n.meta_disks) >= 2 and len(n.data_disks) >= 2 for n in cfg.nodes)),
        ("网络连通性检测", "节点间互通 (需手动验证)", "check_net", lambda: True),
        ("Python 版本检测", "≥ 3.8", "check_py", lambda: sys.version_info >= (3, 8)),
        ("ISO 镜像检测", cfg.iso_path, "check_iso",
         lambda: os.path.exists(cfg.iso_path) if not cfg.iso_path.startswith("/opt") else True),
        ("GaussDB 包检测", cfg.gaussdb_pkg, "check_pkg",
         lambda: os.path.exists(cfg.gaussdb_pkg) if not cfg.gaussdb_pkg.startswith("/opt") else True),
    ]

    passed = 0
    warned = 0
    failed = 0

    for name, expect, key, check_fn in checks:
        try:
            ok = check_fn()
        except:
            ok = False

        if ok:
            console.print(f"  [green]+[/green] {name}")
            console.print(f"       {expect}")
            passed += 1
        else:
            console.print(f"  [red]✗[/red] {name}")
            console.print(f"       [red]{expect}[/red]")
            failed += 1

    console.print()
    if RICH_AVAIL:
        table = Table(box=box.ROUNDED)
        table.add_column("结果", style="bold")
        table.add_column("数量")
        table.add_row("[green]通过[/green]", str(passed))
        table.add_row("[yellow]警告[/yellow]", str(warned))
        table.add_row("[red]失败[/red]", str(failed))
        console.print(table)
    else:
        console.print(f"通过: {passed}, 警告: {warned}, 失败: {failed}")

    if failed > 0:
        console.print("[yellow]!️  存在失败项，请修正后重新检查[/yellow]")
    else:
        console.print("[green][OK] 环境检查通过[/green]")


# ── 模板管理 ──
def cmd_template_list():
    """列出模板"""
    ensure_dirs()
    files = [f for f in os.listdir(TEMPLATE_DIR) if f.endswith(".json")]
    if not files:
        console.print("[yellow]暂无模板[/yellow]")
        return
    console.print("[bold]可用模板:[/bold]")
    for f in files:
        name = f[:-5]
        path = os.path.join(TEMPLATE_DIR, f)
        mtime = os.path.getmtime(path)
        console.print(f"  -> {name}  ({datetime.fromtimestamp(mtime):%Y-%m-%d %H:%M})")


def cmd_template_save(name: str):
    """保存为模板"""
    cfg = load_config()
    ensure_dirs()
    path = os.path.join(TEMPLATE_DIR, f"{name}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(asdict(cfg), f, ensure_ascii=False, indent=2)
    console.print(f"[green]+ 已保存模板: {name}[/green]")


def cmd_template_load(name: str):
    """加载模板"""
    path = os.path.join(TEMPLATE_DIR, f"{name}.json")
    if not os.path.exists(path):
        console.print(f"[red][X] 模板不存在: {name}[/red]")
        return
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if "nodes" in data:
        data["nodes"] = [NodeInfo(**n) if isinstance(n, dict) else n for n in data["nodes"]]
    cfg = ClusterConfig(**data)
    save_config(cfg)
    console.print(f"[green]+ 已加载模板: {name}[/green]")
    show_config(cfg)


# ── CLI 入口 ──
def main():
    parser = argparse.ArgumentParser(
        description="DWS 部署交互助手 v0.1",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python dws_deploy.py init             交互式录入配置
  python dws_deploy.py generate         生成配置文件
  python dws_deploy.py check            环境检查
  python dws_deploy.py show             查看配置
  python dws_deploy.py template list    模板列表
  python dws_deploy.py template save dev  保存为 dev 模板
  python dws_deploy.py template load dev  加载 dev 模板
        """
    )
    sub = parser.add_subparsers(dest="cmd", help="子命令")

    # init
    sub.add_parser("init", help="交互式配置录入")

    # show
    sub.add_parser("show", help="显示当前配置")

    # generate
    sub.add_parser("generate", help="一键生成配置文件")

    # check
    sub.add_parser("check", help="前置环境检查")

    # template
    tpl = sub.add_parser("template", help="模板管理")
    tpl_sub = tpl.add_subparsers(dest="tpl_cmd")
    tpl_sub.add_parser("list", help="列出模板")
    save_p = tpl_sub.add_parser("save", help="保存模板")
    save_p.add_argument("name", help="模板名称")
    load_p = tpl_sub.add_parser("load", help="加载模板")
    load_p.add_argument("name", help="模板名称")

    args = parser.parse_args()

    if not args.cmd:
        parser.print_help()
        return

    if args.cmd == "init":
        cmd_init()
    elif args.cmd == "show":
        show_config()
    elif args.cmd == "generate":
        cmd_generate()
    elif args.cmd == "check":
        cmd_check()
    elif args.cmd == "template":
        if not args.tpl_cmd:
            cmd_template_list()
        elif args.tpl_cmd == "list":
            cmd_template_list()
        elif args.tpl_cmd == "save":
            cmd_template_save(args.name)
        elif args.tpl_cmd == "load":
            cmd_template_load(args.name)


if __name__ == "__main__":
    main()
