# GuardRail 🛡️

**LLM 内容审核护栏** — 防止工具输出污染对话上下文，避免 DeepSeek / OpenAI / Claude 的 400 错误。

[![PyPI](https://img.shields.io/pypi/v/guardrail-safety?color=blue&label=PyPI)](https://pypi.org/project/guardrail-safety/)
[![Python](https://img.shields.io/pypi/pyversions/guardrail-safety?label=Python)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Gitee](https://img.shields.io/badge/Gitee-主仓库-orange)](https://gitee.com/zhangzhiwei610/GuardRail)
[![GitHub](https://img.shields.io/badge/GitHub-镜像-black)](https://github.com/16522246/GuardRail)

---

## 这是什么？

用 LLM API 的人都遇到过这个问题：

```
HTTP 400: Content Exists Risk       ← DeepSeek
HTTP 400: content_policy_violation  ← OpenAI
```

**整条会话报废，必须清空上下文重新开始。**

根因不是你的 system prompt，也不是用户输入——而是**工具输出**（搜索结果、网页抓取、文件读取）里的敏感内容混进了对话上下文。

GuardRail 在 LLM API 和外部内容之间加一道**安全护栏**：扫描 → 检测 → 脱敏，防止脏数据污染你的会话。

---

## 真实案例

PA 搜 GitHub「量化」相关项目，搜索结果混入了 `funNLP`：

```
⭐ fighting41love/funNLP — 反动词表、暴恐词表、敏感词库、中文谣言数据...
```

这些关键词触发了 DeepSeek 审核，**47 条消息全部被拒**，整条会话报废。

```python
# 一行代码解决
from guardrail import GuardRail
gr = GuardRail()
result = gr.scan(tool_output)
if not result.safe:
    tool_output = result.sanitized  # 敏感词已脱敏，会话安全
```

---

## 安装

```bash
pip install guardrail-safety
```

---

## 快速开始

### 3 行代码接入

```python
from guardrail import GuardRail

gr = GuardRail()
result = gr.scan("搜索结果包含敏感内容...")
print(result.safe)      # False
print(result.triggers)  # ['illegal_content']
print(result.sanitized) # 敏感词已被替换
```

### 四种集成模式

| 模式 | 场景 | 示例 |
|------|------|------|
| **Python 库** | Agent 代码中直接调用 | `gr.scan(text)` |
| **CLI** | 命令行手动扫描 | `guardrail scan --text "..."` |
| **代理中间件** | FastAPI / Flask 自动拦截 | `GuardRailMiddleware()` |
| **Hermes Skill** | Agent 自动加载 | `skill_view('content-safety-scanner')` |

---

## 详细用法

### Python API

```python
from guardrail import GuardRail, Sanitizer

# 初始化扫描器
gr = GuardRail()

# 扫描文本
result = gr.scan("My IP is 192.168.1.1 and I used sqlmap to scan.")
print(result.safe)       # False
print(result.triggers)   # ['ip_address', 'hacker_tools']
print(result.sanitized)  # "My IP is [REDACTED IP ADDRESS] and I used [HACKING TOOL REFERENCE REMOVED] to scan."

# 检查 LLM 请求（消息列表）
messages = [
    {"role": "user", "content": "搜索结果..."},
    {"role": "assistant", "content": "回复内容..."},
]
safe = gr.check_request(messages)  # True / False
```

### 三种脱敏策略

```python
from guardrail import Sanitizer
from guardrail.sanitizer import MatchInfo

sanitizer = Sanitizer()
matches = [MatchInfo("敏感词", 0, 3, "political_sensitive")]

# 替换为安全描述
sanitizer.sanitize("文本", strategy="replace", matches=matches)
# → "[POLITICALLY SENSITIVE CONTENT REMOVED]"

# 遮盖为 ***
sanitizer.sanitize("文本", strategy="mask", matches=matches)
# → "***"

# 删除整行
sanitizer.sanitize("干净行\n敏感行\n干净行", strategy="remove", matches=matches)
# → "干净行\n干净行"
```

### CLI 用法

```bash
# 扫描文本
guardrail scan --text "Check this IP: 10.0.0.1"

# 扫描文件
guardrail scan --file search_result.txt

# JSON 输出
guardrail scan --text "sensitive content" --json

# 脱敏（替换策略）
guardrail sanitize --text "sensitive data" --strategy replace

# 脱敏（遮盖策略）
guardrail sanitize --text "sensitive data" --strategy mask

# 脱敏（删除策略）
guardrail sanitize --text "sensitive data" --strategy remove
```

### 代理中间件

```python
from guardrail.proxy import GuardRailMiddleware

middleware = GuardRailMiddleware()

# 检查单条文本
safe, details = middleware.check("user input text")
if not safe:
    print(f"触发: {details['triggers']}")
    print(f"安全版本: {details['sanitized']}")

# 检查 LLM 消息列表
all_safe, per_msg = middleware.check_request(messages)

# 直接脱敏响应
safe_text = middleware.sanitize_response("response with sensitive data")
```

---

## 规则库

GuardRail 基于 YAML 规则文件，支持精确匹配和正则模式：

| 类别 | 说明 | 示例触发词 |
|------|------|-----------|
| `political_sensitive` | 政治敏感词 | tiananmen, falun gong... |
| `illegal_content` | 违法内容引用 | cocaine, ransomware... |
| `personal_info` | 个人隐私信息 | social security number... |
| `hacker_tools` | 黑客工具引用 | sqlmap, metasploit... |

| 正则模式 | 说明 |
|----------|------|
| `ip_address` | IP 地址 |
| `email` | 邮箱地址 |
| `phone_number` | 电话号码 |
| `credit_card` | 信用卡号 |
| `api_key` | API 密钥 |
| `jwt_token` | JWT Token |
| `url` | URL 链接 |

### 自定义规则

在 `guardrail/rules/` 目录下创建 YAML 文件即可扩展：

```yaml
# trigger_words.yml
my_category:
  - "敏感词1"
  - "敏感词2"
```

```yaml
# patterns.yml
custom_pattern:
  pattern: '\b\d{6}\b'  # 匹配6位数字
  description: '[REDACTED CUSTOM]'
```

---

## 架构

```
┌─────────────────────────────────────────────┐
│              你的 Agent / 应用               │
└────────────┬────────────────┬───────────────┘
             │                │
   ┌─────────▼──────┐  ┌─────▼──────────┐
   │  GuardRail CLI  │  │ GuardRail Lib  │
   │  (手动扫描)     │  │ (Python import)│
   └─────────┬──────┘  └─────┬──────────┘
             │                │
   ┌─────────▼────────────────▼──────────┐
   │         规则引擎                      │
   │  ┌──────────┐  ┌──────────────┐     │
   │  │ 精确匹配  │  │ 正则模式匹配  │     │
   │  └──────────┘  └──────────────┘     │
   └─────────────────────────────────────┘
             │
   ┌─────────▼──────────────────────────┐
   │         脱敏引擎                    │
   │  replace / mask / remove           │
   └────────────────────────────────────┘
```

---

## 贡献

欢迎贡献规则和改进！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/my-rule`)
3. 提交更改 (`git commit -m 'Add new rule category'`)
4. 推送到分支 (`git push origin feature/my-rule`)
5. 创建 Pull Request

### 规则贡献指南

- 在 `guardrail/rules/` 下添加 YAML 规则文件
- 每个类别至少 5 个触发词
- 正则模式必须附带测试用例
- 中文敏感词请参考国内 LLM API 审核标准

---

## 许可证

MIT License — 详见 [LICENSE](LICENSE)

---

## 致谢

GuardRail 从一个真实的 bug 中长出：

> PA 搜 GitHub「量化」→ 混入 funNLP 敏感词 → DeepSeek 400 → 诊断根因 → 设计护栏 → 开源

感谢所有用 LLM API 做 Agent 的开发者——你们都可能遇到这个问题。

---

**作者：** [zhangzhiwei610](https://gitee.com/zhangzhiwei610)
