#!/usr/bin/env python3
"""SessionEnd hook: 把每次 Claude 会话的摘要追加到 PROGRESS.md。

stdin 收到 hooks 的 JSON（session_id / transcript_path / hook_event_name ...），
提取 transcript 尾部摘录，调用 `claude -p` 子会话生成六标签中文条目，append 到
<repo>/PROGRESS.md。全部失败路径静默 exit 0，绝不阻塞会话退出。

仅用标准库，系统 python3 运行，不依赖 conda 环境。
"""

import json
import os
import re
import subprocess
import sys
import tempfile
import datetime

# ---------------------------------------------------------------- 配置
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PROGRESS_PATH = os.path.join(REPO_ROOT, "PROGRESS.md")
# 子调用摘要用模型；留空表示继承当前会话模型。成本控制靠 max_turns + NONE 约定。
SUMMARY_MODEL = ""  # 例如 "haiku-4-5-20251001" 或 ""(继承)
MAX_TURNS = 6
EXCERPT_MESSAGES = 120   # 提取 transcript 的消息条数（超出则全文等间隔采样）
MAX_MSG_CHARS = 1500     # 每条消息截断长度
MAX_EXCERPT_CHARS = 200_000

SUMMARY_PROMPT = """你是学习进度记录员。下面是某次 Claude Code 会话的 transcript 摘录（USER/ASSISTANT/TOOL 行，TOOL 行中 Write/Edit 的文件路径是重要证据）。请用中文按以下六个固定标签总结这次会话的学习/工作内容，格式严格为六行，不要任何其他文字：
- 阅读内容: ...
- 代码实现: ...
- 验证/效果: ...
- 想法/设想: ...
- 下一步: ...
- 英文摘要: (一句英文)
要求：只总结与 solid-sim-tutorial 物理仿真学习相关的实质内容（读 phys-sim-book、写/改代码、跑仿真、公式推导等）；TOOL 行里出现的文件路径要体现在对应标签里；若会话没有实质学习内容（纯闲聊、纯规划讨论未动手、与学习无关），只输出 NONE。"""


def log_err(msg):
    sys.stderr.write(f"[progress-hook] {msg}\n")


def read_stdin_json():
    try:
        raw = sys.stdin.read()
        return json.loads(raw) if raw.strip() else {}
    except Exception as e:
        log_err(f"stdin 解析失败: {e}")
        return {}


def message_plain_text(msg):
    """从 transcript 消息提取纯文本。content 可能是 str 或块列表。"""
    content = msg.get("message", {}).get("content", "")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if not isinstance(block, dict):
                continue
            if block.get("type") == "text":
                parts.append(block.get("text", ""))
            elif block.get("type") == "tool_use":
                name = block.get("name", "")
                inp = block.get("input", {}) or {}
                if name in ("Write", "Edit", "MultiEdit", "NotebookEdit"):
                    parts.append(f"[tool {name} path={inp.get('file_path', inp.get('notebook_path', '?'))}]")
                elif name == "Bash":
                    cmd = str(inp.get("command", ""))[:200]
                    parts.append(f"[tool Bash cmd={cmd}]")
                else:
                    parts.append(f"[tool {name}]")
            elif block.get("type") == "tool_result":
                out = block.get("content", "")
                if isinstance(out, str):
                    parts.append(f"[tool_result {out[:500]}]")
                elif isinstance(out, list):
                    text = " ".join(b.get("text", "") for b in out
                                    if isinstance(b, dict) and b.get("type") == "text")
                    parts.append(f"[tool_result {text[:500]}]")
        return "\n".join(parts)
    return ""


