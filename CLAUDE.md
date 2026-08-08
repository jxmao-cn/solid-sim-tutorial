# CLAUDE.md — solid-sim-tutorial

## 项目目标

物理仿真自主学习的复现仓库（fork 自 phys-sim-book/solid-sim-tutorial）。学习流程：读 `/home/steven/mjx/phys-sim-book` 的 mdBook 对应章节 → 在本仓库复现代码、提出设想并用代码验证 → 用 `PROGRESS.md` + `reports/` 向导师定期组会汇报。最终目标是为复现 `/home/steven/mjx/Elastogen`（优化式弹性动力学，local-global/投影动力学家族）打基础。

## 环境

- 所有仓库脚本（pygame/numpy/scipy）用 conda 环境 **solid-sim**：`conda run -n solid-sim python <script>`。系统 python / uv 不可用。
- 工具链脚本（`.claude/scripts/`、`tools/` 证据收集器）用系统 `/usr/bin/python3`，仅标准库，不依赖 conda。
- 10–14 章依赖 taichi/warp，不做无头自动化，证据用仓库已有 `results.gif` + readme。

## 教材映射表（组会报告直接引用）

| 仓库章节 | phys-sim-book 章节 | Elastogen 相关性 |
|---|---|---|
| 0_getting_started, 1_mass_spring | simulation-with-optimization（离散时空/优化时间积分/投影牛顿） | PDNet 局部-全局求解器、优化时间积分 |
| 2_dirichlet, 5_mov_dirichlet | boundary-treatments（Dirichlet/移动边界） | 边界条件与形变约束 |
| 3_contact, 4_friction | boundary-treatments（碰撞/摩擦） | neuralCollision |
| 6_inv_free | hyperelasticity（无翻转弹性） | NeuralMTL 超弹材料 |
| 7_self_contact, 8_self_friction | finite-element-method（2D 自接触） | 碰撞与接触 |
| 9_reduced_DOF | spatial-reductions（模态降维） | 子空间编码（AEtest, cage_U/S.pt） |
| 10_mpm_elasticity, 11_mpm_plastic | material-point-method（MPM） | 暂无直接对应 |
| 12_pbd_cloth, 13_pbd_mesh, 14_pbf | position-based-simulations（PBD/XPBD/PBF） | 投影动力学家族，与 PDNet 同源 |

## 工具链约定

- **`PROGRESS.md`**：SessionEnd hook（`.claude/settings.json` → `.claude/scripts/progress_session_end.py`）在每次 Claude 会话结束时自动追加一条中文进度条目。这是"自上次组会进度"的唯一事实来源。**勿手工编辑已有条目**；会话外的补记可直接 append 新条目。
- **`TOOLCHAIN.md`**：整套工具链的原理与使用说明（hook 自动记录、`/组会报告` 命令、证据收集器、无头截图、故障排查）。
- **`/组会报告`**（别名 `/group-report`）：一键生成双语组会报告到 `reports/组会报告_YYYY-MM-DD.md` 并更新 `reports/index.md`；不改 PROGRESS.md。
- **平板公式笔记**：本期未接入，约定 `formula-<date>.pdf` 放 `reports/formula/`，后续版本自动嵌入报告第 4 节。
- **报告语言**：中文正文 + 每节一段英文 summary（固定模板见 `reports/` 既有报告）。

## git 习惯

- 上游 readme 英文；个人学习注释/笔记用中文（如 `0_getting_started/newton.py`、`simulator1.5.py`）。
- 提交信息与 git log 是学习凭证的一部分，提交时描述要具体（如 commit 4608cae）。
- 工作树中常有未提交的学习文件（如 newton.py），按用户要求提交；模型 checkpoint 一律不提交。
