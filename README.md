# 云途自媒体研究 Skill

当前版本：`1.0.0-dev`

用RedFoxHub和可用浏览器自动采集近期公开内容，再生成带来源的尾流选题、对标分析和可追溯初稿。

## 解决什么

很多“AI做自媒体”流程仍要求用户先准备链接或CSV。本Skill从赛道、博主或热点任务出发：RedFox负责批量作品、账号和榜单数据，Agent浏览器负责寻找并核对具体单条，最终形成可演示的选题、博主或热点调研结果。

## 核心输出

- 原始RedFox响应与公开来源清单
- 作品、账号、互动指标和浏览器抽查记录
- 关键词相关性过滤与被排除样本
- 对标结构与不可复制边界
- 带实拍任务、结果画面、对标链接和交付钩子的候选选题
- 选中题证据包与可追溯初稿
- 失败、缺失字段与事实待核验清单

## 安装

```bash
pip install -r requirements.txt
```

需要独立使用官方RedFox MCP桥时，再安装可选启动器：

```bash
pip install -r requirements-mcp.txt
```

将 `skills/yuntu-media-research/` 复制或链接到支持 `SKILL.md` 的Agent技能目录。不同客户端的技能目录与启用方式可能不同，以客户端当前文档为准。

## 配置RedFox

环境变量统一命名为 `REDFOX_API_KEY`。在 [RedFoxHub控制台](https://redfox.hk/dashboard/keys) 自行创建API Key，然后在仓库根目录运行：

```bash
python3 skills/yuntu-media-research/scripts/configure_key.py
```

输入过程不会显示字符。Key会保存到本机 `.env`，该文件已被Git忽略。也可以只对当前终端设置：

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

当前v1.0采用MCP/SDK双通道：MCP适合宿主Agent原生工具调用，SDK提供更广的平台操作目录。调用前使用`estimate_cost.py`估价，调用后用`normalize.py`统一作品和账号字段。无法从官方说明识别价格时会保留`unknown`，不会猜测。

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

Skill不绑定某个Agent。宿主能读取`SKILL.md`并具备RedFox MCP、Python脚本或浏览器能力中的相应部分即可运行；不同宿主的工具名称可以不同，任务模式、简报和报告结构保持一致。尚未真机验收的宿主不宣称官方兼容。

## 测试

```bash
python3 -m unittest discover -s tests -v
```

发布前还需要运行宿主Agent提供的Skill结构校验，并在macOS与Windows分别完成真实任务验收。

## 平台与状态

Skill本体与Python脚本按macOS和Windows双平台设计，但浏览器控制取决于宿主Agent。`v1.0.0`正在重构：目前已在macOS验收RedFox MCP工具发现、MCP实调用、SDK动态目录、抖音采集、费用模型和统一字段；M2研究层、M3选题层、M4初稿层与Windows真机仍未完成，因此暂不宣称正式可用或已带来增长结果。

## 设计原则

本项目围绕云途真实内容工作重构：RedFox优先、原料由AI自动采集、近期尾流与长期需求分开、每条候选必须能实拍、每个判断都能回指来源，并在用户确认后才进入对标与初稿。

RedFoxHub及其SDK是独立第三方服务，本项目与RedFoxHub无隶属或官方合作关系。接口费用、可用性和条款以RedFoxHub官方信息为准。

## 许可证

MIT。RedFox第三方服务说明见 `THIRD_PARTY_NOTICES.md`。
