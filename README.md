# 云途自媒体研究 Skill

当前版本：`1.0.0-dev`

用RedFoxHub和可用浏览器自动采集近期公开内容，再生成带来源的尾流选题、对标分析和可追溯初稿。

## 解决什么

很多“AI做自媒体”流程仍要求用户先准备链接、评论或CSV。本Skill默认从赛道、人群和任务出发，用RedFox获得结构化作品数据，再由Agent抽查真实页面、补观众问题并形成内容项目。

## 核心输出

- 原始RedFox响应与公开来源清单
- 作品、互动指标和观众问题样本
- 关键词相关性过滤与被排除样本
- 对标结构与不可复制边界
- 带实拍任务、结果画面、对标链接和交付钩子的候选选题
- 选中题证据包与可追溯初稿
- 失败、缺失字段与事实待核验清单

## 安装

```bash
pip install -r requirements.txt
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
python3 skills/yuntu-media-research/scripts/redfox_collect.py status
python3 skills/yuntu-media-research/scripts/redfox_collect.py plan \
  --config skills/yuntu-media-research/assets/example-task.json
python3 skills/yuntu-media-research/scripts/redfox_collect.py collect \
  --config skills/yuntu-media-research/assets/example-task.json \
  --out research-output/codex-for-creators \
  --execute
```

`plan`不会产生付费调用；只有带 `--execute` 的 `collect` 才会请求RedFox。

关键词搜索可能混入同名或偶然命中内容。`required_any_groups`要求每组至少命中一个词，原始采集与过滤结果会同时保留，便于审计。

## Agent使用示例

```text
调用 yuntu-media-research。
我是做AI实用教学的，面向刚开始用AI的内容创作者。
使用RedFox研究近3天抖音正在增长的具体任务，由AI自动取得原料。
给我3条明天能实拍的候选，每条附对标链接、结果画面、Skill钩子和样本限制。
我确认一条后，再输出对标报告和带来源初稿。
```

## 测试

```bash
python3 -m unittest discover -s tests -v
```

发布前还需要运行宿主Agent提供的Skill结构校验，并在macOS与Windows分别完成真实任务验收。

## 平台与状态

Skill本体与Python脚本按macOS和Windows双平台设计，但浏览器控制取决于宿主Agent。`v1.0.0`正在重构：目前只验收了macOS上的RedFox抖音采集层，完整选题到初稿链路与Windows真机仍未验收，因此暂不宣称正式可用或已带来增长结果。

## 设计原则

本项目围绕云途真实内容工作重构：RedFox优先、原料由AI自动采集、近期尾流与长期需求分开、每条候选必须能实拍、每个判断都能回指来源，并在用户确认后才进入对标与初稿。

RedFoxHub及其SDK是独立第三方服务，本项目与RedFoxHub无隶属或官方合作关系。接口费用、可用性和条款以RedFoxHub官方信息为准。

## 许可证

MIT。RedFox第三方服务说明见 `THIRD_PARTY_NOTICES.md`。
