# Newton's Method 牛顿法 —— 非线性方程求解, 后向欧拉时间积分的基石
# ======================================================================
# 本文件包含三个部分:
#
#   1) 通用牛顿法求解器: newton() / numerical_jacobian()
#      —— 这是后续「后向欧拉 (implicit Euler)」时间积分模块的求解内核,
#        届时直接 `from newton import newton` 复用即可。
#
#   2) Demo A (默认): 标量方程 func(x) = x^2 + 3x - 12 的牛顿法切线演示
#      —— 直观展示「切线与 x 轴的交点就是下一次猜测」以及二次收敛。
#
#   3) Demo B: 非线性(硬化)弹簧 + 后向欧拉时间积分
#      —— 每个时间步都要解一个非线性方程, 用的正是牛顿法。
#        后向欧拉对位置 q 的隐式方程为 (M 是质量矩阵, f 是内力):
#            g(q) = M (q - q_n - h v_n) - h^2 f(q) = 0
#        Demo B 是它在 1D 上的标量版本 (M = m); 以后做多维固体仿真时,
#        只需把 residual/jacobian 换成向量版本, 求解循环不需要改动。
#
# 运行方式 (在 solid-sim conda 环境中):
#     python newton.py           # Demo A: 标量根求解 + 切线可视化
#     python newton.py spring    # Demo B: 后向欧拉弹簧仿真
#
# 键盘操作:
#     Demo A: SPACE 立即进入下一步迭代,  R 重新开始
#     Demo B: SPACE 暂停/继续,  T 暂停时单步执行一次牛顿迭代,  R 重新开始
#     两者:   关闭窗口退出
#
# 环境里 scipy 也有现成的牛顿法 (scipy.optimize.newton/fsolve/newton_krylov),
# 可作为结果验证的参考; 这里手写是为了理解算法本身, 以及能用解析雅可比。

import math
import sys

import numpy as np  # 数值计算 (向量与矩阵)
import pygame       # 可视化


def func(x):
    return x**2 + 3*x - 12   # 演示方程: 根为 x* = (-3 + sqrt(57)) / 2 ≈ 2.2749


# ----------------------------------------------------------------------
# 1) 通用牛顿法求解器 (后续后向欧拉模块直接复用)
# ----------------------------------------------------------------------

def numerical_jacobian(f, x, eps=1e-6):
    """用中心差分近似 f 在 x 处的雅可比矩阵 (f 的输入输出同维).

    当解析雅可比难以手推时使用 (比如任意复杂的内力模型).
    """
    x = np.asarray(x, dtype=float)
    J = np.zeros((x.size, x.size))
    for i in range(x.size):
        x_plus, x_minus = x.copy(), x.copy()
        x_plus[i] += eps
        x_minus[i] -= eps
        J[:, i] = (f(x_plus) - f(x_minus)) / (2.0 * eps)
    return J


def newton(f, x, jac=None, tol=1e-10, max_iter=50):
    """用牛顿法求解非线性方程组 f(x) = 0.

    迭代公式: x_{k+1} = x_k - J(x_k)^-1 f(x_k), 其中 J 是 f 的雅可比.

    参数:
        f    : 残差函数, 输入/输出均为同维向量
        x    : 初始猜测
        jac  : 雅可比函数, 输入 x 输出矩阵; 传 None 则用有限差分近似
        tol  : 收敛容差 (||f(x)|| < tol 时停止)
        max_iter : 最大迭代次数

    返回 (root, history):
        root    : 收敛后的解向量
        history : 每次迭代的 (x_k, ||f(x_k)||), 供可视化和调试使用
    """
    x = np.asarray(x, dtype=float)
    scalar_input = x.ndim == 0          # 标量输入内部按 1 元数组处理
    x = np.atleast_1d(x)
    history = []
    for _ in range(max_iter + 1):
        residual = np.atleast_1d(np.asarray(f(x), dtype=float))
        history.append((float(x[0]) if scalar_input else x.copy(),
                        float(np.linalg.norm(residual))))
        if np.linalg.norm(residual) < tol:
            break
        J = jac(x) if jac is not None else numerical_jacobian(f, x)
        x = x + np.linalg.solve(np.atleast_2d(J), -residual)   # 解线性方程组 J dx = -f(x)
    root = float(x[0]) if scalar_input else x
    return root, history


def clip(v, lo, hi):
    return max(lo, min(hi, v))


# ----------------------------------------------------------------------
# 2) Demo A: 标量方程 func(x) = x^2 + 3x - 12 的牛顿法演示
#    几何意义: 在 (x_k, f(x_k)) 处作切线, 切线与 x 轴的交点就是 x_{k+1}
# ----------------------------------------------------------------------

