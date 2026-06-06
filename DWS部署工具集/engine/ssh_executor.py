"""
DWS SSH 执行器 — 三模式（demo/ssh）+ 安全策略三等级

demo  模式: 返回命令文本，用户手动复制执行（零依赖）
ssh   模式: paramiko 连接节点，自动执行并采集结果
hybrid模式: 可 SSH 的节点自动执行，不可达的显示命令文本

安全策略三等级:
  strict  — 仅连接 known_hosts 中已知的主机
  warn    — 未知主机提示警告但可选接受（默认）
  insecure— 自动接受任何主机密钥（仅 demo 模式可用）

用法:
    executor = SSHExecutor(mode="demo")
    result = executor.run_check(precheck_item, node_ip)

    executor = SSHExecutor(mode="ssh", host_key_policy="warn")
    executor.connect("10.134.21.190", "root", password="xxx")
    result = executor.run_check(precheck_item, node_ip)
"""

import re
import time
import logging
from typing import Optional
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)


# ─── 安全策略 ──────────────────────────────────────────────

class SSHHostKeyPolicy:
    """SSH 主机密钥验证策略等级"""

    STRICT = "strict"       # 仅已知主机，拒绝未知
    WARN = "warn"           # 未知主机提示警告但可选接受
    INSECURE = "insecure"   # 自动接受（AutoAddPolicy）

    @staticmethod
    def validate(policy: str) -> str:
        """验证并规范化策略值"""
        if policy not in (SSHHostKeyPolicy.STRICT,
                          SSHHostKeyPolicy.WARN,
                          SSHHostKeyPolicy.INSECURE):
            return SSHHostKeyPolicy.WARN
        return policy

    @staticmethod
    def get_missing_host_key_policy(policy: str):
        """根据策略等级返回 paramiko 的 MissingHostKeyPolicy"""
        try:
            import paramiko
        except ImportError:
            return None

        if policy == SSHHostKeyPolicy.STRICT:
            return paramiko.RejectPolicy()
        elif policy == SSHHostKeyPolicy.WARN:
            return paramiko.WarningPolicy()
        else:
            return paramiko.AutoAddPolicy()

    @staticmethod
    def get_warning(policy: str) -> str:
        """获取安全策略的中文警告文本（用于 UI 展示）"""
        warnings = {
            SSHHostKeyPolicy.STRICT: "【安全模式】仅连接已知主机",
            SSHHostKeyPolicy.WARN: "【警告模式】首次连接未知主机需确认",
            SSHHostKeyPolicy.INSECURE: "【⚠️ 不安全】未验证主机身份，仅用于演示",
        }
        return warnings.get(policy, "")


# ─── 审计记录 ──────────────────────────────────────────────

@dataclass
class AuditRecord:
    """SSH 执行审计记录"""
    timestamp: str = ""          # 操作时间
    source_ip: str = ""          # 来源 IP
    operator: str = ""           # 操作人
    target_host: str = ""        # 目标主机
    command: str = ""            # 执行的命令
    exit_code: int = -1          # 返回码
    duration_sec: float = 0.0    # 执行耗时
    success: bool = False        # 是否成功
    detail: str = ""             # 详情/错误信息


# ─── SSH 执行器 ────────────────────────────────────────────

