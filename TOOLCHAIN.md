# 学习进度工具链使用说明（TOOLCHAIN）

本仓库配套的一套"学习 → 进度记录 → 组会汇报"自动化工具链：**平时学习什么都不用做**，会话结束时 hook 自动把进度写进 `PROGRESS.md`；导师通知开组会时，一条命令生成中英双语报告到 `reports/`。

## 一、总体架构

```
平时学习（Claude 会话）
   │ 会话结束
   ▼
SessionEnd hook ──────► .claude/scripts/progress_session_end.py
   │                         │ ① 摘录 transcript 尾部消息
   │                         ▼
   │                    claude -p 子会话（六标签中文摘要）
   │                         │
   │                         ▼
   │                    PROGRESS.md 追加条目（去重 / 空会话跳过）
   │
开组会前：/组会报告（或 /group-report）
   │
   ├── tools/changes_since.py    git 提交 / 变更文件 / gif / obj 帧数证据
   ├── tools/headless_capture.py 无头运行 pygame demo 并截图（0–8 章）
   └── 生成 reports/组会报告_<日期>.md（七节双语模板）+ 更新 reports/index.md
```

## 二、组件与原理

### 1. SessionEnd hook → PROGRESS.md（自动记录）

- **触发**：每次 Claude 会话结束时，Claude Code 按 `.claude/settings.json` 中配置的 hook 执行 `.claude/scripts/progress_session_end.py`。
- **流程**：读 stdin 的 JSON payload（`session_id` / `transcript_path`）→ 提取 transcript 尾部 120 条消息（USER/ASSISTANT 行，Write/Edit 的文件路径、Bash 命令、tool_result 都是摘要依据）→ 交给 `claude -p` 子会话按固定提示词输出六标签摘要 → 规范化（补齐 `- ` 项目符号前缀、附 `git HEAD`）→ append 到 `PROGRESS.md`。
- **六标签格式**：`阅读内容 / 代码实现 / 验证/效果 / 想法/设想 / 下一步 / 英文摘要`。
- **关键设计**：
  - 防递归：子会话设置 `CLAUDE_PROGRESS_SKIP=1`，脚本开头检测到即退出（本版本 claude CLI 无 `--disable-hooks` 参数，已不用）。
  - 去重：`PROGRESS.md` 中已有该 session_id 前 8 位 → 跳过，重跑不重复。
  - 空会话启发式：无实质用户文本且无工具调用 → 跳过。
  - NONE 约定：子会话判断无实质学习内容（纯闲聊/纯规划）时只输出 `NONE`，脚本不写条目。
  - 静默失败：所有失败路径均 `exit 0`，**绝不阻塞会话退出**。
  - 运行环境：系统 `python3`（仅标准库），不依赖 conda。

### 2. /组会报告 命令（一键生成双语报告）

- 入口：`.claude/commands/组会报告.md`，别名 `/group-report`（英文提示）。
- 七步流程：① 定报告期（读 `reports/index.md` + `PROGRESS.md` 取最新日期，用户可用参数覆盖）→ ② 收集证据（`changes_since.py` + 最多一次无头截图 + 读 PROGRESS 条目与章节中文注释）→ ③ 问 2 个确认问题（报告期是否准确；平板公式笔记是否已整理）→ ④ 生成 `reports/组会报告_<日期>.md`（七节中英双语模板）→ ⑤ 更新 `reports/index.md` → ⑥ 收尾输出完成提示。
- 铁律：**绝不修改 PROGRESS.md**（hook 自动维护的真源）；gif/图片用相对路径；10–14 章（taichi/warp）不自动运行。

### 3. tools/changes_since.py（证据收集器）

- 用法：`/usr/bin/python3 tools/changes_since.py <起始日期 YYYY-MM-DD>`
- 输出四节 markdown 就绪证据：git 提交（含本地未推送提交）／变更与新增文件（含未跟踪）／效果证据（仓库全部 gif、各章 `output/*.obj` 帧数统计、USD 导出）／报告期内 PROGRESS.md 条目。

### 4. tools/headless_capture.py + tools/pygame_shim（无头截图）

- 原理：`SDL_VIDEODRIVER=dummy` 无头显示 + `pygame_shim` 在 `display.flip/update` 时自动保存 PNG（真实 pygame 被透明包装，demo 代码零改动）；demo 本体用 `conda run -n solid-sim` 运行。
- 用法：`/usr/bin/python3 tools/headless_capture.py <章节脚本> [--frames N] [--timeout S] [--out <目录>]`
- 行为：10–14 章（含 `10_mpm` / `11_mpm` / `12_pbd` / `13_pbd` / `14_pbf` 路径）自动 SKIP；demo 阻塞在键盘输入则超时被杀，已产出的截图保留；截图输出到 `<章节>/output/capture/`（已 gitignore）。

## 三、日常使用

1. **平时学习**：无需任何操作。会话结束 hook 自动把本次会话进度写进 `PROGRESS.md`（当前文件的 08-07 条目即由上一会话结束时的 hook 自动生成）。
2. **会话外补记**：直接 append 新条目到 `PROGRESS.md` 末尾；已有条目勿手工编辑。
3. **导师通知开组会**：在 Claude 提示符输入 `/组会报告`（或 `/group-report`），回答 2 个确认问题，报告即生成到 `reports/`。
4. **手动收集证据**：
   ```bash
   /usr/bin/python3 tools/changes_since.py 2026-08-06
   ```
5. **手动无头截图**：
   ```bash
   /usr/bin/python3 tools/headless_capture.py 0_getting_started/simulator1.py --frames 5 --timeout 15
   ```
6. **手动干跑 hook**（调试用）：
   ```bash
   echo '{"session_id":"dryrun-xxx","transcript_path":"<transcript.jsonl>","hook_event_name":"SessionEnd"}' \
     | python3 .claude/scripts/progress_session_end.py
   ```

## 四、注意事项

- `PROGRESS.md` 是"自上次组会以来进度"的唯一事实来源，由 hook 自动维护，**勿手工编辑已有条目**。
- 10–14 章（taichi/warp）不做无头自动化，证据用仓库已有 `results.gif` + readme。
- hook 与证据脚本用系统 `python3`（仅标准库）；仿真 demo 一律用 `conda run -n solid-sim`。
- `.claude/settings.json` 已持久化 `"model": "claude-haiku-4-5-20251001"` 作为项目默认模型（新会话自动生效，可用 `/model` 临时切换）。
- 截图目录 `<章节>/output/capture/` 已 gitignore，不会误提交。
- 报告模板、教材映射表、git 习惯见 `CLAUDE.md` 与 `reports/` 既有报告。

## 五、故障排查

| 现象 | 原因 | 处理 |
|---|---|---|
| PROGRESS.md 未写条目 | 空会话，或无实质学习内容（子会话输出 NONE） | 属正常；检查 transcript 是否有实质内容 |
| 同一会话条目重复 | — | 不会发生：session_id 前 8 位去重 |
| 截图 0 张 | demo 未调用 flip/update 或提前退出 | 检查 demo 主循环；必要时调大 `--timeout` |
| 子调用 `claude -p` 失败 | 模型不可用 / 超时 | 看 stderr 的 `[progress-hook]` 日志；失败不影响会话退出 |
| hook 不触发 | `.claude/settings.json` 被改动 / hook 未接线 | 确认 hooks.SessionEnd 配置存在，脚本路径为绝对路径 |