def demo_scalar():
    def df(x):                          # 演示方程的导数 f'(x) = 2x + 3
        return 2.0 * x + 3.0
    root_exact = (-3.0 + math.sqrt(57.0)) / 2.0

    # 一次求解获得全部迭代历史, 再逐帧重放, 便于观察切线迭代过程
    root, history = newton(func, 1.0, jac=df)   # 初始猜测 x0 = 1.0

    # ---- 可视化 ----
    pygame.init()
    screen = pygame.display.set_mode((900, 900))
    pygame.display.set_caption("Newton's Method: f(x) = x^2 + 3x - 12")
    font = pygame.font.Font(None, 20)
    font_big = pygame.font.Font(None, 24)
    clock = pygame.time.Clock()

    def text(s, x, y, color=(0, 0, 0), font=font):
        screen.blit(font.render(s, True, color), (x, y))

    plot_rect = (60, 50, 660, 760)   # (left, top, width, height) 函数图像区域
    wx_range = (-1.0, 4.0)           # 世界坐标范围
    wy_range = (-17.0, 18.0)

    def proj(wx, wy):                # 世界坐标 -> 屏幕坐标
        left, top, w, h = plot_rect
        sx = left + (wx - wx_range[0]) / (wx_range[1] - wx_range[0]) * w
        sy = top + (wy_range[1] - wy) / (wy_range[1] - wy_range[0]) * h
        return int(sx), int(sy)

    def draw_state(k):
        x_k, _ = history[k]   # 当前残差在右侧数值表中随表展示

        # 背景与函数曲线 y = f(x)
        screen.fill((255, 255, 255))
        xs = np.linspace(wx_range[0], wx_range[1], 300)
        pygame.draw.lines(screen, (0, 0, 255), False,
                          [proj(x, func(x)) for x in xs], 2)

        # 坐标轴与刻度
        pygame.draw.line(screen, (170, 170, 170),
                         proj(wx_range[0], 0), proj(wx_range[1], 0), 1)
        pygame.draw.line(screen, (170, 170, 170),
                         proj(0, wy_range[0]), proj(0, wy_range[1]), 1)
        for xt in range(-1, 5):
            pygame.draw.line(screen, (200, 200, 200), proj(xt, -0.35), proj(xt, 0.35), 1)
            text(str(xt), proj(xt, 0)[0] - 5, proj(xt, 0)[1] + 6, (120, 120, 120))
        for yt in range(-15, 16, 5):
            pygame.draw.line(screen, (200, 200, 200), proj(-0.05, yt), proj(0.05, yt), 1)
            text(str(yt), proj(0, yt)[0] - 30, proj(0, yt)[1] - 8, (120, 120, 120))

        # 根的位置 (绿色竖线) 与标题
        pygame.draw.line(screen, (0, 180, 0),
                         proj(root_exact, wy_range[0]), proj(root_exact, wy_range[1]), 1)
        text('f(x) = x^2 + 3x - 12    root: x* = (-3+sqrt(57))/2', 70, 8, (0, 0, 0), font_big)

        # 之前迭代的轨迹点 (灰色小圆, 展示收敛路径)
        for x_j, _ in history[:k]:
            pygame.draw.circle(screen, (150, 150, 150), proj(x_j, func(x_j)), 4)
            pygame.draw.circle(screen, (150, 150, 150), proj(x_j, 0), 3)

        # 当前迭代: 切点/切线 (红色) 与 x 轴上的新猜测 (蓝色)
        pygame.draw.line(screen, (150, 150, 150), proj(x_k, 0), proj(x_k, func(x_k)), 1)
        half_w = 1.8   # 切线的绘制半宽
        tx0, tx1 = clip(x_k - half_w, wx_range[0], wx_range[1]), \
                   clip(x_k + half_w, wx_range[0], wx_range[1])
        pygame.draw.line(screen, (255, 0, 0),   # 切线 y = f(x_k) + f'(x_k)(x - x_k)
                         proj(tx0, clip(func(x_k) + df(x_k) * (tx0 - x_k), wy_range[0], wy_range[1])),
                         proj(tx1, clip(func(x_k) + df(x_k) * (tx1 - x_k), wy_range[0], wy_range[1])), 2)
        pygame.draw.circle(screen, (255, 0, 0), proj(x_k, func(x_k)), 6)
        pygame.draw.circle(screen, (0, 0, 255), proj(x_k, 0), 5)

        pygame.draw.rect(screen, (0, 0, 0), plot_rect, 1)   # 图像区域边框

        # ---- 右侧: 迭代数值表 ----
        tx = 740
        text('iterations', tx, 60, (0, 0, 0), font_big)
        for j, (x_j, res_j) in enumerate(history):
            color = (255, 0, 0) if j == k else (60, 60, 60)
            text(f'k={j}   x={x_j: .6f}', tx, 100 + 44 * j, color)
            text(f'      |f|={res_j: .2e}', tx, 118 + 44 * j, color)
        y0 = 100 + 44 * len(history)
        text(f'converged: x = {root: .6f}', tx, y0, (0, 150, 0))
        text(f'exact: x* = {root_exact: .6f}', tx, y0 + 22, (0, 150, 0))
        text('red: tangent at (x_k, f(x_k))', tx, y0 + 58)
        text('blue: next guess on x-axis', tx, y0 + 80)
        text('green: root x*', tx, y0 + 102)
        text('SPACE: next    R: restart', tx, y0 + 130, (120, 120, 120))

    # ---- 重放循环: 每次迭代展示约 1.25 秒, SPACE 跳过 ----
    k = 0                 # 当前展示到第几次迭代
    frame_count = 0
    frames_per_iter = 75  # 60 FPS 下约 1.25 秒
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and k < len(history) - 1:
                    k += 1
                    frame_count = 0
                elif event.key == pygame.K_r:
                    k = 0
                    frame_count = 0
        if k < len(history) - 1 and frame_count >= frames_per_iter:
            k += 1
            frame_count = 0
        draw_state(k)
        pygame.display.flip()
        frame_count += 1
        clock.tick(60)
    pygame.quit()


