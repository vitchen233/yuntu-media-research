# 首次使用与宿主适配

## 宿主原则

本Skill不依赖某个智能体的固定工具名。Codex、WorkBuddy、Claude Code或其他支持`SKILL.md`的宿主都执行同一份任务合同：

1. 宿主有RedFox MCP时优先用MCP。
2. 没有MCP时运行本Skill的Python SDK脚本。
3. 单条任务按`browser-session.md`判断系统Chrome、宿主独立浏览器和登录会话；没有浏览器时继续批量研究并标注未核对。
4. 宿主必须将产物保存到当前工作区，不得只在聊天中展示。

## 自动配置检查

以当前已加载的`SKILL.md`所在目录为Skill根目录。宿主支持`${CLAUDE_SKILL_DIR}`时可使用该变量；否则使用加载文件的绝对路径。不要假设用户当前工作目录就是Skill目录。

用户第一次调用、说“配置”、“无法使用”或当API调用失败时，先运行：

```bash
python3 "<skill根目录>/scripts/doctor.py" --json
```

首次初始化固定使用以下顺序：

```text
步骤1：创作者问卷 → 步骤2：RedFox配置 → 开始使用
```

根据`next_action`处理：

- `ready`：告知用户技术和创作者档案均已就绪，列出选题、账号、单条三种任务，让用户直接说目标。
- `configure-creator-profile`：先在聊天中展示下面的简短问卷。用户回答后，将答案整理为JSON临时文件，运行`python3 "<skill根目录>/scripts/configure_profile.py" --input "<临时JSON路径>"`写入用户级档案，然后删除临时文件并重新运行`doctor.py`。若宿主不能安全创建临时文件，再引导用户直接运行交互式`configure_profile.py`。不要要求用户手工寻找配置目录。
- `configure-api-key`：说明现在进入第2步RedFox配置。不让用户把Key发到聊天。指导其在本地终端运行`python3 "<skill根目录>/scripts/configure_key.py"`，输入完成后重新运行`doctor.py`。
- `install-redfox-sdk`：指导运行`python3 -m pip install "redfox-python-sdk>=0.3.0,<1"`，然后重新检查。

默认密钥位置：

- macOS / Linux：`~/.config/yuntu-media-research/.env`
- Windows：`%APPDATA%\yuntu-media-research\.env`

也支持环境变量`REDFOX_API_KEY`和自定义`YUNTU_MEDIA_RESEARCH_ENV`。检查结果只输出是否已配置，绝不输出Key内容。

## 步骤1：创作者问卷

Agent首次调用时一次询问以下6组问题，允许用户按编号回答：

```text
为了让后面的选题和报告真正适合你，请先回答6组初始化问题：
1. 我应该怎样称呼你？你的身份或内容背景是什么？
2. 你主要做什么赛道？
3. 你主要发布在哪些平台？
4. 你的核心目标受众是谁？他们最想解决什么具体问题？
5. 你当前做内容最重要的目标是什么？通常准备交付什么资料、Skill、源码或服务？
6. 你优先使用或讲解哪些工具？有哪些不想讲、不能讲或不希望作出的承诺？
```

第2、3、4题是最低必填项；其他题可以回答“暂不设置”。用户回答后先用一小段摘要复述，明显歧义才追问一次，不把初始化变成长访谈。用户确认无误后保存档案并进入RedFox配置。

这些信息不是密钥，但仍只用于当前用户的研究上下文。不要提交到Skill仓库，也不要在公开视频、公开报告或分享包中自动展示姓名与私人说明。

## 步骤2：RedFox配置

先检查SDK和API Key。安装命令已经使用`--with-deps`时通常只需配置Key。Key必须由用户在本机隐藏输入，不能通过聊天、截图、临时JSON或创作者档案传递。

## 创作者研究档案

默认位置：

- macOS / Linux：`~/.config/yuntu-media-research/creator-profile.json`
- Windows：`%APPDATA%\yuntu-media-research\creator-profile.json`

也可通过`YUNTU_MEDIA_RESEARCH_PROFILE`指定其他路径。最低必填项为：

1. 主要赛道`creator_niche`；
2. 核心目标受众`target_audience`；
3. 主要发布平台`platforms`。

建议同时填写创作者身份、受众常见问题、内容目标、优先工具、常用交付物和内容边界。档案只保存长期稳定信息，不保存某一期标题、临时热点或未经验证的效果数字。

研究时按以下优先级合并：

```text
当前任务明确输入 > creator-profile.json > Skill默认值
```

如果当前任务已经明确给出最低三项，可以先执行一次性研究；只有用户确认后才写入长期档案。

## 第一次就绪后的对话

用简短自然语言说明：

```text
配置检查和创作者档案都已就绪。我会默认按照你的赛道、受众和平台工作。现在可以帮你做三件事：
1. 找近3天值得拍的选题；
2. 拆解一个公开账号；
3. 拆解一条公开视频的钩子、方法和画面。
直接告诉我你的赛道、博主名或作品链接即可。
```

不在首次引导中向用户展开MCP、SDK、字段统一等实现细节，除非用户主动询问。

浏览器不属于固定的第三个初始化步骤，因为它由具体宿主和目标页面共同决定。第一次遇到单条页面时再自动检查：公开页直接核对；需要登录时优先连接用户已登录的Chrome或让用户在宿主独立浏览器中自行登录；两者都不可用时标记登录受阻，不索取任何登录凭据。
