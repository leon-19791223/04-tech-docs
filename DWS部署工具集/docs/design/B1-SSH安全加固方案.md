# B-1：SSH 安全加固

## 1. 现状分析

`engine/ssh_executor.py` 当前存在以下安全问题：

| 风险 | 位置 | 描述 | 严重程度 |
|:-----|:------|:------|:--------:|
| 主机密钥无验证 | 第130行 `AutoAddPolicy()` | 自动接受任何未知主机的密钥，存在中间人攻击(MITM)风险 | **高** |
| 明文凭据传输 | `app.py` `/api/precheck/run` | SSH 密码/key 在 HTTP POST 中明文传输，存于内存 | **中** |
| 无操作审计 | 整个类 | 谁在什么时间执行了什么命令没有记录 | **中** |
| 无访问控制 | `app.py` 全部路由 | SSH 模式可被任意调用 | **中** |

## 2. 改造目标

| 维度 | 当前状态 | 目标状态 |
|:------|:---------|:---------|
| 主机密钥验证 | 全接受(AutoAddPolicy) | 三等级可切换(strict/warn/insecure) |
| 凭据管理 | 明文传/明文存 | 一次性加密凭据 + TTL 自动过期 |
| 操作审计 | 无 | 记录操作人IP/时间/命令/返回码/耗时 |
| 访问控制 | 无 | Token 鉴权中间件(可选) |
| demo 模式 | 安全策略不适用 | demo 强制 insecure + 红字警告 |

## 3. 技术方案

### 3.1 SSH 安全策略三等级

在 `ssh_executor.py` 中新增 `SSHHostKeyPolicy` 枚举/类：

```python
class SSHHostKeyPolicy:
    """SSH 主机密钥验证策略"""
    
    # 严格模式：仅连接 known_hosts 中已知的主机
    # 使用 paramiko.RejectPolicy，未知主机直接拒绝
    STRICT = "strict"
    
    # 警告模式：未知主机提示警告但可选接受
    # 使用 paramiko.WarningPolicy，将警告写入日志
    WARN = "warn"
    
    # 不安全模式：自动接受任何主机密钥（原 AutoAddPolicy）
    # 仅 demo 模式可用，页面显示红字警告
    INSECURE = "insecure"
```

策略选择逻辑：

```
demo 模式 → 强制 INSECURE（显示红字警告："未验证主机身份"）
SSH 模式 → 默认 WARN（可通过配置切换到 STRICT）
```

### 3.2 凭据加密管理

新增 `engine/credential_manager.py`：

```python
class CredentialManager:
    """凭据管理器 — 加密存储 + TTL 自动过期
    
    使用 fernet 对称加密（Python cryptography 包）
    凭据在内存中加密存储，get() 后自动清除
    """
    
    def store(self, cred_type: str, credential: dict) -> str:
        """加密存储凭据，返回 credential_id（UUID）"""
        # 1. 序列化凭据为 JSON
        # 2. 使用 fernet 加密
        # 3. 存入内存 dict {credential_id: {data, expires_at, created_at, source_ip}}
        # 4. 设置 TTL（默认 300 秒）
        pass
    
    def get(self, credential_id: str) -> Optional[dict]:
        """获取凭据（一次性，获取后立即删除）"""
        # 1. 检查是否过期
        # 2. 解密返回
        # 3. 立即从内存中删除
        pass
    
    def cleanup_expired(self) -> int:
        """清理过期凭据，返回清理数量"""
        pass
```

### 3.3 操作审计增强

在 `ssh_executor.py` 中集成审计记录：

```python
@dataclass
class AuditRecord:
    timestamp: str
    source_ip: str
    username: str
    command: str
    exit_code: int
    duration_sec: float
    target_host: str
    success: bool
```

每次 SSH 执行后自动记录审计信息：
- 谁（操作用户身份）
- 什么时间
- 从哪来（source_ip）
- 做了什么（执行的命令）
- 结果如何（返回码/成功/失败）
- 耗时

### 3.4 Token 鉴权中间件（可选）

在 `app.py` 中新增简单 Token 鉴权：

```python
def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        # 如果鉴权未启用，直接放行
        if not app.config.get('AUTH_ENABLED', False):
            return f(*args, **kwargs)
        
        # 从请求头获取 Token
        token = request.headers.get('X-Auth-Token') or \
                request.args.get('token')
        
        if token != app.config.get('AUTH_TOKEN', 'dws-default-token'):
            return jsonify({"error": "未授权访问"}), 401
        
        return f(*args, **kwargs)
    return decorated
```

## 4. 改动文件清单

| 文件 | 操作 | 内容 |
|:-----|:------|:------|
| `engine/ssh_executor.py` | **修改** | SSHHostKeyPolicy 三等级 + 审计记录 |
| `engine/credential_manager.py` | **新增** | 凭据加密存储与自动过期 |
| `app.py` | **修改** | 新增鉴权中间件 + 凭据管理路由 + SSH 模式安全策略 |
| `templates/dws_precheck.html` | **修改** | SSH 模式增加安全策略选择 UI |
| `docs/design/B1-SSH安全加固方案.md` | **新增** | 本设计文档 |

## 5. 影响范围

| 模式 | 影响 | 说明 |
|:-----|:------|:------|
| **demo 模式** | 无影响 | 强制 INSECURE 策略 + 红字警告，功能不变 |
| **SSH 模式（新）** | 行为变化 | 默认 WARN 策略，首次连接未知主机需确认 |
| **SSH 模式（与旧系统）** | 向后兼容 | 可通过配置切换回 INSECURE 恢复旧行为 |
| **嘉兴 POC** | **零影响** | 修改全在 DWS部署工具集/ 目录内 |

## 6. 测试方案

| 编号 | 用例 | 方法 | 预期 |
|:-----|:------|:------|:------|
| TC-B1-01 | STRICT 策略拒绝未知主机 | 模拟连接未知 IP | 连接失败，明确提示主机密钥未知 |
| TC-B1-02 | WARN 策略提示但可连接 | 模拟连接未知 IP | 提示警告，连接继续 |
| TC-B1-03 | INSECURE 策略自动接受 | 模拟连接未知 IP | 自动接受，无缝连接 |
| TC-B1-04 | demo 模式强制 INSECURE | 创建 SSHExecutor(mode="demo") | policy 始终为 INSECURE |
| TC-B1-05 | 凭据加密后不可逆读取明文 | 加密后检查内存 | 内存中无明文密码 |
| TC-B1-06 | 凭据 TTL 过期自动清除 | 创建凭据，等待 TTL + 1 秒 | get() 返回 None |
| TC-B1-07 | 凭据一次性使用 | get() 后再次 get() | 第二次返回 None |
| TC-B1-08 | 审计记录含全部字段 | 模拟 SSH 执行 | 记录含 timestamp/source_ip/command/exit_code/duration |
| TC-B1-09 | 鉴权中间件开启未带 Token 返回 401 | HTTP 请求无 Token | 返回 401 |
| TC-B1-10 | 鉴权中间件关闭不影响 demo | 关闭鉴权，访问所有路由 | 全部正常 |
| TC-B1-11 | 回归：`/api/health` 正常 | 启动后 curl | 返回 200 + 版本信息 |
