"""pygame 透明包装: 无头 (SDL dummy) 运行时在 flip/update 时自动保存 PNG 截图。

用法: SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy \
      PYTHONPATH=<repo>/tools/pygame_shim:<repo> \
      PYGAME_CAPTURE_DIR=<输出目录> PYGAME_CAPTURE_EVERY=<每N帧存一张> \
      conda run -n solid-sim python <demo>.py

机制: 本模块先于真实 pygame 被 import，把真实 pygame 加载为 sys.modules["pygame"]
并包装其 display.flip / display.update。截图失败时静默降级，不影响 demo 运行。
"""

import os
import sys

_here = os.path.dirname(os.path.abspath(__file__))   # .../tools/pygame_shim/pygame
_shim_dir = os.path.dirname(_here)                    # .../tools/pygame_shim

# 从 sys.path 移除本 shim 目录，让 import 拿到真实 pygame
sys.path = [p for p in sys.path if os.path.abspath(p) != _shim_dir]

# 弹出本模块占用的 sys.modules 入口（本模块尚未初始化完成，直接丢弃）
sys.modules.pop("pygame", None)

import pygame as _real  # noqa: E402

# 真实 pygame 现在在 sys.modules["pygame"]；把我们的包装挂在真实模块上
_capture_dir = os.environ.get("PYGAME_CAPTURE_DIR", "capture")
_capture_every = max(1, int(os.environ.get("PYGAME_CAPTURE_EVERY", "10")))
_frame_count = [0]
_saved = [0]
_broken = [False]


def _maybe_save():
    if _broken[0]:
        return
    _frame_count[0] += 1
    if _frame_count[0] % _capture_every != 0:
        return
    try:
        surf = _real.display.get_surface()
        if surf is None:
            return
        os.makedirs(_capture_dir, exist_ok=True)
        _real.image.save(surf, os.path.join(_capture_dir,
                                            f"frame_{_saved[0]:04d}.png"))
        _saved[0] += 1
    except Exception as e:  # 截图失败不阻断 demo
        _broken[0] = True
        sys.stderr.write(f"[pygame_shim] 截图停用: {e}\n")


_orig_flip = _real.display.flip
_orig_update = _real.display.update


def _flip(*args, **kwargs):
    _maybe_save()
    return _orig_flip(*args, **kwargs)


def _update(*args, **kwargs):
    _maybe_save()
    return _orig_update(*args, **kwargs)


_real.display.flip = _flip
_real.display.update = _update

# 导出与真实 pygame 完全一致（属性访问走 __getattr__）
__version__ = getattr(_real, "__version__", "")


def __getattr__(name):
    return getattr(_real, name)


def __dir__():
    return dir(_real)
