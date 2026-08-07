#!/usr/bin/env python3
"""证据收集器: 输出自 <date> 以来仓库变更的 markdown 就绪证据块。

用法: python3 tools/changes_since.py <since_date> [--repo <path>]
输出章节: git 提交 / 变更文件 / 效果证据(gif, obj 计数, USD) / PROGRESS.md 条目。
仅用标准库。
"""

import argparse
import os
import re
import subprocess
import sys
import datetime

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def sh(cmd, cwd=None):
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=60,
                             cwd=cwd or REPO_ROOT)
        return out.stdout.strip()
    except Exception as e:
        return f"(error: {e})"


def collect_git(date_str, repo):
    print("## git 提交 (since %s)" % date_str)
    log = sh(["git", "log", f"--since={date_str}",
              '--format=%h %ad %s', "--date=short"])
    print(log if log else "(无)")
    local = sh(["git", "log", "--oneline", "origin/main..HEAD"])
    print("\n本地提交 (origin/main..HEAD):")
    print(local if local else "(无)")
    print(f"\ngit HEAD: {sh(['git', 'rev-parse', '--short', 'HEAD'])}")


def collect_files(date_str, repo):
    print("\n## 变更/新增文件 (since %s)" % date_str)
    names = sh(["git", "log", f"--since={date_str}", "--name-only",
                '--format=', "--date=short"])
    names = [n for n in names.splitlines() if n.strip()]
    status = sh(["git", "status", "--short"])
    untracked = [l for l in status.splitlines() if l.startswith("??")]
    changed = [l for l in status.splitlines() if not l.startswith("??")]
    seen = set()
    if names:
        print("git log 命中的文件:")
        for n in sorted(set(names)):
            print(f"- {n}")
            seen.add(n)
    if untracked:
        print("\n未跟踪文件:")
        for l in untracked:
            print(f"- {l[3:]}")
    if changed:
        print("\n工作树已修改 (未提交):")
        for l in changed:
            print(f"- {l}")


def collect_evidence(repo):
    print("\n## 效果证据")
    print("### gif 动画")
    gifs = []
    for root, dirs, files in os.walk(repo):
        dirs[:] = [d for d in dirs if d not in (".git", "__pycache__", ".claude")]
        for fn in files:
            if fn.endswith(".gif"):
                gifs.append(os.path.relpath(os.path.join(root, fn), repo))
    print("\n".join(f"- {g}" for g in sorted(gifs)) if gifs else "(无)")
    print("\n### 各章 output/ obj 帧数")
    total = 0
    for entry in sorted(os.listdir(repo)):
        odir = os.path.join(repo, entry, "output")
        if os.path.isdir(odir):
            count = sum(1 for fn in os.listdir(odir) if fn.endswith(".obj"))
            print(f"- {entry}/output: {count} obj")
            total += count
    print(f"合计: {total} 帧")
    print("\n### USD 导出")
    usd = []
    for root, dirs, files in os.walk(repo):
        dirs[:] = [d for d in dirs if d not in (".git", "__pycache__", ".claude")]
        for fn in files:
            if fn.endswith((".usd", ".usda", ".usdc")):
                usd.append(os.path.relpath(os.path.join(root, fn), repo))
    print("\n".join(f"- {u}" for u in usd) if usd else "(无)")


def collect_progress(date_str, repo):
    print("\n## PROGRESS.md 条目 (since %s)" % date_str)
    path = os.path.join(repo, "PROGRESS.md")
    if not os.path.exists(path):
        print("(PROGRESS.md 不存在)")
        return
    with open(path, encoding="utf-8") as f:
        content = f.read()
    sections = re.split(r"(?m)^## ", content)
    found = False
    for sec in sections[1:]:
        m = re.match(r"(\d{4}-\d{2}-\d{2})", sec.strip())
        if m and m.group(1) >= date_str:
            print("## " + sec.rstrip())
            found = True
    if not found:
        print("(无)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("since", help="起始日期 YYYY-MM-DD")
    ap.add_argument("--repo", default=REPO_ROOT)
    args = ap.parse_args()
    print(f"# 学习证据 (since {args.since}, 今天 {datetime.date.today()})")
    collect_git(args.since, args.repo)
    collect_files(args.since, args.repo)
    collect_evidence(args.repo)
    collect_progress(args.since, args.repo)


if __name__ == "__main__":
    sys.exit(main())
