# Mass-Spring Solid Simulation

import math
import numpy as np  # for vector data structure and computations
import pygame       # for visualization
import square_mesh_plus  # for generating a triangular mesh
sqrt3 = 3**0.5

# simulation setup
side_length = 1             # side length of the triangle
n_seg = 4                  # number of springs per side of the triangle
m = 1000                    # mass of each particle
[x, e] = square_mesh_plus.generate(side_length, n_seg)   # array of particle positions and springs
x0 = x.copy()               # 保存初始位置，供"重新演示"时恢复

v = np.array([[0.0, 0.0]] * len(x))     # velocity array of particles ###
g = np.array([0.0, -10.0])  # gravitational acceleration
a1 = np.array([-5.0*sqrt3, 5.0])
a2 = np.array([5.0*sqrt3, 5.0])
spring_rest_len = []        # rest length array of the springs ###
for i in range(0, len(e)):  # calculate the rest length of each spring
    spring_vec = x[e[i][0]] - x[e[i][1]]    # the vector connecting two ends of spring i
    spring_rest_len.append(math.sqrt(spring_vec[0] * spring_vec[0] + spring_vec[1] * spring_vec[1]))
spring_stiffness = 1e6      # stiffness of the spring
h = 0.01                    # time step size in seconds

# visualization/rendering setup
pygame.init()
render_FPS = 100                    # number of frames to render per second
resolution = np.array([900, 900])   # visualization window size in pixels
offset = resolution / 2             # offset between window coordinates and simulated coordinates
scale = 200                         # scale between window coordinates and simulated coordinates
def screen_projection(x):           # convert simulated coordinates to window coordinates
    return [offset[0] + scale * x[0], resolution[1] - (offset[1] + scale * x[1])]
screen = pygame.display.set_mode(resolution)    # initialize visualizer

# ---- 加速度可视化与交互调整（HUD，位于窗口左侧）----
px_per_unit = 18        # 画箭头时每单位加速度对应的像素数
hud_anchor = np.array([250, 300])   # 三个加速度箭头共用的起点
accel = {'a1': a1, 'a2': a2, 'g': g}    # 名字 -> 加速度数组（通过 [:] 原地修改以保持引用一致）
accel_color = {'a1': (200, 40, 40), 'a2': (40, 90, 220), 'g': (40, 170, 70)}
font = pygame.font.SysFont('Arial', 22)
small_font = pygame.font.SysFont('Arial', 18)
selected = None     # 当前被选中的加速度名（'a1' / 'a2'），None 表示没有选中
dragging = False    # 是否正在拖拽箭头

def draw_arrow(color, p0, p1, width=3):     # 画一条带箭头的线段
    pygame.draw.line(screen, color, p0, p1, width)
    ang = math.atan2(p1[1] - p0[1], p1[0] - p0[0])
    for da in (2.5, -2.5):                  # 箭头两翼
        pygame.draw.line(screen, color, p1,
                         (p1[0] + 12 * math.cos(ang + da), p1[1] + 12 * math.sin(ang + da)), width)

def accel_delta(a):     # 加速度（物理坐标，y 向上）-> 屏幕上箭头的偏移（y 向下）
    return np.array([a[0], -a[1]]) * px_per_unit

def dist_to_segment(p, a, b):               # 点 p 到线段 ab 的距离（命中检测用）
    ab = b - a
    t = np.dot(p - a, ab) / np.dot(ab, ab) if np.dot(ab, ab) > 0 else 0.0
    t = min(max(t, 0.0), 1.0)
    q = a + t * ab
    return math.hypot(p[0] - q[0], p[1] - q[1])

# ---- 预设模式（点击右侧按钮或按 1 / 2 / 3 直接应用并重新演示）----
presets = [
    {'name': '1 Balance',    'a1': np.array([-5.0 * sqrt3, 5.0]),  'a2': np.array([5.0 * sqrt3, 5.0])},
    {'name': '2 Mild shake', 'a1': np.array([-9.0, 5.0]),          'a2': np.array([7.0, 5.0])},
    {'name': '3 Fast',       'a1': np.array([-5.0 * sqrt3, 12.0]), 'a2': np.array([5.0 * sqrt3, 12.0])},
]
for i, b in enumerate(presets):
    b['rect'] = pygame.Rect(755, 100 + i * 48, 130, 38)

def apply_preset(b):        # 应用预设加速度，并从初始状态重新演示
    global time_step, selected
    accel['a1'][:] = b['a1']
    accel['a2'][:] = b['a2']
    x[:] = x0[:]            # 恢复初始位置
    v[:] = 0                # 速度清零
    time_step = 0           # 模拟时钟归零
    selected = None         # 取消箭头选中

