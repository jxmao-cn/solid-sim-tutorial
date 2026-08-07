#!/usr/bin/env python3
"""无头运行 pygame demo 并自动截图（作为报告"验证/效果"证据）。

用法: python3 tools/headless_capture.py <script.py> [--frames N] [--timeout S] [--out <dir>]

- 通过 pygame_shim 在 SDL dummy 驱动下每 N 帧保存一张 PNG。
- 10–14 章 (taichi/warp) 不可无头运行，直接打印 SKIP。
- demo 若阻塞在键盘输入则超时被杀（证据口径: 无头可跑 + 出图）。
仅用标准库；demo 本体用 conda run -n solid-sim 运行。
"""

import argparse
import os
import shutil
import subprocess
import sys
import time

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHIM_DIR = os.path.join(REPO_ROOT, "tools", "pygame_shim")
SKIP_PATTERNS = ("10_mpm", "11_mpm", "12_pbd", "13_pbd", "14_pbf")


def count_pngs(out_dir):
    if not os.path.isdir(out_dir):
        return 0
    return sum(1 for fn in os.listdir(out_dir) if fn.endswith(".png"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("script", help="要运行的 pygame demo 脚本（相对仓库根或绝对路径）")
    ap.add_argument("--frames", type=int, default=10, help="每 N 帧截一张 (默认 10)")
    ap.add_argument("--timeout", type=int, default=30, help="超时秒数 (默认 30)")
    ap.add_argument("--out", default=None, help="截图输出目录 (默认 <章节>/output/capture)")
    args = ap.parse_args()

    script = args.script
    if not os.path.isabs(script):
        script = os.path.join(REPO_ROOT, script)
    script = os.path.abspath(script)
    if not os.path.isfile(script):
        print(f"SKIP: 脚本不存在 {script}")
        return 0

    if any(p in script for p in SKIP_PATTERNS):
        print(f"SKIP: {script} 依赖 taichi/warp，无法无头运行；"
              f"证据用仓库已有 results.gif + readme")
        return 0

    chapter = os.path.basename(os.path.dirname(script))
    out_dir = args.out or os.path.join(REPO_ROOT, chapter, "output", "capture")
    os.makedirs(out_dir, exist_ok=True)

    env = dict(os.environ)
    pythonpath = [SHIM_DIR, REPO_ROOT]
    if env.get("PYTHONPATH"):
        pythonpath += env["PYTHONPATH"].split(os.pathsep)
    env.update({
        "SDL_VIDEODRIVER": "dummy",
        "SDL_AUDIODRIVER": "dummy",
        "PYTHONPATH": os.pathsep.join(pythonpath),
        "PYGAME_CAPTURE_DIR": out_dir,
        "PYGAME_CAPTURE_EVERY": str(max(1, args.frames)),
    })

    if not shutil.which("conda"):
        print("SKIP: 找不到 conda，无法用 solid-sim 环境运行")
        return 0

    cmd = ["conda", "run", "-n", "solid-sim", "python", script]
    t0 = time.time()
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True,
                              timeout=args.timeout, env=env, cwd=REPO_ROOT)
        rc, timed_out = proc.returncode, False
    except subprocess.TimeoutExpired as e:
        rc, timed_out = None, True
        # 尽力拿已产出的输出
        print("(demo 超时被杀，输出尾部如下)")
        for tail in (e.stdout or "", e.stderr or ""):
            for ln in str(tail).strip().splitlines()[-5:]:
                print(f"  | {ln}")
    except FileNotFoundError:
        print("SKIP: conda run 启动失败（solid-sim 环境不存在?）")
        return 0

    dur = time.time() - t0
    npng = count_pngs(out_dir)
    print(f"### 无头运行结果: {os.path.basename(script)}")
    print(f"- 状态: {'超时(被主动终止)' if timed_out else '正常退出'} "
          f"exit_code={rc if rc is not None else 'n/a'}")
    print(f"- 时长: {dur:.1f}s | 截图: {npng} 张 | 目录: {out_dir}")
    if npng == 0:
        print("- 提示: 0 张截图，demo 可能未调用 display.flip/update 或提前退出")
    return 0


if __name__ == "__main__":
    sys.exit(main())
