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

- `ready`：告知用户已就绪，列出选题、账号、单条三种任务，让用户直接说目标。
- `configure-api-key`：不让用户把Key发到聊天。指导其在本地终端运行`python3 "<skill根目录>/scripts/configure_key.py"`，输入完成后重新运行`doctor.py`。
- `install-redfox-sdk`：指导运行`python3 -m pip install "redfox-python-sdk>=0.3.0,<1"`，然后重新检查。

默认密钥位置：

- macOS / Linux：`~/.config/yuntu-media-research/.env`
- Windows：`%APPDATA%\yuntu-media-research\.env`

也支持环境变量`REDFOX_API_KEY`和自定义`YUNTU_MEDIA_RESEARCH_ENV`。检查结果只输出是否已配置，绝不输出Key内容。

## 第一次就绪后的对话

用简短自然语言说明：

```text
配置检查通过。我现在可以帮你做三件事：
1. 找近3天值得拍的选题；
2. 拆解一个公开账号；
3. 拆解一条公开视频的钩子、方法和画面。
直接告诉我你的赛道、博主名或作品链接即可。
```

不在首次引导中向用户展开MCP、SDK、字段统一等实现细节，除非用户主动询问。