time_step = 0   # the number of the current time step
running = True  # flag indicating whether the simulation is still running
while running:
    # run until the user asks to quit
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # 先检查右侧的预设模式按钮
            hit_preset = None
            for b in presets:
                if b['rect'].collidepoint(event.pos):
                    hit_preset = b
                    break
            if hit_preset is not None:
                apply_preset(hit_preset)
                continue
            # 否则点选最近的 a1 / a2 箭头：优先看头部（25 像素内），其次看箭身（12 像素内），都取最近的
            cand = []
            for name in ('a1', 'a2'):
                p1 = hud_anchor + accel_delta(accel[name])
                cand.append((name,
                             math.hypot(event.pos[0] - p1[0], event.pos[1] - p1[1]),
                             dist_to_segment(event.pos, hud_anchor, p1)))
            if min(c[1] for c in cand) < 25:
                selected = min(cand, key=lambda c: c[1])[0]
            elif min(c[2] for c in cand) < 12:
                selected = min(cand, key=lambda c: c[2])[0]
            else:
                selected = None
            dragging = selected is not None
        elif event.type == pygame.MOUSEMOTION and dragging:
            # 拖拽时让箭头跟随鼠标：方向与大小由鼠标相对公共起点的位置决定（注意 y 轴翻转）
            p = (np.array(event.pos) - hud_anchor) / px_per_unit
            accel[selected][:] = [p[0], -p[1]]
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            dragging = False
        elif event.type == pygame.KEYDOWN and event.key in (pygame.K_1, pygame.K_2, pygame.K_3):
            apply_preset(presets[event.key - pygame.K_1])   # 快捷键应用预设
        elif event.type == pygame.KEYDOWN and event.key in (pygame.K_r, pygame.K_SPACE):
            # 用当前的 a1 / a2 重新演示整个网格的运动
            x[:] = x0[:]    # 恢复初始位置
            v[:] = 0        # 速度清零
            time_step = 0   # 模拟时钟归零

    # update the frame to display according to render_FPS
    if time_step % int(math.ceil((1.0 / render_FPS) / h)) == 0:
        # fill the background with white color, display simulation time at the top,
        # draw each spring segment, and render each particle as a circle:
        screen.fill((255, 255, 255))
        pygame.display.set_caption('Current time: ' + f'{time_step * h: .2f}s')
        for i in range(0, len(e)):  ###
            pygame.draw.aaline(screen, (0, 0, 255), screen_projection(x[e[i][0]]), screen_projection(x[e[i][1]]))
        for i in range(0, len(x)):  ###
            pygame.draw.circle(screen, (0, 0, 255), screen_projection(x[i]), 0.02 * scale)
        # 绘制 g、a1、a2 三个加速度箭头（共用同一个起点；被选中的箭头加粗并画上高亮圈）
        for name in ('g', 'a1', 'a2'):
            p0 = hud_anchor
            p1 = p0 + accel_delta(accel[name])
            draw_arrow(accel_color[name], p0, p1, width=4 if name == selected else 3)
            pygame.draw.circle(screen, (80, 80, 80), p0, 4)     # 箭头锚点
            if name == selected:
                pygame.draw.circle(screen, (255, 180, 0), p1, 9, 2)   # 选中高亮圈
            label = small_font.render(f'{name} = ({accel[name][0]:.1f}, {accel[name][1]:.1f})',
                                      True, accel_color[name])
            w, _ = label.get_size()
            if p1[0] < p0[0]:   # 箭头指向左 → 标签放头部右侧，避免压到网格
                screen.blit(label, (int(p1[0]) + 10, int(p1[1]) - 8))
            else:               # 否则放头部左侧
                screen.blit(label, (int(p1[0]) - w - 10, int(p1[1]) - 8))
        # 预设模式按钮（点击直接应用并重新演示，鼠标悬停时高亮）
        for b in presets:
            rect = b['rect']
            hover = rect.collidepoint(pygame.mouse.get_pos())
            pygame.draw.rect(screen, (210, 230, 245) if hover else (235, 235, 235), rect, border_radius=8)
            pygame.draw.rect(screen, (110, 110, 110), rect, 2, border_radius=8)
            label = small_font.render(b['name'], True, (50, 50, 50))
            screen.blit(label, label.get_rect(center=rect.center))
        # 操作提示
        hint1 = font.render('Presets: click the buttons on the right, or press 1 / 2 / 3', True, (60, 60, 60))
        hint2 = font.render('Drag an arrowhead to adjust a1 / a2     R / Space: reset & replay', True, (60, 60, 60))
        screen.blit(hint1, (10, 8))
        screen.blit(hint2, (10, 34))
        pygame.display.flip()   # flip the display
        pygame.time.wait(int(1000.0 / render_FPS))  # wait to render the next frame

    # step forward the simulation by updating particle velocity and position ###
    for i in range(0, len(e)):
        # calculate elasticity force of spring i:
        spring_vec = x[e[i][0]] - x[e[i][1]]
        spring_cur_len = math.sqrt(spring_vec[0] * spring_vec[0] + spring_vec[1] * spring_vec[1])
        spring_displacement = spring_cur_len - spring_rest_len[i]
        spring_force = -spring_stiffness * spring_displacement * (spring_vec / spring_cur_len)
        # update the velocity of the two ends of spring i
        v[e[i][0]] += h * (g + a1 + a2 + spring_force / m)
        v[e[i][1]] += h * (g + a1 + a2 - spring_force / m)
    # fix the three corners of the triangle by setting velocity to 0:
    v[-1] = v[0] = v[n_seg] = np.array([0, 0])
    # update the position of each particle:
    for i in range(0, len(x)):
        x[i] += h * v[i]

    time_step += 1  # update time step counter
