---
name: yuntu-media-research
description: 使用RedFox实时与优质数据、可用浏览器完成选题调研、博主分析和单条内容结构拆解，并生成可追溯、可录屏的独立HTML报告。适用于创作者问今天讲什么、近3天什么题有流量、分析某个博主、拆解高表现作品或准备自媒体研究演示时。
---

# 云途自媒体研究

把“今天讲什么、这个博主为什么有效、这条内容是怎样抓住人的”推进成可拍、可展示的调研结果，并在用户选题后生成有来源的短视频初稿。RedFoxHub广域库负责近3天实时发现，优质库负责账号基线与历史详情；优先使用宿主已连接的RedFox MCP，否则使用官方Python SDK。浏览器负责核对具体单条，评论只在页面自然可见且当前任务确有需要时顺手查看。

## 核心边界

1. 默认由Agent采集原始材料，不要求用户先整理链接、评论或表格。
2. RedFox调用前先检查 `REDFOX_API_KEY` 是否存在并估算请求数；不得打印、记录或提交密钥。
3. 只处理公开数据，不绕过登录、验证码、付费墙或平台限制。
4. 页面事实、API字段、计算、推断和假设分开；缺字段就写缺失。
5. 借鉴热门任务、结构和需求，不复制原句、人格、包装或未经验证的效果承诺。
6. 写初稿前必须已有来源清单、代表单条与选题依据，模型常识不能冒充近期热度。
7. 无法采集时保存失败与已尝试路径，不能把采集悄悄退回给用户后声称任务完成。
8. 本Skill服务于内容调研与视频演示，不以建立完备的社媒数据研究平台为目标。
9. 近3天热点判断必须优先调用广域/实时接口；优质库空结果不能写成“没有热度”。
10. 最终报告必须使用真实采集数据；示例、占位符和模型编造数据不得进入可录屏产物。
11. 单条作品先由浏览器核对；只有确实需要完整文案时才调用外部转写能力，不把FunASR源码、模型或依赖捆绑进Skill。
12. 单条任务必须区分系统Chrome复用、宿主独立浏览器和无浏览器三种会话；页面需要登录时由用户自行登录，不读取或保存密码、Cookie和Token。

## 默认任务参数

- `creator_niche`：创作者赛道
- `target_audience`：具体人群与任务
- `platforms`：默认1个平台，最多3个
- `time_window`：热点默认近3天；样本不足扩到7天并标记
- `goal`：涨粉、搜索流量、Skill领取、软件开源或知识解释
- `delivery_asset`：Skill、源码、模板、报告或文档
- `material_input_mode`：默认 `ai-collected`

首次个性化使用时，从用户级`creator-profile.json`读取长期稳定信息。参数优先级为：当前任务明确输入最高，其次是已保存档案，最后才使用Skill默认值。不要把单期热点、临时标题或一次性工具偏好写回长期档案。

除非缺失信息会显著改变研究方向，否则直接执行。不要要求用户先提供“20条资料”或“100条评论”。

## 工作流

### -1. 首次运行与自动引导

用户第一次调用、主动要求配置或发生认证/依赖错误时，读取`references/first-run.md`，运行`scripts/doctor.py --json`并按`next_action`逐步引导。首次初始化固定先建立创作者研究档案，再配置RedFox；不要让用户在聊天里粘贴API Key。

每次建立研究简报前读取`scripts/creator_profile.py`返回的用户级档案。个性化选题调研至少需要`creator_niche`、`target_audience`和`platforms`；若当前任务已经明确给出这三项，可以先执行并询问是否保存为长期默认。档案缺失不能被模型自行猜测。

用户要求使用示例、复制提示词或不知道怎么开始时，读取`references/prompt-library.md`，只推荐与当前任务匹配的模板。

### 0. 选择任务模式

- `topic-research`：浏览器寻找具体单条并核对页面，RedFox补批量作品和互动数据，输出可拍选题。
- `creator-analysis`：RedFox采集博主主页、近期作品和账号内相对表现，输出内容结构、代表作品和可借鉴方向；不要求评论。
- `content-structure-analysis`：读取一条确定作品的页面、详情或转写，拆解开头、推进顺序、证明方式、画面任务和可复用结构。
- `draft-from-research`：用户选中候选后，只根据当前任务的来源、报告和真实交付物生成可追溯短视频初稿；不得绕过研究直接写近期热点。

