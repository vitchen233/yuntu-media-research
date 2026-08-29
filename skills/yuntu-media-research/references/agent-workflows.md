# 通用Agent提示词与执行方式

本Skill不绑定特定Agent。只要宿主能够读取`SKILL.md`、运行脚本或调用MCP，并按需使用浏览器，就可以执行。宿主名称不影响任务结构。

文中的`scripts/`、`references/`和`assets/`都相对于当前Skill根目录解析；不要假设宿主工作区就是Skill目录。

## Agent启动检查

执行任务前按顺序判断：

1. 第一次运行`scripts/doctor.py --json`，只读取配置状态，不输出密钥。
2. 读取用户级创作者档案；当前任务明确输入覆盖档案，档案覆盖默认值。缺失最低字段时按`references/first-run.md`引导。
3. 当前会话是否已有RedFox MCP工具；有则优先使用，工具名不强制为某个宿主前缀。
4. 没有MCP时，能否运行`redfox_catalog.py status`；能则使用SDK。
5. 单条任务读取`references/browser-session.md`，判断当前是系统Chrome控制、宿主内置浏览器还是无浏览器，并记录是否复用现有登录。
6. 页面要求登录时由用户自行登录；能连接已登录Chrome时只操作授权标签页，不能连接时明确标记`login-blocked`，不得索取密码、验证码或Cookie。
7. 单条确实需要完整文案时，按`references/local-transcription.md`检测并调用Skill外的FunASR；不要预装或捆绑它。
8. 没有浏览器时仍可完成RedFox批量分析，但报告必须标记`unverified`并删除依赖页面画面的判断。
9. 只有RedFox密钥和浏览器都不可用时，才向用户说明缺少哪项能力；不要要求用户代为整理整批数据。

## 通用调用提示词

面向用户的完整可复制版本见`prompt-library.md`。以下只是Agent内部简版：

```text
调用 yuntu-media-research。
请先判断本题属于选题调研、博主分析还是内容结构拆解，只运行一个主模式。
优先使用当前可用的RedFox MCP；没有MCP时使用Skill自带SDK脚本。
需要寻找或核对具体单条时先检查浏览器通道和登录会话；优先复用用户授权且已经登录的系统Chrome，否则使用宿主独立浏览器并如实记录限制。
近3天选题先使用广域实时库，账号基线再使用优质库，最后由浏览器核对代表单条。
先给出简短采集计划和预计请求数，再执行；最后生成可双击打开的独立HTML报告。
不要索取登录凭据，不要为了补齐字段接入额外评论API，不要编造浏览器未看到的数据。
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

## 内容结构拆解

```text
调用 yuntu-media-research，运行 content-structure-analysis。
分析对象：{{一条公开作品链接}}。
先用浏览器核对页面、章节、可见字幕和画面。确实需要完整文案时，按references/local-transcription.md检测本地FunASR；缺少时征得同意后安装到Skill之外。只有本地方案不可用时才询问是否调用RedFox付费转写。
按时间顺序拆解开头承诺、结果证明、动作推进、判断转折、画面任务和结尾承接。
明确哪些结构可复用、哪些依赖作者人格或未经验证承诺；最后给出当前创作者自己的改写方向，不复制原句。
```

## 从研究结果生成初稿

```text
调用 yuntu-media-research，运行 draft-from-research。
选中题：{{已确认候选题}}。
只读取当前研究任务保存的来源清单、报告、代表作品和真实交付物状态。
先核对开头准备展示的结果是否真实存在，再生成任务型短视频初稿、来源映射和事实审计。
不要复制对标原句、作者人格或未经验证的效率与流量承诺，不写视频包装。
```

## 输出选择

- `topic-research`使用`assets/topic-research-report.md`。
- `creator-analysis`使用`assets/creator-analysis-report.md`。
- `content-structure-analysis`使用`assets/content-structure-analysis-report.md`。
- 三种模式都先使用`assets/research-brief.md`建立内部简报。
- `draft-from-research`使用`references/draft-writing.md`和`assets/short-video-draft.md`。
- 三种模式最终都按`references/html-report-contract.md`生成`report.json`与独立`report.html`。

模板用于保证不漏关键结果，不要求空着的章节硬填内容。没有证据的字段直接删除或标记未核对。
