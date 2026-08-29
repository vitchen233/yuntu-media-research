# 通用Agent提示词与执行方式

本Skill不绑定特定Agent。只要宿主能够读取`SKILL.md`、运行脚本或调用MCP，并按需使用浏览器，就可以执行。宿主名称不影响任务结构。

文中的`scripts/`、`references/`和`assets/`都相对于当前Skill根目录解析；不要假设宿主工作区就是Skill目录。

## Agent启动检查

执行任务前按顺序判断：

1. 当前会话是否已有`mcp__redfox__*`工具；有则优先使用。
2. 没有MCP时，能否运行`redfox_catalog.py status`；能则使用SDK。
3. 当前是否有浏览器能力；有则用于寻找或核对具体单条。
4. 没有浏览器时仍可完成RedFox批量分析，但报告必须标记“单条页面未人工核对”。
5. 只有RedFox密钥和浏览器都不可用时，才向用户说明缺少哪项能力；不要要求用户代为整理整批数据。

## 通用调用提示词

```text
调用 yuntu-media-research。
请先判断本题属于选题调研、博主分析还是热点分析，只运行一个主模式。
优先使用当前可用的RedFox MCP；没有MCP时使用Skill自带SDK脚本。
需要寻找或核对具体单条时使用当前Agent的浏览器能力。
先给出简短采集计划和预计请求数，再执行；最后按对应模板输出可展示的调研报告。
不要为了补齐字段接入额外评论API，不要编造浏览器未看到的数据。
```

## 选题调研

```text
调用 yuntu-media-research，运行 topic-research。
研究对象：{{赛道、工具或具体任务}}。
时间范围：默认近3天，样本不足时扩展到7天并说明。
请用浏览器寻找3至5条代表单条，用RedFox补充批量作品与互动数据。
最终只给3条适合拍摄的候选，每条说明目标人群、具体任务、可见结果、推荐开头、怎么拍、对标链接和可交付钩子。
```

## 博主分析

```text
调用 yuntu-media-research，运行 creator-analysis。
分析对象：{{博主名称或主页链接}}。
请采集主页信息和近期作品，建立账号内表现基线，找出代表作品和异常高表现作品。
总结这个博主反复在讲什么、哪些内容结构可以复用、哪些只是偶发热点，并给出3个适合当前创作者借鉴的方向。
评论不是必需项，不要因为没有评论中断分析。
```

## 热点分析

```text
调用 yuntu-media-research，运行 hotspot-analysis。
热点对象：{{关键词、产品、事件或工具}}。
请用RedFox搜索近期作品、增长内容或可用榜单，再用浏览器核对3至5条代表单条。
说明热度来自哪里、目前大家在用什么角度讲、哪些角度已经拥挤、当前创作者最适合从哪个具体任务切入。
最终给3条可拍候选，不写完整稿件。
```

## 输出选择

- `topic-research`使用`assets/topic-research-report.md`。
- `creator-analysis`使用`assets/creator-analysis-report.md`。
- `hotspot-analysis`使用`assets/hotspot-analysis-report.md`。
- 三种模式都先使用`assets/research-brief.md`建立内部简报。

模板用于保证不漏关键结果，不要求空着的章节硬填内容。没有证据的字段直接删除或标记未核对。