默认只选一个研究模式。需要演示完整链路时可以按`topic-research → creator-analysis → content-structure-analysis`依次运行，前一步的选中对象必须成为下一步输入。`draft-from-research`是研究后的下游动作，只有用户确认选题后才能运行。

随后读取`references/agent-workflows.md`，执行宿主能力检查并选择对应提示词。内部简报使用`assets/research-brief.md`，最终结果使用对应报告模板。

### 1. 建立简报

创建 `research-output/<task>/brief.json`，包含任务、受众、平台、时间窗、查询词、样本计划、预计调用数、预算边界和停止条件。记录`profile_source`，并把本次实际使用的非敏感档案字段保存为`profile_snapshot.json`，便于复现实验；不要复制无关私人说明。字段见 `references/output-contract.md`。

### 2. 发现RedFox能力并规划采集

先运行：

```bash
python3 scripts/redfox_mcp.py status
python3 scripts/redfox_catalog.py status
python3 scripts/redfox_catalog.py discover --platform douyin --capability search
```

宿主已配置`mcp__redfox__*`工具时直接读取当前工具目录。独立运行时可用`uvx redfox-mcp`连接官方stdio桥；启动器不可用则使用SDK目录，不因单一通道失败而停止。

调用前生成`request_plan.json`并估价：

```bash
python3 scripts/estimate_cost.py --plan assets/example-request-plan.json
```

`price_class`只从当前官方说明识别为`quality`、`realtime`或`unknown`。未知价格必须显示，不得用平均价填补。

没有密钥时停止API调用，并说明需要用户在RedFox控制台自行创建或配置。推荐运行 `python3 scripts/configure_key.py`，以隐藏输入方式写入Git忽略的本地 `.env`。不得代用户读取、显示或上传密钥。

抖音快速研究优先组合：

- 广域关键词作品搜索：找近3天具体任务与工具内容
- 每日/七日点赞飙升榜：发现超出常规搜索词的尾流
- 优质库账号作品与详情：建立账号内历史基线
- 广域作品详情与视频提文案：只对少量确定的高价值对标使用

三层调用顺序：

1. `realtime-wide`：近3天发现与增长判断。
2. `quality`：账号、历史作品和完整字段补充。
3. `browser-verified`：页面存在性、可见标题、章节、评论与播放内容抽查。

广域库无样本时才拆分组合词或扩到7天；每次回退都写入`fallback_log.jsonl`，不能悄悄改变时间范围。

当前RedFox能力、字段和成本边界见 `references/redfox.md`。核心任务与验收见`references/research-capabilities.md`。接口可能变化，运行前以官方文档为准。

### 3. 执行采集与保留原始响应

```bash
python3 scripts/redfox_collect.py collect --config assets/example-task.json \
  --out research-output/<task> --execute
```

原始JSON放入 `raw/redfox/`，标准化作品写入 `works.jsonl`，来源写入 `source_manifest.jsonl`。不要覆盖原始响应。

MCP或SDK通用调用示例：

```bash
python3 scripts/redfox_mcp.py call --tool douyin_search_ai_articles \
  --args '{"keyword":"Codex"}' --execute --out raw/redfox/mcp.json
python3 scripts/redfox_catalog.py call --operation sdk.douyin.search_ai_articles \
  --args '{"keyword":"Codex"}' --execute --out raw/redfox/sdk.json
python3 scripts/normalize.py --input raw/redfox/mcp.json --kind work \
  --platform douyin --out works.jsonl
```

关键词搜索会混入只碰巧包含单个词的内容。配置 `required_any_groups`，要求作品在每组中至少命中一个词；完整采集保存为 `works_collected.jsonl`，过滤后的研究样本保存为 `works.jsonl`，排除理由保存为 `relevance_exclusions.jsonl`。不得删除排除样本来伪装命中率。

### 4. 浏览器寻找与核对单条

先读取`references/browser-session.md`完成浏览器会话预检，记录`browser_channel`、`session_mode`、`login_required`和`verification_status`。能连接用户已登录的系统Chrome时，可以在用户授权的目标标签页中核对；不能复用登录时使用宿主独立会话，或明确标记`login-blocked`/`unverified`。不得把RedFox字段存在写成页面已经核对。

围绕当前任务寻找或抽查3至5条真实页面，保存可见标题、作者、发布时间、指标和页面URL。选题调研可以顺手查看页面中自然可见的评论，博主分析和内容结构拆解不以评论为前置条件。不得为了补齐字段额外接入评论API。

