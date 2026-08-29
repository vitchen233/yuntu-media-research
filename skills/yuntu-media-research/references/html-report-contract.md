# 独立HTML报告合同

Agent负责研究与写入`report.json`，`scripts/render_report.py`只负责确定性渲染。页面不得出现示例数字、占位链接或模型编造的来源。

## 通用字段

- `report_type`：`topic-research`、`creator-analysis`或`content-structure-analysis`
- `title`、`summary`、`generated_at`
- `meta`：平台、时间范围、数据层级等短标签
- `metrics`：`label`、`value`、可选`note`
- `method`：实际使用的RedFox接口、浏览器核对和回退过程
- `limitations`：空结果、未收录、字段缺失、转写状态、样本偏差

## topic-research

- `sources[]`：`title`、`author`、`published_at`、`likes`、`comments`、`saves`、`shares`、`url`
- `candidates[]`：`title`、`audience_task`、`visible_result`、`shooting_task`、`delivery_asset`、`evidence`、`benchmark_url`、`tailwind_mode`、`readiness`
- `signal_map[]`：`label`、`share`、`evidence`、`implication`
- `evidence_ladder[]`：`label`、`detail`、`status`
- `source_signals[]`：`title`、`save_rate`、`share_rate`
- `candidate_comparison[]`：`label`、`mode`、`traffic`、`usefulness`、`shootability`、`asset`、`difference`、`total`
- `material_flow[]`：`label`、`detail`

## creator-analysis

- `profile`：`positioning`、`core_audience`、`content_promise`、`conversion_asset`
- `content_map[]`：`label`、`share`、`note`
- `performance_comparison[]`：`label`、`latest`、`hot`、`latest_width`、`hot_width`
- `duration_distribution[]`：`label`、`share`、`note`；`publishing_rhythm[]`与`rhythm_note`记录节奏
- `hook_patterns[]`：`label`、`share`、`mechanism`、`examples[]`、`evidence_level`
- `method_matrix[]`：`stage`、`action`、`proof`、`purpose`、`evidence_level`
- `case_teardowns[]`：`title`、`duration`、`hook`、`method`、`proof`、`cta`、`yuntu_take`、`url`、`evidence_level`
- `conversion_funnel[]`：`stage`、`label`、`detail`、`metric`、`width`
- `engagement_scatter[]`：`title`、`likes`、`save_rate`、`share_rate`、`url`
- `sources[]`：账号内代表作品，字段同上
- `insights[]`：`title`、`detail`、`boundary`

钩子、方法和转化判断必须显示证据级别。只有标题和指标时写“标题编码”或“数据统计”；核对过画面或转写后才能写“视频核验”或“逐字稿验证”。

## content-structure-analysis

- `stages[]`：`time`、`role`、`title`、`detail`、`visual`
- `reusable_patterns[]`：`title`、`detail`
- `draft_direction`：`title`、`opening`、`proofs[]`
- `attention_curve[]`：`time`、`label`、`strength`
- `visual_mix[]`：`label`、`share`、`purpose`
- `information_density[]`：`time`、`label`、`level`、`detail`
- `proof_chain[]`：`label`、`detail`、`visual`
- `shot_map[]`：`time`、`type`、`spoken_role`、`visual_task`、`max_hold`

## 输出要求

```bash
python3 scripts/render_report.py --input report.json --output report.html
```

输出必须是UTF-8单文件HTML，离线可打开，所有来源链接在新标签页打开。报告只展示当前任务真实存在的字段；缺失项进入`limitations`，不能用0或空白伪装成已采集。