# ----------------------------------------------------------------------
# 3) Demo B: 后向欧拉 (implicit Euler) + 牛顿法
#    非线性(硬化)弹簧悬挂质点: 每个时间步的隐式方程都用牛顿法求解
# ----------------------------------------------------------------------

def demo_implicit_euler():
    # ---- 物理参数 (一维: s = 弹簧伸长量, 向下为正) ----
    m = 1.0        # 质点质量
    k = 100.0      # 弹簧线性刚度
    c = 1000.0     # 非线性硬化系数: F(s) = -k s - c s^3
    g = 10.0       # 重力加速度 (向下为正)
    h = 0.1        # 时间步长
    rest_len = 0.8 # 弹簧原长 (仅用于绘制)
    anchor = np.array([0.0, 2.0])   # 悬挂点位置

    def spring_force(s):            # 弹簧力 (指向悬挂点, 即向上)
        return -k * s - c * s ** 3

    def accel(s):                   # 加速度 a(s) = g + F(s) / m
        return g + spring_force(s) / m

    # ---- 后向欧拉 ----
    # v_{n+1} = v_n + h a(s_{n+1})
    # s_{n+1} = s_n + h v_{n+1}
    # 消去 v_{n+1} 得到关于 s_{n+1} 的非线性方程, 即牛顿法要解的残差:
    #     g(s) = s - s_n - h v_n - h^2 a(s) = 0
    # 其雅可比 (一维即标量导数):
    #     g'(s) = 1 - h^2 a'(s) = 1 + h^2 (k + 3 c s^2) / m
    # 对应一般固体仿真的情形: 残差 = M (q - q_n - h v_n) - h^2 f(q),
    # 雅可比 = M - h^2 df/dq (df/dq 即弹性刚度矩阵)。
    # 同样的 h 下显式欧拉早已发散 (稳定性要求 h < 2/omega, 这里 omega~30),
    # 隐式欧拉无条件稳定 —— 代价是每步要解一次非线性方程, 即牛顿法。
    def residual(s_, s_n, v_n):
        return s_ - s_n - h * v_n - h * h * accel(s_)

    def jacobian(s_):   # g'(s) 只依赖 s, 与 s_n / v_n 无关
        return 1.0 + h * h * (k + 3.0 * c * s_ * s_) / m

    # ---- 可视化 ----
    pygame.init()
    screen = pygame.display.set_mode((900, 900))
    pygame.display.set_caption("Implicit (Backward) Euler + Newton: nonlinear spring")
    font = pygame.font.Font(None, 18)
    font_small = pygame.font.Font(None, 14)
    font_big = pygame.font.Font(None, 22)
    clock = pygame.time.Clock()

    def text(s, x, y, color=(0, 0, 0), font=font):
        screen.blit(font.render(s, True, color), (x, y))

    # 左侧主面板: 弹簧动画 (世界坐标 x 范围与 y 范围)
    panel_rect = (20, 40, 600, 840)
    wx_range = (-1.5, 1.5)
    wy_range = (-1.5, 2.8)

    def proj(wx, wy):                # 世界坐标 -> 屏幕坐标
        left, top, w, h = panel_rect
        sx = left + (wx - wx_range[0]) / (wx_range[1] - wx_range[0]) * w
        sy = top + (wy_range[1] - wy) / (wy_range[1] - wy_range[0]) * h
        return int(sx), int(sy)

    # 右侧面板几何: (a) 残差曲线 / (b) 残差收敛条形图 / (c) 状态与操作
    res_rect = (660, 60, 220, 300)
    bar_rect = (660, 390, 220, 230)
    info_rect = (660, 650, 220, 220)

    # ---- 仿真状态 (闭包 draw_frame 在每帧读取这些变量的当前值) ----
    s, v = 0.5, 0.0          # 初始状态: 弹簧被拉长 0.5, 静止
    time, step = 0.0, 0
    history = []             # 当前时间步的牛顿迭代历史: [(s_k, |g(s_k)|), ...]
    replay_idx = 0           # 正在展示 history 中的第几项
    guess = 0.0              # 当前步的初始猜测
    frames_held = 0
    frames_per_iter = 3      # 每次牛顿迭代展示的帧数 (60 FPS 下约 0.05 秒)
    paused = False
    solving = True           # True: 需要为当前步求解; False: 正在重放牛顿迭代
    step_once = False        # T 键: 暂停时单步执行一次牛顿迭代

    def res_k_now():         # 当前展示迭代的残差
        if history and replay_idx < len(history):
            return history[replay_idx][1]
        return 0.0

    def draw_frame():
        # ---- 左侧主面板: 弹簧与质点 ----
        screen.fill((255, 255, 255))
        text('backward Euler: solve g(s) = s - s_n - h v_n - h^2 a(s) = 0', 32, 8, (0, 0, 0), font_small)
        text('each time step -> one Newton solve (right panel)', 32, 26, (0, 0, 0), font_small)
        pygame.draw.line(screen, (0, 0, 0), proj(-0.4, anchor[1]), proj(0.4, anchor[1]), 1)  # 悬挂杆
        pygame.draw.circle(screen, (0, 0, 0), proj(anchor[0], anchor[1]), 4)
        particle = np.array([0.0, anchor[1] - rest_len - s])   # 质点位置: 原长下方 s
        pygame.draw.aaline(screen, (0, 0, 255), proj(anchor[0], anchor[1]), proj(*particle))  # 弹簧
        pygame.draw.circle(screen, (0, 0, 255), proj(*particle), 18)
        pygame.draw.rect(screen, (0, 0, 0), panel_rect, 1)

        # ---- 右侧 (a): 当前时间步的残差曲线 g(s) 与牛顿切线 ----
        left, top, w, h = res_rect
        pygame.draw.rect(screen, (245, 245, 245), res_rect)
        text('residual g(s) of this step', left + 6, top + 4, (0, 0, 0), font_big)
        if history:
            s_lo, s_hi = guess - 0.4, guess + 0.4          # s 轴窗口
            samples = np.linspace(s_lo, s_hi, 80)
            ys = np.array([residual(s_, s, v) for s_ in samples])
            y_lo, y_hi = min(0.0, ys.min()), max(0.0, ys.max())
            span = y_hi - y_lo
            if span < 1e-9:
                span = 1.0
            y_lo, y_hi = y_lo - 0.15 * span, y_hi + 0.15 * span

            def rproj(s_, y_):                              # 残差面板内的投影
                sx = left + (s_ - s_lo) / (s_hi - s_lo) * w
                sy = top + 26 + (y_hi - y_) / (y_hi - y_lo) * (h - 34)
                return int(sx), int(sy)

            # 零点线 (解 g(s)=0 的点就在这条线上)
            pygame.draw.line(screen, (0, 150, 0), rproj(s_lo, 0), rproj(s_hi, 0), 1)
            # 残差曲线
            pygame.draw.lines(screen, (0, 0, 255), False,
                              [rproj(s_, y_) for s_, y_ in zip(samples, ys)], 2)
            # 初始猜测标记 (灰色方块)
            pygame.draw.rect(screen, (120, 120, 120),
                             (*rproj(guess, residual(guess, s, v)), 6, 6))
            # 逐项重放牛顿迭代: 迭代点 + 当前项的切线
            for j in range(replay_idx + 1):
                s_j, res_j = history[j]
                color = (255, 0, 0) if j == replay_idx else (150, 150, 150)
                if j == replay_idx:
                    slope = jacobian(s_j)                   # 切线 y = g + g'(s - s_j)
                    pygame.draw.line(screen, (255, 0, 0),
                                     rproj(s_j - 0.3, clip(res_j - 0.3 * slope, y_lo, y_hi)),
                                     rproj(s_j + 0.3, clip(res_j + 0.3 * slope, y_lo, y_hi)), 2)
                pygame.draw.circle(screen, color, rproj(s_j, res_j), 4)
            if not solving:
                text(f'Newton iter {replay_idx}/{len(history) - 1},  |g| = {res_k_now(): .2e}',
                     left + 6, top + h - 20)
        else:
            text('computing next step ...', left + 6, top + 60, (120, 120, 120))
        pygame.draw.rect(screen, (0, 0, 0), res_rect, 1)

        # ---- 右侧 (b): 每次迭代的残差 (对数刻度条形图) ----
        left, top, w, h = bar_rect
        pygame.draw.rect(screen, (245, 245, 245), bar_rect)
        text('|g(s_k)| per iteration (log10)', left + 6, top + 4, (0, 0, 0), font_big)
        if history:
            res_list = [res_j for _, res_j in history]
            res_max = max(res_list)
            floor = max(1e-13, res_max * 1e-8)   # 纵轴下界, 避免 log 到 0
            n = len(history)
            bw = (w - 12 - (n - 1) * 6) / n      # 每根柱子的宽度
            for j, (_, res_j) in enumerate(history):
                bx = left + 6 + j * (bw + 6)
                t = (math.log10(res_j) - math.log10(floor)) / \
                    (math.log10(res_max) - math.log10(floor))
                bh = max(0.0, min(1.0, t)) * (h - 70)
                by = top + h - 26 - bh
                color = (255, 0, 0) if j == replay_idx else (0, 0, 255)
                pygame.draw.rect(screen, color, (bx, by, bw, bh))
                text(f'{res_j:.0e}', bx, by - 14, (0, 0, 0), font_small)
        pygame.draw.rect(screen, (0, 0, 0), bar_rect, 1)

        # ---- 右侧 (c): 状态数值与操作说明 ----
        left, top, w, h = info_rect
        pygame.draw.rect(screen, (245, 245, 245), info_rect)
        text(f'step = {step}    t = {time: .2f}s', left + 6, top + 6, (0, 0, 0), font_big)
        text(f's (extension) = {s: .4f}', left + 6, top + 34)
        text(f'v = {v: .4f}', left + 6, top + 56)
        text(f'spring force F = {spring_force(s): .3f}', left + 6, top + 78)
        text(f'gravity force mg = {m * g: .1f}', left + 6, top + 100)
        if history and replay_idx < len(history):
            text(f'Newton iter {replay_idx}/{len(history) - 1}', left + 6, top + 128)
            text(f'residual |g| = {history[replay_idx][1]: .2e}', left + 6, top + 150)
        text('SPACE: pause/resume', left + 6, top + 184)
        text('T: single Newton step', left + 6, top + 204)
        text('R: reset', left + 6, top + 224)
        pygame.draw.rect(screen, (0, 0, 0), info_rect, 1)

    # ---- 主循环: 每帧最多执行一次牛顿迭代 (或一次时间步的求解+重放) ----
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    paused = not paused
                elif event.key == pygame.K_t and paused:   # 暂停时单步执行
                    paused = False
                    step_once = True
                elif event.key == pygame.K_r:
                    s, v, time, step = 0.5, 0.0, 0.0, 0
                    history, replay_idx, frames_held = [], 0, 0
                    solving, paused = True, False

        if not paused:
            if solving:
                # 求解当前时间步: 初始猜测取显式欧拉预测 s_n + h v_n
                guess = s + h * v
                s_new, history = newton(
                    lambda s_: residual(s_, s, v),   # 残差依赖当前步的 s_n, v_n
                    guess,                           # 初始猜测
                    jac=jacobian)                    # 雅可比与 s_n, v_n 无关, 直接传
                replay_idx = 0
                frames_held = 0
                solving = False
            else:
                # 重放牛顿迭代 (逐帧展示, 相当于把一次求解放慢)
                frames_held += 1
                if frames_held >= frames_per_iter:
                    frames_held = 0
                    replay_idx += 1
                    if replay_idx >= len(history):
                        # 收敛, 应用后向欧拉时间步: v_{n+1} = (s_{n+1} - s_n) / h
                        s, v = s_new, (s_new - s) / h
                        time += h
                        step += 1
                        solving = True
                        history = []

        if step_once:
            paused = True
            step_once = False

        draw_frame()
        pygame.display.flip()
        clock.tick(60)
    pygame.quit()


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'spring':
        demo_implicit_euler()
    else:
        demo_scalar()