内容结构拆解需要完整文案时，读取`references/local-transcription.md`。先检测用户本机是否已有FunASR；缺少时征得同意后从官方渠道安装或拉取到Skill之外的隔离目录，再对用户有权处理的本地媒体转写。只有本地方案不可用或用户明确选择服务端转写时，才核价并确认是否调用RedFox视频提文案。

### 5. 识别尾流机会

区分：

- `direct-tailwind`：同一具体任务，用另一工具或面向另一人群实测
- `improved-rebuild`：审计已有Skill或流程，解决可证实缺陷
- `reverse-original`：从真实失败、Issue、付费商品或个人高频任务反向开发
- `knowledge-entry`：围绕明确对象完成听懂、判断或操作

推荐时至少说明依据来自批量互动、近期增长、浏览器单条、搜索问题或创作者真实任务中的哪一种；本Skill不要求为每条候选建立统计学需求证明。

### 6. 生成3条具体候选

每条必须说明：目标人群、观众任务、实拍什么、先展示什么结果、AI如何取得原料、对标链接、差异、交付钩子、证据与样本限制。禁止“让AI自动办公”这类无具体任务的标题。

将候选写入 `topic_cards.jsonl`，再运行：

```bash
python3 scripts/rank_topics.py research-output/<task>/topic_cards.jsonl \
  --out research-output/<task>/topic_ranking.csv
```

### 7. 生成可视化报告

Agent先按`references/html-report-contract.md`写入对应的`report.json`，再运行：

```bash
python3 scripts/validate_report.py report.json
python3 scripts/render_report.py --input report.json --output report.html
```

输出为单文件HTML，不依赖网络字体、CDN或本地服务，可直接双击打开。三种报告必须使用真实来源、明确采集层级、生成时间、样本限制与失败记录。

### 8. 用户确认后形成初稿

读取`references/draft-writing.md`与`assets/short-video-draft.md`，生成`selected_topic.md`、`draft.md`、`draft_source_map.json`和`audit.md`。初稿采用完成态前置、具体摩擦、原料自动取得、连续动作升级、逐段证明、人机边界和交付结算；这是一套任务型短教学候选结构，不强制用于所有内容。

近期事实、指标和第三方行为在`draft_source_map.json`中映射到`Sxxx`；个人实测、计算和推断分别映射到`Practice`、`Calculated`、`Inference`。口播正文不朗读来源标签。不得出现外部作者姓名、复制其原句或把相关性包装成因果。

生成后运行：

```bash
python3 scripts/validate_draft.py research-output/<task>
```

### 9. 验收

```bash
python3 scripts/validate_output.py research-output/<task>
```

验证失败时修复证据链，不删除校验字段。安全与发布承诺见 `references/evidence-and-safety.md`。

## 快速模式

用户说“给我3条明天能拍的”时，默认1个平台、近3天、2至4个查询词、每词1页，抽查3至5个对标，最终只返回3条候选。样本不足可以结束，但必须说明覆盖。

## 资源

- 首次运行：`references/first-run.md`
- 可复制提示词：`references/prompt-library.md`
- RedFox接入：`references/redfox.md`
- 核心任务验收：`references/research-capabilities.md`
- 通用Agent提示词：`references/agent-workflows.md`
- 浏览器与登录会话：`references/browser-session.md`
- 可选本地转写：`references/local-transcription.md`
- 输出字段：`references/output-contract.md`
- 证据与安全：`references/evidence-and-safety.md`
- 示例任务：`assets/example-task.json`
- 研究简报：`assets/research-brief.md`
- 选题报告：`assets/topic-research-report.md`
- 博主报告：`assets/creator-analysis-report.md`
- 内容结构报告：`assets/content-structure-analysis-report.md`
- HTML报告合同：`references/html-report-contract.md`
- HTML渲染：`scripts/render_report.py`
- 数据采集：`scripts/redfox_collect.py`
- MCP工具发现与调用：`scripts/redfox_mcp.py`
- SDK能力发现与调用：`scripts/redfox_catalog.py`
- 请求费用估算：`scripts/estimate_cost.py`
- 跨平台字段统一：`scripts/normalize.py`
- 相关性过滤：`scripts/filter_relevance.py`
- 密钥配置：`scripts/configure_key.py`
- 创作者档案：`scripts/configure_profile.py`
- 候选排序：`scripts/rank_topics.py`
- 输出校验：`scripts/validate_output.py`
- 初稿方法：`references/draft-writing.md`
- 初稿模板：`assets/short-video-draft.md`
- 初稿校验：`scripts/validate_draft.py`