def session_has_work(transcript_path):
    """空会话启发式: 没有任何实质 user 文本且没有任何文件/命令工具调用 → 跳过。"""
    meaningful_user = 0
    has_tool = False
    try:
        with open(transcript_path, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                try:
                    rec = json.loads(line)
                except Exception:
                    continue
                if rec.get("type") == "user":
                    text = message_plain_text(rec)
                    text = text.strip()
                    if (len(text) > 40 and "system-reminder" not in text
                            and not text.startswith("<")):
                        meaningful_user += 1
                elif rec.get("type") == "assistant":
                    if re.search(r'"tool_use"', line):
                        has_tool = True
    except Exception as e:
        log_err(f"transcript 读取失败: {e}")
        return False
    return meaningful_user >= 1 or has_tool


def build_excerpt(transcript_path):
    """把 transcript 消息压缩成紧凑文本，供子会话摘要。超过上限时全文等间隔采样，保证头部与尾部内容都能进摘录。"""
    messages = []
    try:
        with open(transcript_path, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                try:
                    rec = json.loads(line)
                except Exception:
                    continue
                if rec.get("type") not in ("user", "assistant"):
                    continue
                text = message_plain_text(rec).strip()
                if not text:
                    continue
                kind = "USER" if rec.get("type") == "user" else "ASSISTANT"
                messages.append(f"{kind}: {text[:MAX_MSG_CHARS]}")
    except Exception as e:
        log_err(f"transcript 提取失败: {e}")
        return None
    # 全文等间隔采样（含首尾）：会话很长时只取尾部会丢掉开头内容
    if len(messages) > EXCERPT_MESSAGES:
        step = (len(messages) - 1) / (EXCERPT_MESSAGES - 1)
        messages = [messages[int(round(i * step))] for i in range(EXCERPT_MESSAGES)]
    excerpt = "\n\n".join(messages)
    return excerpt[:MAX_EXCERPT_CHARS]


def summarize(excerpt_path):
    """调用 claude -p 子会话摘要。失败返回 None。"""
    claude = os.environ.get("CLAUDE_BIN", "claude")
    # 注意: 本版本 claude CLI 无 --disable-hooks；防递归靠下面的
    # CLAUDE_PROGRESS_SKIP=1 环境变量守卫（子会话触发 SessionEnd 时脚本直接退出）。
    cmd = [claude, "-p", SUMMARY_PROMPT, "--output-format", "text",
           "--max-turns", str(MAX_TURNS),
           "--dangerously-skip-permissions"]
    if SUMMARY_MODEL:
        cmd += ["--model", SUMMARY_MODEL]
    env = dict(os.environ)
    env["CLAUDE_PROGRESS_SKIP"] = "1"  # 防子会话再触发本 hook
    try:
        with open(excerpt_path, "r", encoding="utf-8", errors="replace") as f:
            proc = subprocess.run(cmd, stdin=f, capture_output=True, text=True,
                                  timeout=300, env=env)
        out = (proc.stdout or "").strip()
        if proc.returncode != 0:
            log_err(f"claude -p 失败 rc={proc.returncode}: {(proc.stderr or '')[:300]}")
            return None
        return out
    except FileNotFoundError:
        log_err("找不到 claude 命令")
        return None
    except subprocess.TimeoutExpired:
        log_err("claude -p 超时")
        return None
    except Exception as e:
        log_err(f"子调用异常: {e}")
        return None


def git_head_short():
    try:
        out = subprocess.run(
            ["git", "-C", REPO_ROOT, "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, timeout=10)
        return out.stdout.strip() or ""
    except Exception:
        return ""


# 六标签行若缺项目符号前缀则补上（模型输出可能不带 "- "）
LABEL_RE = re.compile(r"^(阅读内容|代码实现|验证/效果|想法/设想|下一步|英文摘要):")


def append_entry(session_id, body):
    """规范化并追加一条 PROGRESS 条目。body 来自子会话输出。"""
    body = body.strip()
    if not body:
        return False
    lines = []
    for ln in body.splitlines():
        ln = ln.strip()
        if not ln:
            continue
        if not ln.startswith("- ") and LABEL_RE.match(ln):
            ln = "- " + ln
        lines.append(ln)
    header = f"## {datetime.date.today().isoformat()} — session {session_id[:8]}"
    entry = header + "\n" + "\n".join(lines).rstrip() + "\n"
    head = git_head_short()
    if head:
        entry += f"- git HEAD: {head}\n"
    entry += "\n"
    try:
        if not os.path.exists(PROGRESS_PATH):
            with open(PROGRESS_PATH, "w", encoding="utf-8") as f:
                f.write("# PROGRESS.md — 学习进度日志\n\n")
        with open(PROGRESS_PATH, "r", encoding="utf-8") as f:
            existing = f.read()
        if existing and not existing.endswith("\n"):
            existing += "\n"
        with open(PROGRESS_PATH, "w", encoding="utf-8") as f:
            f.write(existing + entry)
        return True
    except Exception as e:
        log_err(f"写入 PROGRESS.md 失败: {e}")
        return False


def main():
    payload = read_stdin_json()
    if os.environ.get("CLAUDE_PROGRESS_SKIP") == "1":
        return 0
    if payload.get("hook_event_name") != "SessionEnd":
        return 0
    session_id = payload.get("session_id") or ""
    transcript_path = payload.get("transcript_path") or ""
    if not session_id or not transcript_path or not os.path.isfile(transcript_path):
        return 0
    # 去重: 该会话已记录过（防重复触发）
    try:
        with open(PROGRESS_PATH, "r", encoding="utf-8") as f:
            if session_id[:8] in f.read():
                return 0
    except FileNotFoundError:
        pass
    except Exception:
        pass
    # 空会话跳过
    if not session_has_work(transcript_path):
        return 0
    # 提取摘录并摘要
    excerpt = build_excerpt(transcript_path)
    if not excerpt:
        return 0
    fd, tmp_path = tempfile.mkstemp(prefix="progress_excerpt_", suffix=".txt")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(excerpt)
        summary = summarize(tmp_path)
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
    if not summary or summary.strip().upper() == "NONE":
        return 0
    append_entry(session_id, summary)
    return 0


if __name__ == "__main__":
    sys.exit(main())
