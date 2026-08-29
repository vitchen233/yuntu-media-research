# 云途自媒体研究 Skill

当前版本：`1.1.1`

用RedFoxHub实时/广域库、优质库和可用浏览器自动采集公开内容，生成选题调研、账号分析和单条内容结构拆解三种独立HTML报告，并在选题确认后生成有来源的短视频初稿。

## 解决什么

很多“AI做自媒体”流程仍要求用户先准备链接或CSV。本Skill从赛道、博主或具体作品出发：RedFox广域库负责近3天实时发现，优质库负责账号和历史作品，Agent浏览器负责核对具体单条，最终形成可离线打开、适合录屏的研究结果。

## 核心输出

- 原始RedFox响应与公开来源清单
- 作品、账号、互动指标和浏览器抽查记录
- 关键词相关性过滤与被排除样本
- 对标结构与不可复制边界
- 带实拍任务、结果画面、对标链接和交付钩子的候选选题
- 选中题证据包与可追溯初稿
- 失败、缺失字段与事实待核验清单
- 三种云途视觉HTML报告和一个本地启动首页

## 支持的智能体

同一份Skill可安装到Codex、WorkBuddy、Claude Code和其他支持`SKILL.md`的Agent。研究任务、真实性边界和HTML报告一致；宿主只负责提供不同的浏览器、终端或MCP能力。

- Codex：`~/.codex/skills/yuntu-media-research/`
- WorkBuddy 国内版：`~/.workbuddy/skills/yuntu-media-research/`
- WorkBuddy 海外版：`~/.workbuddy-ai/skills/yuntu-media-research/`
- Claude Code：`~/.claude/skills/yuntu-media-research/`
- 其他宿主：使用`install.py --target "<skills目录>"`

## 一键安装

下载或克隆仓库后，在仓库根目录运行其中一条：

```bash
# Codex
python3 install.py --host codex --with-deps

# WorkBuddy 国内版
python3 install.py --host workbuddy --with-deps

# WorkBuddy 海外版
python3 install.py --host workbuddy-ai --with-deps

# Claude Code
python3 install.py --host claude --with-deps
```

Windows中可将`python3`换成`py`。已安装旧版时追加`--force`覆盖。安装后重启或刷新Agent。

## 手动安装

```bash
pip install -r requirements.txt
```

需要独立使用官方RedFox MCP桥时，再安装可选启动器：

```bash
pip install -r requirements-mcp.txt
```

将`skills/yuntu-media-research/`整个复制到上面对应的技能目录，保证最终路径为`<skills目录>/yuntu-media-research/SKILL.md`，然后安装依赖：

```bash
python3 -m pip install "redfox-python-sdk>=0.3.0,<1"
```

## 配置RedFox