class SSHExecutor:
    """SSH 执行器 — 三模式 + 安全策略三等级"""

    MODE_DEMO = "demo"
    MODE_SSH = "ssh"
    MODE_HYBRID = "hybrid"
    VALID_MODES = (MODE_DEMO, MODE_SSH, MODE_HYBRID)

    def __init__(self, mode: str = "demo",
                 host_key_policy: str = "insecure",
                 username: str = "root",
                 credential_id: str = "",
                 port: int = 22,
                 source_ip: str = "",
                 operator: str = "",
                 audit_log: Optional[list] = None):
        """
        Args:
            mode: demo / ssh / hybrid
            host_key_policy: strict / warn / insecure（demo 模式强制 insecure）
            username: SSH 用户名
            credential_id: 凭据 ID（通过 CredentialManager 获取）
            port: SSH 端口
            source_ip: 来源 IP（用于审计）
            operator: 操作人（用于审计）
            audit_log: 外部审计日志列表（可选，用于记录操作）
        """
        self.mode = mode if mode in self.VALID_MODES else self.MODE_DEMO
        # demo 模式强制 INSECURE
        if self.mode == self.MODE_DEMO:
            self.host_key_policy = SSHHostKeyPolicy.INSECURE
        else:
            self.host_key_policy = SSHHostKeyPolicy.validate(host_key_policy)
        self.username = username
        self.credential_id = credential_id
        self._password = ""
        self._key_file = ""
        self.port = port
        self.source_ip = source_ip
        self.operator = operator
        self._client = None
        self._last_host = ""
        # 审计日志
        self.audit_log = audit_log if audit_log is not None else []
        self._resolve_credential()

    def _resolve_credential(self):
        """通过 CredentialManager 解析凭据（如果使用 credential_id）"""
        if self.credential_id and self.mode == self.MODE_SSH:
            try:
                from engine.credential_manager import get_credential_manager
                mgr = get_credential_manager()
                cred = mgr.get(self.credential_id)
                if cred:
                    c = cred.get("credential", {})
                    self._password = c.get("password", "")
                    self._key_file = c.get("key_file", "")
                    self.username = c.get("username", self.username)
            except ImportError:
                pass
        elif not self.credential_id and self.mode == self.MODE_SSH:
            # 兼容旧接口：直接用 password/key_file 参数（不推荐）
            pass

    @property
    def security_warning(self) -> str:
        """获取安全策略的中文警告文本"""
        return SSHHostKeyPolicy.get_warning(self.host_key_policy)

    @property
    def policy_label(self) -> str:
        """获取安全策略标签"""
        labels = {
            SSHHostKeyPolicy.STRICT: "严格",
            SSHHostKeyPolicy.WARN: "警告",
            SSHHostKeyPolicy.INSECURE: "不安全",
        }
        return labels.get(self.host_key_policy, "未知")

    # ── 公共 API ──────────────────────────────────────────

    def run_check(self, item: dict, node_ip: str) -> dict:
        """执行单条预检项（自动根据 mode 分发）"""
        if self.mode == self.MODE_DEMO:
            return self._run_demo(item, node_ip)
        return self._run_ssh(item, node_ip)

    def run_checks(self, items: list, node_ips: list, parallel: bool = True) -> list:
        """批量执行预检项

        Args:
            items: PRECHECK_ITEMS 列表
            node_ips: 节点 IP 列表
            parallel: 是否并行执行（ssh 模式下生效）

        Returns: [{"item_id":..., "node":..., "status":..., ...}, ...]
        """
        results = []
        if self.mode == self.MODE_DEMO or not parallel:
            # 串行执行
            for item in items:
                for ip in node_ips:
                    results.append(self.run_check(item, ip))
        else:
            # ssh 模式下暂不实现真并行，先串行（避免连接风暴）
            # 后续可升级为 ThreadPoolExecutor
            for item in items:
                for ip in node_ips:
                    results.append(self.run_check(item, ip))
        return results

    def format_node_commands(self, items: list, node_ips: list) -> str:
        """生成用户可复制粘贴的命令文本（demo 模式用）"""
        lines = [
            "=" * 60,
            f"  DWS 环境预检命令集 — demo 模式",
            f"  节点: {', '.join(node_ips)}",
            f"  检查项: {len(items)} 项",
            "=" * 60,
            "",
        ]
        for item in items:
            cat = item.get("category", "")
            name = item.get("name", item.get("id", ""))
            cmd = item.get("check_cmd", "")
            sev = item.get("severity", "info")
            sev_tag = {"error": "[必需]", "warning": "[建议]"}.get(sev, "[信息]")
            lines.append(f"── {sev_tag} [{cat}] {name} ──")
            lines.append(f"   命令: {cmd}")
            lines.append(f"   说明: {item.get('description', '')}")
            lines.append("")

        # 按节点输出执行建议
        for ip in node_ips:
            lines.append(f"── 在节点 {ip} 上执行 ──")
            for item in items:
                cmd = item.get("check_cmd", "")
                lines.append(f"  ssh {ip} \"{cmd}\"")
            lines.append("")

        lines.append(f"── 修复建议 ──")
        for item in items:
            if item.get("solution"):
                lines.append(f"  [{item.get('name','')}] {item['solution']}")
        lines.append("")
        return "\n".join(lines)

    # ── demo 模式 ────────────────────────────────────────

    def _run_demo(self, item: dict, node_ip: str) -> dict:
        """demo 模式：返回命令文本，不真实执行"""
        return {
            "item_id": item.get("id", ""),
            "item_name": item.get("name", ""),
            "category": item.get("category", ""),
            "node": node_ip,
            "mode": "demo",
            "status": "pending",
            "cmd": item.get("check_cmd", ""),
            "detail": f"[Demo] 请在节点 {node_ip} 上手动执行以上命令",
            "solution": item.get("solution", ""),
        }

    # ── 审计记录 ──────────────────────────────────────────

    def _add_audit_record(self, target_host: str, command: str,
                          exit_code: int, duration_sec: float,
                          success: bool, detail: str = ""):
        """添加一条审计记录"""
        record = AuditRecord(
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            source_ip=self.source_ip or "localhost",
            operator=self.operator or self.username,
            target_host=target_host,
            command=command[:200],
            exit_code=exit_code,
            duration_sec=round(duration_sec, 1),
            success=success,
            detail=detail[:200],
        )
        self.audit_log.append({
            "timestamp": record.timestamp,
            "source_ip": record.source_ip,
            "operator": record.operator,
            "target_host": record.target_host,
            "command": record.command,
            "exit_code": record.exit_code,
            "duration_sec": record.duration_sec,
            "success": record.success,
            "detail": record.detail,
        })

    # ── SSH 模式 ─────────────────────────────────────────

    def _connect(self, host: str) -> bool:
        """建立 SSH 连接（延迟连接，按需建立）"""
        try:
            import paramiko
            self._client = paramiko.SSHClient()
            # 使用安全策略
            policy_class = SSHHostKeyPolicy.get_missing_host_key_policy(
                self.host_key_policy)
            if policy_class:
                self._client.set_missing_host_key_policy(policy_class)
            # 连接
            if self._key_file:
                self._client.connect(host, port=self.port,
                                     username=self.username,
                                     key_filename=self._key_file,
                                     timeout=10)
            else:
                self._client.connect(host, port=self.port,
                                     username=self.username,
                                     password=self._password or self.password,
                                     timeout=10)
            self._last_host = host
            return True
        except ImportError:
            raise RuntimeError("paramiko 未安装，请执行: pip install paramiko")
        except paramiko.SSHException as e:
            self._client = None
            if "not found in known_hosts" in str(e).lower():
                raise PermissionError(
                    f"主机 {host} 不在 known_hosts 中。"
                    f"请先手动连接: ssh {self.username}@{host}"
                    f"或将安全策略设为 warn")
            raise ConnectionError(f"SSH 连接失败 {host}:{self.port} — {e}")
        except Exception as e:
            self._client = None
            raise ConnectionError(f"无法连接到 {host}:{self.port} — {e}")

    def _exec_cmd(self, cmd: str) -> tuple:
        """在已连接的节点上执行单条命令，返回 (stdout, stderr, exit_code)"""
        if not self._client:
            raise RuntimeError("未连接，请先调用 connect()")
        stdin, stdout, stderr = self._client.exec_command(cmd, timeout=30)
        exit_code = stdout.channel.recv_exit_status()
        return stdout.read().decode("utf-8", errors="replace"), \
               stderr.read().decode("utf-8", errors="replace"), \
               exit_code

    def _close(self):
        """关闭连接"""
        if self._client:
            self._client.close()
            self._client = None

    def _parse_result(self, item: dict, stdout: str) -> dict:
        """根据预检项规则解析 SSH 返回结果

        判断逻辑:
          1. 检查 stdout 是否含预期值
          2. 按 item.id 定制解析规则（覆盖全部 40 项）
          3. 无特化规则时走默认 fallback
        """
        item_id = item.get("id", "")
        stdout_clean = stdout.strip()
        lines = [l for l in stdout_clean.split("\n") if l.strip()]

        # ── 硬件类 (12项) ─────────────────────────────────────
        if item_id == "hw-raid":
            has_read = "read ahead" in stdout_clean.lower()
            has_write = "write back" in stdout_clean.lower()
            if has_read and has_write:
                return {"status": "pass", "detail": "RAID策略已配置 (Read Ahead + Write Back)"}
            return {"status": "warn", "detail": f"RAID策略可能未按规范配置: {stdout_clean[:100]}"}

        if item_id == "hw-disk-count":
            try:
                count = int(stdout_clean.split("\n")[-1])
                if count >= 6:
                    return {"status": "pass", "detail": f"{count}块盘/节点 (满足生产≥6)"}
                return {"status": "warn", "detail": f"{count}块盘 (建议≥6)"}
            except ValueError:
                return {"status": "warn", "detail": f"无法解析磁盘数量: {stdout_clean[:80]}"}

        if item_id == "hw-network-card":
            if "speed" in stdout_clean.lower() or "duplex" in stdout_clean.lower():
                return {"status": "pass", "detail": f"网卡正常: {stdout_clean[:80]}"}
            return {"status": "warn", "detail": f"网卡信息: {stdout_clean[:80]}"}

        if item_id == "hw-ssd-check":
            has_hdd = "1" in [l.split()[-1] for l in lines if len(l.split()) >= 2]
            if not has_hdd:
                return {"status": "pass", "detail": "全部为SSD(ROTA=0)"}
            return {"status": "warn", "detail": f"存在HDD盘(ROTA=1): {stdout_clean[:100]}"}

        if item_id == "hw-bios-numa":
            if "0" in stdout_clean:
                return {"status": "pass", "detail": f"numa_balancing=0 (已关闭)"}
            return {"status": "warn", "detail": f"numa_balancing={stdout_clean[:30]} (需=0)"}

        if item_id == "hw-bios-version":
            has_ver = any(v in stdout_clean for v in ["V158", "V159", "V160"])
            if has_ver:
                return {"status": "pass", "detail": f"BIOS版本: {stdout_clean[:60]}"}
            return {"status": "warn", "detail": f"BIOS版本: {stdout_clean[:60]} (建议≥V158)"}

        if item_id == "hw-uefi-mode":
            if "uefi" in stdout_clean.lower():
                return {"status": "pass", "detail": "UEFI模式"}
            return {"status": "fail", "detail": "Legacy模式, 需重装OS为UEFI"}

        if item_id == "hw-cpu-freq":
            try:
                freq = float(stdout_clean.split()[0]) if stdout_clean else 0
                if freq >= 2400:
                    return {"status": "pass", "detail": f"CPU频率={freq:.0f}MHz"}
                return {"status": "warn", "detail": f"CPU频率={freq:.0f}MHz (需≥2400)"}
            except (ValueError, IndexError):
                return {"status": "warn", "detail": f"无法解析CPU频率: {stdout_clean[:80]}"}

        if item_id == "hw-mem-freq":
            if "speed" in stdout_clean.lower() or "mhz" in stdout_clean.lower() or "mt/s" in stdout_clean.lower():
                return {"status": "pass", "detail": f"内存频率: {stdout_clean[:80]}"}
            return {"status": "warn", "detail": f"内存频率: {stdout_clean[:80]}"}

        if item_id == "hw-pcie-link":
            if "lnk" in stdout_clean.lower():
                return {"status": "pass", "detail": f"PCIe链路: {stdout_clean[:80]}"}
            return {"status": "warn", "detail": f"PCIe信息: {stdout_clean[:80]}"}

        if item_id == "hw-raid-cache":
            if "cache" in stdout_clean.lower() or "read" in stdout_clean.lower():
                return {"status": "pass", "detail": f"RAID缓存: {stdout_clean[:80]}"}
            return {"status": "warn", "detail": f"缓存信息: {stdout_clean[:80]}"}

        if item_id == "hw-bbu-status":
            if "state" in stdout_clean.lower() and "ok" in stdout_clean.lower():
                return {"status": "pass", "detail": "BBU状态正常"}
            if "未检测" in stdout_clean or "no bbu" in stdout_clean.lower():
                return {"status": "warn", "detail": "未检测到BBU"}
            return {"status": "warn", "detail": f"BBU状态: {stdout_clean[:80]}"}

        # ── OS 类 (15项) ──────────────────────────────────────
        if item_id == "os-audit":
            if "inactive" in stdout_clean.lower() or "unknown" in stdout_clean.lower():
                return {"status": "pass", "detail": "auditd已关闭"}
            return {"status": "fail", "detail": "auditd运行中，需要关闭"}

        if item_id == "os-firewall":
            fw_ok = "inactive" in stdout_clean.lower() or "disabled" in stdout_clean.lower()
            if fw_ok:
                return {"status": "pass", "detail": "firewalld已关闭"}
            return {"status": "warn", "detail": "firewalld未关闭，需要确认"}

        if item_id == "os-selinux":
            if "disabled" in stdout_clean.lower():
                return {"status": "pass", "detail": "SELinux=disabled"}
            return {"status": "warn", "detail": f"SELinux={stdout_clean[:60]}"}

        if item_id == "os-swap":
            if stdout_clean == "0" or not stdout_clean:
                return {"status": "pass", "detail": "swap已关闭"}
            return {"status": "fail", "detail": f"swap未完全关闭: {stdout_clean[:80]}"}

        if item_id == "os-hugepage":
            if "never" in stdout_clean:
                return {"status": "pass", "detail": "透明大页已关闭"}
            return {"status": "fail", "detail": "透明大页未关闭"}

        if item_id == "os-timezone":
            if "asia/shanghai" in stdout_clean.lower():
                return {"status": "pass", "detail": "时区=Asia/Shanghai"}
            return {"status": "fail", "detail": f"时区={stdout_clean[:60]}(需Asia/Shanghai)"}

        if item_id == "os-charset":
            if "utf-8" in stdout_clean.lower() or "utf8" in stdout_clean.lower():
                return {"status": "pass", "detail": f"字符集={stdout_clean.strip()}"}
            return {"status": "warn", "detail": f"字符集={stdout_clean.strip()}(建议en_US.UTF-8)"}

        if item_id == "os-kernel-params":
            if "watermark" in stdout_clean.lower() and "numa" in stdout_clean.lower():
                return {"status": "pass", "detail": f"内核参数: {stdout_clean[:100]}"}
            return {"status": "warn", "detail": f"内核参数: {stdout_clean[:100]}"}

        if item_id == "os-umask":
            if "0022" in stdout_clean:
                return {"status": "pass", "detail": "umask=0022"}
            return {"status": "warn", "detail": f"umask={stdout_clean.strip()} (建议0022)"}

        if item_id == "os-file-max":
            try:
                val = int(stdout_clean.split()[-1])
                if val >= 1000000:
                    return {"status": "pass", "detail": f"fs.file-max={val}"}
                return {"status": "warn", "detail": f"fs.file-max={val} (需≥1000000)"}
            except (ValueError, IndexError):
                return {"status": "warn", "detail": f"file-max: {stdout_clean[:80]}"}

        if item_id == "os-tcp-params":
            has_tw_reuse = "tcp_tw_reuse = 1" in stdout_clean
            has_somaxconn = "somaxconn" in stdout_clean and "65535" in stdout_clean
            if has_tw_reuse and has_somaxconn:
                return {"status": "pass", "detail": f"TCP参数正常: {stdout_clean[:120]}"}
            return {"status": "warn", "detail": f"TCP参数: {stdout_clean[:120]}"}

        if item_id == "os-arp-filter":
            if "arp_filter" in stdout_clean.lower():
                return {"status": "pass", "detail": f"ARP配置: {stdout_clean[:100]}"}
            return {"status": "pass", "detail": f"ARP参数: {stdout_clean[:100]}"}

        if item_id == "os-ntp-offset":
            if "yes" in stdout_clean.lower() or "synchronized" in stdout_clean.lower():
                return {"status": "pass", "detail": "NTP已同步"}
            if "system time" in stdout_clean.lower():
                return {"status": "pass", "detail": f"NTP偏移: {stdout_clean[:60]}"}
            return {"status": "fail", "detail": "NTP未同步, 需检查chrony配置"}

        if item_id == "os-ssh-config":
            if "maxsessions" in stdout_clean.lower() or "usedns" in stdout_clean.lower():
                return {"status": "pass", "detail": f"SSH配置: {stdout_clean[:100]}"}
            return {"status": "warn", "detail": "SSH配置未定制(建议: MaxSessions=1024, UseDNS=no)"}

        if item_id == "os-password-policy":
            if "pass_max_days" in stdout_clean.lower():
                return {"status": "pass", "detail": f"密码策略: {stdout_clean[:100]}"}
            return {"status": "warn", "detail": "密码策略未配置(建议: PASS_MAX_DAYS=90)"}

        # ── 网络类 (8项) ──────────────────────────────────────
        if item_id == "net-switch-mtu":
            if "mtu 1500" in stdout_clean.lower():
                return {"status": "pass", "detail": "MTU=1500 全网一致"}
            return {"status": "warn", "detail": f"MTU配置: {stdout_clean[:80]}"}

        if item_id == "net-vlan-config":
            if "vlan" in stdout_clean.lower() or "802.1q" in stdout_clean.lower():
                return {"status": "pass", "detail": f"VLAN已配置: {stdout_clean[:80]}"}
            return {"status": "warn", "detail": "未配置VLAN标记"}

        if item_id == "net-route-reach":
            if "不可达" not in stdout_clean and "timeout" not in stdout_clean.lower() and stdout_clean:
                return {"status": "pass", "detail": "路由可达"}
            return {"status": "fail", "detail": f"路由不可达: {stdout_clean[:80]}"}

        if item_id == "net-bandwidth-test":
            if "iperf3已安装" in stdout_clean:
                return {"status": "pass", "detail": "iperf3已安装, 可用于带宽测试"}
            return {"status": "warn", "detail": f"iperf3未安装: {stdout_clean[:80]}"}

        if item_id == "net-retrans":
            if "retransmit" in stdout_clean.lower() or "retrans" in stdout_clean.lower():
                parts = stdout_clean.split()
                if parts and parts[-1].isdigit():
                    val = int(parts[-1])
                    if val < 100:
                        return {"status": "pass", "detail": f"重传统计正常 (重传={val})"}
                    return {"status": "warn", "detail": f"重传={val}, 需进一步检查"}
                return {"status": "pass", "detail": f"TCP统计: {stdout_clean[:60]}"}
            return {"status": "pass", "detail": "无法精确计算重传率(需用netstat -s)"}

        if item_id == "net-port-negotiation":
            if "mb/s" in stdout_clean.lower():
                return {"status": "pass", "detail": f"端口协商: {stdout_clean[:100]}"}
            return {"status": "warn", "detail": f"端口速率: {stdout_clean[:100]}"}

        if item_id == "net-stp-status":
            if "no-carrier" in stdout_clean.upper():
                return {"status": "warn", "detail": f"存在端口未连接: {stdout_clean[:80]}"}
            return {"status": "pass", "detail": "网络接口状态正常"}

        if item_id == "net-mac-table":
            if "neighbor" in stdout_clean.lower() or "reachable" in stdout_clean.lower() or "stale" in stdout_clean.lower():
                return {"status": "pass", "detail": f"邻居表正常: {stdout_clean[:80]}"}
            if not stdout_clean:
                return {"status": "warn", "detail": "无邻居条目(可能未配置网络)"}
            return {"status": "pass", "detail": f"MAC表: {stdout_clean[:80]}"}

        # ── 存储类 (5项) ──────────────────────────────────────
        if item_id in ("stor-mount",):
            targets = ["/srv/BigData", "dbdata_om", "mppdb"]
            found = sum(1 for t in targets if t in stdout_clean)
            if found >= 2:
                return {"status": "pass", "detail": f"关键目录已挂载 ({found}/{len(targets)}匹配)"}
            return {"status": "warn", "detail": f"挂载可能不完整: {stdout_clean[:100]}"}

        if item_id in ("stor-fstab",):
            if "未配置" not in stdout_clean and stdout_clean:
                return {"status": "pass", "detail": "/etc/fstab已配置"}
            return {"status": "fail", "detail": "/etc/fstab未配置"}

        if item_id == "stor-striping":
            if "strip" in stdout_clean.lower() or "chunk" in stdout_clean.lower():
                return {"status": "pass", "detail": f"条带化配置: {stdout_clean[:80]}"}
            return {"status": "warn", "detail": f"条带信息: {stdout_clean[:80]}"}

        if item_id == "stor-alignment":
            if "2048s" in stdout_clean or "s" in stdout_clean:
                return {"status": "pass", "detail": f"分区对齐: {stdout_clean[:80]}"}
            return {"status": "warn", "detail": f"分区信息: {stdout_clean[:80]}"}

        if item_id == "stor-readahead":
            try:
                val = int(stdout_clean.split()[-1])
                if val >= 4096:
                    return {"status": "pass", "detail": f"readahead={val} (≥4096)"}
                return {"status": "warn", "detail": f"readahead={val} (建议≥4096)"}
            except (ValueError, IndexError):
                return {"status": "warn", "detail": f"readahead: {stdout_clean[:80]}"}

        # ── 软件类 (2项) ──────────────────────────────────────
        if item_id in ("sw-python",):
            if "python" in stdout_clean.lower():
                return {"status": "pass", "detail": stdout_clean[:80]}
            return {"status": "fail", "detail": f"Python未安装: {stdout_clean[:80]}"}

        if item_id == "sw-yum":
            if "gcc" in stdout_clean or "installed" in stdout_clean or stdout_clean:
                return {"status": "pass", "detail": "yum源可用"}
            return {"status": "fail", "detail": "yum源不可用"}

        # 默认解析：有输出且非空判定为 pass
        if stdout_clean and "未安装" not in stdout_clean and "FAIL" not in stdout_clean.upper() and "error" not in stdout_clean.lower():
            return {"status": "pass", "detail": stdout_clean[:80]}
        return {"status": "warn", "detail": stdout_clean[:100] if stdout_clean else "无输出"}

    def _run_ssh(self, item: dict, node_ip: str) -> dict:
        """ssh 模式：真实执行并解析结果"""
        cmd = item.get("check_cmd", "")
        if not cmd:
            return {
                "item_id": item.get("id", ""),
                "item_name": item.get("name", ""),
                "category": item.get("category", ""),
                "node": node_ip,
                "mode": "ssh",
                "status": "fail",
                "detail": "无检查命令",
            }

        try:
            connected = self._connect(node_ip)
            if not connected:
                raise ConnectionError(f"无法连接到 {node_ip}")

            self._last_host = node_ip
            start = time.time()
            stdout, stderr, exit_code = self._exec_cmd(cmd)
            elapsed = round(time.time() - start, 1)

            parsed = self._parse_result(item, stdout)
            status = parsed["status"]
            detail = parsed["detail"]

            # 如果 exit_code != 0 且解析结果是 pass，降级为 warn
            if exit_code != 0 and status == "pass":
                status = "warn"
                detail = f"{detail} (exit_code={exit_code})"

            self._close()

            # 记录审计
            self._add_audit_record(
                target_host=node_ip,
                command=cmd,
                exit_code=exit_code,
                duration_sec=elapsed,
                success=(status != "fail"),
                detail=detail[:100],
            )

            return {
                "item_id": item.get("id", ""),
                "item_name": item.get("name", ""),
                "category": item.get("category", ""),
                "node": node_ip,
                "mode": "ssh",
                "status": status,
                "detail": detail,
                "stdout": stdout[:500],
                "stderr": stderr[:200] if stderr else "",
                "exit_code": exit_code,
                "elapsed_sec": elapsed,
                "solution": item.get("solution", "") if status != "pass" else "",
            }

        except ImportError:
            return {
                "item_id": item.get("id", ""),
                "item_name": item.get("name", ""),
                "category": item.get("category", ""),
                "node": node_ip,
                "mode": "ssh",
                "status": "fail",
                "detail": "paramiko 未安装。执行: pip install paramiko",
            }
        except Exception as e:
            self._close()
            return {
                "item_id": item.get("id", ""),
                "item_name": item.get("name", ""),
                "category": item.get("category", ""),
                "node": node_ip,
                "mode": "ssh",
                "status": "fail",
                "detail": str(e)[:200],
            }

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self._close()
