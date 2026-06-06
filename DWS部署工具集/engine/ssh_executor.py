"""
DWS SSH 执行器 — 双模式（demo/ssh）

demo 模式: 返回命令文本，用户手动复制执行（零依赖）
ssh  模式: paramiko 连接节点，自动执行并采集结果

用法:
    executor = SSHExecutor(mode="demo")
    result = executor.run_check(precheck_item, node_ip)
    # → {"item_id":"hw-raid", "mode":"demo", "status":"pending",
    #     "cmd":"storcli64 ...", "detail":"在节点上执行以上命令"}

    executor = SSHExecutor(mode="ssh", username="root", password="xxx")
    result = executor.run_check(precheck_item, node_ip)
    # → {"item_id":"hw-raid", "mode":"ssh", "status":"pass|warn|fail",
    #     "detail":"RAID策略已配置", "stdout":"..."}
"""

import re
import time
from typing import Optional


class SSHExecutor:
    """双模式 SSH 执行器"""

    MODE_DEMO = "demo"
    MODE_SSH = "ssh"

    def __init__(self, mode: str = "demo", username: str = "root",
                 password: str = "", key_file: str = "", port: int = 22):
        self.mode = mode
        self.username = username
        self.password = password
        self.key_file = key_file
        self.port = port
        self._client = None

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

    # ── SSH 模式 ─────────────────────────────────────────

    def _connect(self, host: str) -> bool:
        """建立 SSH 连接（延迟连接，按需建立）"""
        try:
            import paramiko
            self._client = paramiko.SSHClient()
            self._client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            if self.key_file:
                self._client.connect(host, port=self.port,
                                     username=self.username,
                                     key_filename=self.key_file,
                                     timeout=10)
            else:
                self._client.connect(host, port=self.port,
                                     username=self.username,
                                     password=self.password,
                                     timeout=10)
            return True
        except ImportError:
            raise RuntimeError("paramiko 未安装，请执行: pip install paramiko")
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
          1. 如果命令包含 grep/echo 等关键词 → 检查 stdout 是否含预期值
          2. 如果命令返回非零 → 通常是 fail
          3. 特殊规则: 按 item.id 定制解析
        """
        item_id = item.get("id", "")
        stdout_clean = stdout.strip()
        lines = [l for l in stdout_clean.split("\n") if l.strip()]

        # 按 item.id 定制解析规则
        # 硬件类
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

        if item_id == "hw-ssd-check":
            has_hdd = "1" in [l.split()[-1] for l in lines if len(l.split()) >= 2]
            if not has_hdd:
                return {"status": "pass", "detail": "全部为SSD(ROTA=0)"}
            return {"status": "warn", "detail": f"存在HDD盘(ROTA=1): {stdout_clean[:100]}"}

        # OS 类
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
            return {"status": "pass" if "disabled" in stdout_clean.lower() else "warn",
                    "detail": f"SELinux={stdout_clean[:60]}"}

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
                return {"status": "pass", "detail": f"时区=Asia/Shanghai"}
            return {"status": "fail", "detail": f"时区={stdout_clean[:60]}(需Asia/Shanghai)"}

        # 存储类
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

        # 软件类
        if item_id in ("sw-python",):
            if "python" in stdout_clean.lower():
                return {"status": "pass", "detail": stdout_clean[:80]}
            return {"status": "fail", "detail": f"Python未安装: {stdout_clean[:80]}"}

        if item_id == "os-charset":
            if "utf-8" in stdout_clean.lower() or "utf8" in stdout_clean.lower():
                return {"status": "pass", "detail": f"字符集={stdout_clean.strip()}"}
            return {"status": "warn", "detail": f"字符集={stdout_clean.strip()}(建议en_US.UTF-8)"}

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