环境变量统一命名为`REDFOX_API_KEY`。在[RedFoxHub控制台](https://redfox.hk/dashboard/keys)自行创建API Key，然后在仓库或已安装的Skill目录运行：

```bash
# 在仓库根目录
python3 skills/yuntu-media-research/scripts/configure_key.py

# 已进入安装后的Skill目录
python3 scripts/configure_key.py
```

输入过程不会显示字符。Key默认保存到用户级配置目录，所有工作区都能找到：

- macOS / Linux：`~/.config/yuntu-media-research/.env`
- Windows：`%APPDATA%\yuntu-media-research\.env`

也可以只对当前终端设置：

- macOS：双击 `setup-key.command`
- Windows：双击 `setup-key.bat`

```bash
# macOS / Linux
export REDFOX_API_KEY="YOUR_API_KEY"

# Windows PowerShell
$env:REDFOX_API_KEY="YOUR_API_KEY"
```

不要把Key发到聊天、写入示例、输出、截图或GitHub。公开视频里只展示 `status` 返回的 `true/false`，不要展示 `.env` 内容或RedFox密钥页。

## 第一次运行

安装后，可以直接对Agent说：

```text
第一次使用 yuntu-media-research，请开始初始化。
```

Agent会执行两步初始化：先通过简短问卷建立创作者研究档案，再配置RedFox。API Key只在本机隐藏输入，不会要求你粘贴到聊天里。也可以自己运行检查：

```bash
# 在仓库根目录
python3 skills/yuntu-media-research/scripts/doctor.py --json

# 已进入安装后的Skill目录
python3 scripts/doctor.py --json
```

### 建立创作者研究档案

技术配置只决定“能不能采集”，创作者档案决定“替谁研究、哪些题适合”。运行：

```bash
# 在仓库根目录
python3 skills/yuntu-media-research/scripts/configure_profile.py

# 已进入安装后的Skill目录
python3 scripts/configure_profile.py
```

脚本会询问你的身份、赛道、平台、目标受众、受众问题、内容目标、优先工具、交付物和边界。最低必填项是赛道、目标受众和平台。默认保存到：

- macOS / Linux：`~/.config/yuntu-media-research/creator-profile.json`
- Windows：`%APPDATA%\yuntu-media-research\creator-profile.json`

也可以修改`skills/yuntu-media-research/assets/creator-profile.example.json`后导入：

```bash
python3 skills/yuntu-media-research/scripts/configure_profile.py \
  --input skills/yuntu-media-research/assets/creator-profile.example.json
```

研究参数优先级为：本次任务明确输入 > 已保存档案 > Skill默认值。档案不会写入公开仓库；单期热点和临时标题也不会自动污染长期信息。

### 可选本地视频转写

需要拆解一条作品的完整文案时，Skill会先用浏览器核对页面，再检测本机是否已有[FunASR](https://github.com/modelscope/FunASR)。本仓库不捆绑FunASR源码、Python依赖、模型权重或媒体下载器；缺少时，Agent必须先征得同意，再从官方渠道安装或拉取到Skill之外的隔离环境。只有本地方案不可用时，才会核价并询问是否调用RedFox付费转写。

可以直接对Agent说：

```text
请拆解这条公开视频。先用浏览器核对页面；需要完整文案时检测本机FunASR，缺少时先征得我同意，再从官方渠道安装到Skill之外的隔离环境。只有本地方案不可用时，才询问我是否调用RedFox付费转写。
```

具体检测、macOS / Linux与Windows安装路径、调用命令和产物清单见`skills/yuntu-media-research/references/local-transcription.md`。

需要查看内置提示词时，对Agent说：

```text
请打开 yuntu-media-research 的提示词库，给我最适合当前任务的一条。
```

完整模板位于`skills/yuntu-media-research/references/prompt-library.md`，包含首次配置、近3天选题、博主分析、单条拆解、三报告演示和跨宿主对比。

研究完成并选中题目后，可以继续说：

```text
调用 yuntu-media-research，运行 draft-from-research。请根据刚才的真实研究结果生成短视频初稿、来源映射和事实审计。
```

初稿不会绕过研究直接编造近期事实，也不会复制对标作者的原句、人格或未经验证的效果承诺。

### 命令行自检

```bash
python3 skills/yuntu-media-research/scripts/redfox_mcp.py status
python3 skills/yuntu-media-research/scripts/redfox_catalog.py status
python3 skills/yuntu-media-research/scripts/redfox_catalog.py discover \
  --platform douyin --capability search
python3 skills/yuntu-media-research/scripts/redfox_collect.py status
python3 skills/yuntu-media-research/scripts/redfox_collect.py plan \
  --config skills/yuntu-media-research/assets/example-task.json
python3 skills/yuntu-media-research/scripts/redfox_collect.py collect \
  --config skills/yuntu-media-research/assets/example-task.json \
  --out research-output/codex-for-creators \
  --execute
```

`plan`不会产生付费调用；只有带 `--execute` 的 `collect` 才会请求RedFox。

当前v1.0采用MCP/SDK双通道：MCP适合宿主Agent原生工具调用，SDK提供广域实时搜索和更完整的平台操作目录。是否使用Codex或WorkBuddy不改变研究合同。热点默认先使用`search_works_wide`，账号基线再使用优质库。调用前使用`estimate_cost.py`估价，调用后用`normalize.py`统一作品和账号字段。无法从官方说明识别价格时会保留`unknown`，不会猜测。

关键词搜索可能混入同名或偶然命中内容。`required_any_groups`要求每组至少命中一个词，原始采集与过滤结果会同时保留，便于审计。

## Agent使用示例

```text
调用 yuntu-media-research。
我是做AI实用教学的，面向刚开始用AI的内容创作者。
使用RedFox研究近3天抖音正在增长的具体任务，由AI自动取得原料。
给我3条明天能实拍的候选，每条附对标链接、结果画面、Skill钩子和样本限制。
我确认一条后，再输出对标报告和带来源初稿。
```

也可以直接运行三种模式：

```text
调用 yuntu-media-research，运行 creator-analysis。
分析这个公开博主主页，使用RedFox采集近期作品并建立账号内基线。
找出高表现作品、可复用内容结构和3个适合我借鉴的方向。
```

内置提示词还包含“一次生成三报告”与“Codex / WorkBuddy同任务独立对比”。

Skill不绑定某个Agent。宿主能读取`SKILL.md`并具备RedFox MCP、Python脚本或浏览器能力中的相应部分即可运行；不同宿主的工具名称可以不同，任务模式、简报和报告结构保持一致。尚未真机验收的宿主不宣称官方兼容。

三种模式分别为`topic-research`、`creator-analysis`和`content-structure-analysis`。Agent完成研究后写入`report.json`：

```bash
python3 skills/yuntu-media-research/scripts/validate_report.py report.json
python3 skills/yuntu-media-research/scripts/render_report.py \
  --input report.json --output report.html
```

HTML不依赖CDN或本地服务器，可以直接双击打开。多份报告可以使用`render_report_index.py`生成统一入口。

## 测试

```bash
python3 -m unittest discover -s tests -v
```

发布前还需要运行宿主Agent提供的Skill结构校验，并在macOS与Windows分别完成真实任务验收。

## 平台与状态

Skill本体与Python脚本按macOS和Windows双平台设计，但浏览器控制取决于宿主Agent。`v1.0.0`已在macOS真实验收RedFox MCP工具发现、广域近3天搜索、优质库账号基线、视频转写、费用模型、统一字段和三种HTML报告。安装器与用户级配置路径已使用临时目录模拟macOS、Windows和多宿主安装；Windows真机与各宿主结果仍以社区反馈持续验证。本项目不宣称已带来流量或增长结果。

## 设计原则

本项目围绕云途真实内容工作重构：RedFox优先、原料由AI自动采集、近期尾流与长期需求分开、每条候选必须能实拍、每个判断都能回指来源，并在用户确认后才进入对标与初稿。

RedFoxHub及其SDK是独立第三方服务，本项目与RedFoxHub无隶属或官方合作关系。接口费用、可用性和条款以RedFoxHub官方信息为准。

## 许可证

MIT。RedFox第三方服务说明见 `THIRD_PARTY_NOTICES.md`。
