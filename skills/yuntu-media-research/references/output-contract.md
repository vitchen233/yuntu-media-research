# 输出合同

## capability_catalog.json

每个操作至少包含：`operation_id`、`transport`、`platform`、`capabilities`、`parameters`、`description`和`price_class`。`price_class`无法从官方工具说明识别时必须为`unknown`。

## request_plan.json

必填：`items`。每项包含`operation`、`requests`、`price_class`；只有当前端点文档已核对时才可写`unit_price`。估价必须同时输出未知价格操作。

## brief.json

必填：`task_id`、`creator_niche`、`target_audience`、`platforms`、`time_window`、`goal`、`delivery_asset`、`material_input_mode`、`queries`、`started_at`、`sample_plan`、`stop_conditions`。

## source_manifest.jsonl

每行必填：`source_id`、`url`、`source_type`、`platform`、`title`、`author`、`published_at`、`collected_at`、`access_status`、`observed_fields`、`query`。

## works.jsonl

必填：`work_id`、`source_id`、`platform`、`url`、`title`、`author`、`published_at`。指标缺失设为 `null`。

## audience_questions.jsonl

可选。只有当前任务确实查看了页面评论、搜索问题或其他观众原话时创建。每行包含：`question_id`、`source_id`、`text`、`source_kind`、`collected_at`。不得把分析者总结改写成观众原话。

## topic_cards.jsonl

必填：`topic_id`、`title`、`target_audience`、`audience_task`、`visible_result`、`shooting_task`、`source_ids`、`benchmark_urls`、`tailwind_mode`、`difference`、`opening_direction`、`delivery_asset`、`material_acquisition`、`readiness`。

评分字段 `demand`、`momentum`、`differentiation`、`evidence`、`shootability`、`asset_value` 均为0至5。

`shooting_task`必须具体，例如“让Codex通过RedFox采集近3天AI工具视频并输出带链接的选题表”，不能只写“展示AI提效”。
