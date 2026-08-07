# PROGRESS.md — 学习进度日志

本文件由 SessionEnd hook（`.claude/scripts/progress_session_end.py`）在每次 Claude 会话结束时自动追加，是"自上次组会以来进度"的唯一事实来源。格式：每个会话一个 `## <日期> — session <id前8位>` 条目 + 六个固定标签（阅读内容 / 代码实现 / 验证效果 / 想法设想 / 下一步 / git HEAD）。**勿手工编辑已有条目**。

## 2026-08-06 (基线) — session 4608cae (初始学习)
- 会话ID: 4608cae-initial
- 阅读内容: phys-sim-book Simulation with Optimization（离散时空、时间积分、优化框架、投影牛顿 2D mass-spring case study）；0_getting_started 教程
- 代码实现: 0_getting_started/newton.py（通用牛顿求解器 newton(f,x,jac)，Demo A 标量切线可视化、Demo B 后向欧拉非线性硬化弹簧，中文注释笔记）；simulator1.5.py（时变质量矩阵 m(t) 演示）；阅读 simulator1.py（显式辛欧拉悬挂弹簧）
- 验证/效果: 本地运行观察（pygame 窗口、牛顿收敛过程条）；git HEAD 4608cae
- 想法/设想: newton.py 的 newton() 设计为标量/向量通用、支持解析/数值雅可比，拟封装为 backward_euler 子模块供多维仿真复用
- 下一步: 在 newton.py 基础上实现多维后向欧拉子模块（残差 M(q - q_n - h v_n) - h^2 f(q) = 0，雅可比 M - h^2 ∂f/∂q，直接复用 newton 求解循环）
- git HEAD: 4608cae

## 2026-08-07 — session d9e99afc
- 阅读内容: 通读 0_getting_started/ 下既有教程代码（readme.md、simulator0.py、simulator1.py、simulator1.5.py、simulator2.py）作为编写参考；查证 solid-sim 环境（numpy 2.2.6、scipy 1.15.3、pygame 2.6.1）中 scipy 的牛顿法实现（optimize.newton/fsolve/root/root_scalar/newton_krylov，后者已从 sparse.linalg 迁至 optimize 命名空间）。
- 代码实现: 在用户骨架（func + newton(f,x)）基础上完成 0_getting_started/newton.py（约 440 行）：通用牛顿求解内核 newton(f, x, jac=None, tol, max_iter)，支持标量/向量、可选解析雅可比（缺省中心差分），返回 (root, history)；Demo A 可视化求解 func(x)=x²+3x-12（切线/迭代/根）；Demo B 用牛顿法实现非线性硬化弹簧的后向欧拉（残差 s−s_n−hv_n−h²a(s)=0，雅可比 1+h²(k+3cs²)/m，即多维 M−h²∂f/∂q 的标量版），并实时演示每步牛顿迭代；同步更新 0_getting_started/readme.md 及记忆文件（solid-sim-tutorial-env.md、backward-euler-next-step.md、MEMORY.md）。
- 验证/效果: conda run -n solid-sim 下：标量/有限差分/二维向量三种情形结果正确，残差路径 8.0→2.56→9.7e-2→1.7e-4→4.8e-10→0 呈典型二次收敛；两个 Demo 无头运行 8 秒无异常；scipy 交叉验证 200 步隐式欧拉稳定收敛到平衡点 s*=0.09217（h=0.1 时显式欧拉发散、隐式无条件稳定）；过程中修复 3 个 bug（标量变 0 维数组、解析雅可比返回 1 维、jacobian 传参顺序）。
- 想法/设想: scipy 的 fsolve/newton_krylov 不作为替代、而是手写牛顿法的"参考答案"用于交叉验证同一残差方程（手写可用解析雅可比 M−h²K，更本质更快）；newton.py 的求解内核设计为可复用模块，后续后向欧拉直接 from newton import newton。
- 下一步: 基于 newton() 内核实现后向欧拉子模块（backward Euler），用于 0_getting_started 的固体仿真演示。
- 英文摘要: Completed a reusable Newton solver module with two visualization demos (including a nonlinear-spring backward Euler), cross-validated against scipy, paving the way for a backward Euler submodule.
- git HEAD: 4608cae

