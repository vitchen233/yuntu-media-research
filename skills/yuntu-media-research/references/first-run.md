# 首次使用与宿主适配

## 宿主原则

本Skill不依赖某个智能体的固定工具名。Codex、WorkBuddy、Claude Code或其他支持`SKILL.md`的宿主都执行同一份任务合同：

1. 宿主有RedFox MCP时优先用MCP。
2. 没有MCP时运行本Skill的Python SDK脚本。
3. 宿主有浏览器时核对代表单条；没有时继续批量研究并标注未人工核对。
4. 宿主必须将产物保存到当前工作区，不得只在聊天中展示。

## 自动配置检查

以当前已加载的`SKILL.md`所在目录为Skill根目录。宿主支持`${CLAUDE_SKILL_DIR}`时可使用该变量；否则使用加载文件的绝对路径。不要假设用户当前工作目录就是Skill目录。

用户第一次调用、说“配置”、“无法使用”或当API调用失败时，先运行：

```bash
python3 "<skill根目录>/scripts/doctor.py" --json
```

根据`next_action`处理：

- `ready`：告知用户技术和创作者档案均已就绪，列出选题、账号、单条三种任务，让用户直接说目标。
- `configure-api-key`：不让用户把Key发到聊天。指导其在本地终端运行`python3 "<skill根目录>/scripts/configure_key.py"`，输入完成后重新运行`doctor.py`。
- `install-redfox-sdk`：指导运行`python3 -m pip install "redfox-python-sdk>=0.3.0,<1"`，然后重新检查。
- `configure-creator-profile`：说明技术配置已经通过，但缺少个性化研究上下文。优先引导运行`python3 "<skill根目录>/scripts/configure_profile.py"`并回答简短问题；也可以复制`assets/creator-profile.example.json`修改后用`--input`导入。完成后重新运行`doctor.py`。

默认密钥位置：

- macOS / Linux：`~/.config/yuntu-media-research/.env`
- Windows：`%APPDATA%\yuntu-media-research\.env`

也支持环境变量`REDFOX_API_KEY`和自定义`YUNTU_MEDIA_RESEARCH_ENV`。检查结果只输出是否已配置，绝不输出Key内容。

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
