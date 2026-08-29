# RedFoxHub接入

核对时间：2026-08-30。官方入口：

- 官网：https://redfox.hk/
- API文档：https://redfox.hk/apis
- 快速开始：https://redfox.hk/quick-start
- Python SDK：https://github.com/redfox-data/redfox-python-sdk

## 当前能力

官方页面列出抖音、小红书、公众号、视频号、快手、B站、今日头条、TikTok、X、YouTube、Instagram等平台。Python SDK README列出14个内容平台及热点、AI搜索和素材工具。

RedFox官方DSH插件提供`redfox-mcp` stdio桥，2026-08-30实测动态返回40个MCP工具。官方Python SDK 0.3.0在同日动态发现137个公开操作。两者能力面不同：MCP便于Agent原生调用，SDK平台面更广，因此本Skill采用双通道适配。

本Skill已验证抖音优质库关键词搜索和AI作品搜索：

```text
POST https://redfox.hk/story/api/dyData/searchArticle
Header: REDFOX_API_KEY
```

官方文档显示参数包含 `keyword`、`startDate`、`endDate`、`offset` 和 `sortType`。返回字段可包含作品链接、标题、正文、发布时间、点赞、评论、收藏、分享、转发、粉丝数、评论热词和数据更新时间。

工具名等AI主题优先使用SDK的 `search_ai_articles`。2026-08-30实测 `Codex` 在近3天返回13条高相关结果，优于优质库组合词搜索。AI作品搜索的部分结果 `url` 为空，本Skill仅在存在 `photoId` 时按抖音标准作品路径生成链接，并记录 `url_basis: calculated-from-photo-id`，后续仍需浏览器抽查。

RedFox还提供抖音每日热门榜、每日点赞飙升榜、七日点赞飙升榜、账号作品、作品详情和视频提文案。后续必须逐接口核对文档后再接入，不凭记忆猜路径或参数。

MCP默认通过`uvx redfox-mcp`启动；需要Python 3.10运行环境，由`uvx`隔离管理。未安装`uv`时继续使用SDK通道，不把MCP不可用误报为RedFox整体不可用。

## 鉴权与费用

- 密钥从 `REDFOX_API_KEY` 环境变量读取。
- 官网也展示 `X-API-KEY` 请求头，但本Skill统一使用 `REDFOX_API_KEY`。
- 2026-08-30页面显示关键词搜索抖音作品优质库为 `¥0.04/次`，价格会变化，以调用时官方页面和账户账单为准。
- 同日官方价格页显示优质数据基价`¥0.04/次`、实时数据基价`¥0.06/次`，并按账户累计请求量提供阶梯折扣。目录从接口说明识别价格类别，无法识别时保持`unknown`，不猜价。
- 新用户可能有免费额度；余额和计费属于RedFox账户，不由本Skill承诺。

## 安全

创建API Key是账户侧持久操作，应由用户在RedFox控制台完成。Skill只检查环境变量是否存在，不输出其内容。`.env`、原始凭据和调用日志不得提交GitHub。

## SDK边界

官方 `redfox-python-sdk` 0.3.0 README声明MIT并在包元数据中标为MIT，但2026-08-30审计提交 `ec393e18e6a46df5ed324d2c9c866a3a6ad2fc53` 未包含独立LICENSE文件。本项目不复制SDK源码，只将其作为可选依赖；发布前再次核对PyPI与仓库许可证状态。
