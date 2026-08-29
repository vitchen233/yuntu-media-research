# 可选本地视频转写

当单条内容结构拆解确实需要完整文案时，优先在用户本机调用官方FunASR。FunASR是外部开源项目，本Skill不捆绑其源码、Python包、模型权重或媒体下载器。

## 使用边界

1. 先用浏览器打开单条页面，核对作者、标题、发布时间、可见字幕和URL。
2. 用户已提供本地视频或音频时直接使用；否则只通过平台允许的下载、保存或用户授权方式取得媒体，不绕过登录、验证码、DRM、付费墙或平台限制。
3. 仅凭页面可见文字即可完成任务时，不安装FunASR。
4. 安装依赖、首次下载模型或调用付费转写前，先说明磁盘、计算和费用影响并征得用户同意。
5. OCR只用于画面中的可见文字，不能替代语音转写。

## 1. 检测现有能力

```bash
command -v ffmpeg
command -v funasr
python3 -c "import funasr; print(funasr.__version__)"
```

Windows PowerShell：

```powershell
Get-Command ffmpeg -ErrorAction SilentlyContinue
Get-Command funasr -ErrorAction SilentlyContinue
py -c "import funasr; print(funasr.__version__)"
```

已有可用FunASR时直接调用，不重复安装。没有时先询问用户是否允许建立隔离环境。

## 2. 在Skill外安装

macOS / Linux推荐安装到用户缓存目录：

```bash
python3 -m venv ~/.cache/yuntu-media-research/funasr-venv
~/.cache/yuntu-media-research/funasr-venv/bin/python -m pip install --upgrade pip
~/.cache/yuntu-media-research/funasr-venv/bin/python -m pip install torch torchaudio funasr
```

Windows PowerShell推荐安装到用户本地数据目录：

```powershell
py -m venv "$env:LOCALAPPDATA\yuntu-media-research\funasr-venv"
& "$env:LOCALAPPDATA\yuntu-media-research\funasr-venv\Scripts\python.exe" -m pip install --upgrade pip
& "$env:LOCALAPPDATA\yuntu-media-research\funasr-venv\Scripts\python.exe" -m pip install torch torchaudio funasr
```

只有用户明确要求从源码安装或检查最新源码时，才从官方仓库拉取到Skill之外：

```bash
git clone --depth 1 https://github.com/modelscope/FunASR.git ~/.cache/yuntu-media-research/FunASR
~/.cache/yuntu-media-research/funasr-venv/bin/python -m pip install -e ~/.cache/yuntu-media-research/FunASR
```

Windows对应目录可使用`$env:LOCALAPPDATA\yuntu-media-research\FunASR`。不要把克隆目录、虚拟环境或模型缓存写入本Skill仓库。

## 3. 准备音频

若输入是用户有权处理的本地视频，可用ffmpeg提取单声道16 kHz音频：

```bash
ffmpeg -i input.mp4 -vn -ac 1 -ar 16000 audio.wav
```

不要声称本Skill内置视频下载能力。无法合法取得本地媒体时，停止本地转写并记录原因。

## 4. 调用FunASR

macOS / Linux示例：

```bash
~/.cache/yuntu-media-research/funasr-venv/bin/funasr audio.wav \
  --model paraformer --language zh --output-format json

~/.cache/yuntu-media-research/funasr-venv/bin/funasr audio.wav \
  --model paraformer --language zh --output-format srt --output-dir ./transcript
```

Windows PowerShell示例：

```powershell
& "$env:LOCALAPPDATA\yuntu-media-research\funasr-venv\Scripts\funasr.exe" audio.wav --model paraformer --language zh --output-format json
& "$env:LOCALAPPDATA\yuntu-media-research\funasr-venv\Scripts\funasr.exe" audio.wav --model paraformer --language zh --output-format srt --output-dir .\transcript
```

首次运行可能下载模型。执行前向用户说明并确认，模型名称与参数以FunASR官方当前文档和本机CLI帮助为准。

## 5. 保存与追溯

在当前研究任务目录保存：

- `transcript/transcript.json`：带时间信息的结构化结果；
- `transcript/transcript.srt`：用于逐段核对的字幕；
- `transcript/transcription_manifest.json`：来源URL、浏览器核对时间、媒体文件哈希、引擎、模型、是否有时间戳和失败记录。

转写文本是机器识别结果，不自动等于作者原稿。报告引用前抽查开头、关键数字、专有名词和转折段。

## 6. RedFox付费回退

仅在以下情况询问是否改用RedFox视频提文案：无法取得可处理的本地媒体、用户拒绝或无法安装本地依赖、本地结果不可用，或者用户明确选择服务端转写。

调用前按当前官方价格重新核对并显示预计费用。已知参考价为`¥0.60/条`时，也必须先确认后执行；轮询免费不代表提交任务免费。

## 第三方许可

FunASR工具包由ModelScope维护，官方仓库声明采用MIT许可证；具体模型可能有独立许可。不要重新分发模型权重，使用前核对所选模型页面的条款。详见仓库根目录`THIRD_PARTY_NOTICES.md`。
