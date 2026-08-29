#!/usr/bin/env python3
"""Render a standalone, video-ready HTML research report from JSON."""

import argparse
import html
import json
from pathlib import Path


ACCENTS = {
    "topic-research": ("#9e95ff", "#d7a96f"),
    "creator-analysis": ("#54c8b1", "#d7a96f"),
    "content-structure-analysis": ("#de7d6b", "#9e95ff"),
}


def esc(value):
    return html.escape(str(value if value is not None else ""), quote=True)


def number(value):
    try:
        value = float(value)
    except (TypeError, ValueError):
        return esc(value or "-")
    if value >= 10000:
        return f"{value / 10000:.1f}万"
    return f"{int(value):,}"


def link(url, label="查看来源"):
    if not url:
        return '<span class="muted">未提供链接</span>'
    return f'<a href="{esc(url)}" target="_blank" rel="noreferrer">{esc(label)} ↗</a>'


def pills(values):
    return "".join(f'<span class="pill">{esc(value)}</span>' for value in values if value)


def metric_cards(items):
    return "".join(
        f'<div class="metric"><span>{esc(item.get("label"))}</span>'
        f'<strong>{number(item.get("value"))}</strong><small>{esc(item.get("note", ""))}</small></div>'
        for item in items
    )


def source_table(items):
    rows = []
    for item in items:
        metrics = " · ".join(
            f'{label}{number(item.get(key))}'
            for key, label in (("likes", "赞 "), ("comments", "评 "), ("saves", "藏 "), ("shares", "转 "))
            if item.get(key) is not None
        )
        rows.append(
            "<tr>"
            f'<td><b>{esc(item.get("title"))}</b><small>{esc(item.get("author", ""))}</small></td>'
            f'<td>{esc(item.get("published_at", "-"))}</td><td>{esc(metrics or "字段缺失")}</td>'
            f'<td>{link(item.get("url"))}</td></tr>'
        )
    return '<div class="table-wrap"><table><thead><tr><th>作品</th><th>发布时间</th><th>公开指标</th><th>来源</th></tr></thead><tbody>' + "".join(rows) + "</tbody></table></div>"


def pct(value):
    try:
        return max(0, min(100, float(value)))
    except (TypeError, ValueError):
        return 0


def horizontal_bars(items, value_key="share", suffix="%"):
    return "".join(
        f'<div class="bar-row"><div><b>{esc(item.get("label"))}</b><span>{esc(item.get("note", ""))}</span></div>'
        f'<div class="bar"><i style="width:{pct(item.get(value_key, 0))}%"></i></div>'
        f'<strong>{esc(item.get(value_key, 0))}{esc(suffix)}</strong></div>'
        for item in items
    )


def topic_body(data):
    candidates = []
    for index, item in enumerate(data.get("candidates", []), 1):
        candidates.append(
            f'<article class="candidate"><div class="rank">0{index}</div><div><div class="row">'
            f'<span class="status">{esc(item.get("tailwind_mode", "候选"))}</span>'
            f'<span class="score">准备度 {esc(item.get("readiness", "待验证"))}</span></div>'
            f'<h3>{esc(item.get("title"))}</h3><p>{esc(item.get("audience_task"))}</p>'
            f'<dl><div><dt>先展示</dt><dd>{esc(item.get("visible_result"))}</dd></div>'
            f'<div><dt>怎么拍</dt><dd>{esc(item.get("shooting_task"))}</dd></div>'
            f'<div><dt>交付钩子</dt><dd>{esc(item.get("delivery_asset"))}</dd></div></dl>'
            f'<div class="proof"><b>为什么现在做</b><span>{esc(item.get("evidence"))}</span></div>'
            f'<div class="footer-link">{link(item.get("benchmark_url"), "对标作品")}</div></div></article>'
        )
    signal_map = data.get("signal_map", [])
    signal_html = "".join(
        f'<article><span>{esc(item.get("share"))}%</span><h3>{esc(item.get("label"))}</h3>'
        f'<div class="signal-meter"><i style="width:{pct(item.get("share"))}%"></i></div>'
        f'<p>{esc(item.get("evidence"))}</p><small>{esc(item.get("implication"))}</small></article>'
        for item in signal_map
    )
    evidence = "".join(
        f'<div><span>{i:02d}</span><b>{esc(item.get("label"))}</b><p>{esc(item.get("detail"))}</p>'
        f'<small>{esc(item.get("status"))}</small></div>'
        for i, item in enumerate(data.get("evidence_ladder", []), 1)
    )
    candidate_compare = "".join(
        f'<tr><td><b>{esc(item.get("label"))}</b><small>{esc(item.get("mode"))}</small></td>'
        + "".join(f'<td><div class="score-cell"><i style="width:{pct(item.get(key, 0) * 20)}%"></i><span>{esc(item.get(key, 0))}/5</span></div></td>' for key in ("traffic", "usefulness", "shootability", "asset", "difference"))
        + f'<td><strong>{esc(item.get("total"))}</strong></td></tr>'
        for item in data.get("candidate_comparison", [])
    )
    source_signals = "".join(
        f'<article><b>{esc(item.get("title"))}</b><div class="ratio-row"><span>收藏/点赞</span><i style="width:{pct(item.get("save_rate", 0) * 100)}%"></i><strong>{float(item.get("save_rate", 0)):.0%}</strong></div>'
        f'<div class="ratio-row"><span>转发/点赞</span><i style="width:{pct(item.get("share_rate", 0) * 100)}%"></i><strong>{float(item.get("share_rate", 0)):.0%}</strong></div></article>'
        for item in data.get("source_signals", [])
    )
    flow = "".join(f'<div><span>{i:02d}</span><b>{esc(item.get("label"))}</b><p>{esc(item.get("detail"))}</p></div>' for i, item in enumerate(data.get("material_flow", []), 1))
    parts = []
    if signal_html:
        parts.append(section("观众正在用什么方式找答案", f'<div class="signal-grid">{signal_html}</div>'))
    if evidence:
        parts.append(section("证据链：从搜索热度到可拍任务", f'<div class="evidence-ladder">{evidence}</div>'))
    if source_signals:
        parts.append(section("代表作品的行动信号", f'<div class="source-signal-grid">{source_signals}</div>'))
    parts.append(section("近3天代表作品", source_table(data.get("sources", []))))
    parts.append(section("3条可拍候选", '<div class="candidate-grid">' + "".join(candidates) + "</div>"))
    if candidate_compare:
        parts.append(section("候选比较：不只看热度", '<div class="table-wrap"><table><thead><tr><th>候选</th><th>流量</th><th>实用</th><th>可拍</th><th>资产</th><th>差异</th><th>总分</th></tr></thead><tbody>' + candidate_compare + '</tbody></table></div>'))
    if flow:
        parts.append(section("素材怎么由AI自己采集", f'<div class="flow-strip">{flow}</div>'))
    return "".join(parts)


def creator_body(data):
    profile = data.get("profile", {})
    profile_html = "".join(
        f'<div><span>{esc(label)}</span><strong>{esc(profile.get(key, "-"))}</strong></div>'
        for key, label in (("positioning", "账号定位"), ("core_audience", "核心人群"), ("content_promise", "内容承诺"), ("conversion_asset", "转化资产"))
    )
    comparison = data.get("performance_comparison", [])
    comparison_html = "".join(
        f'<div class="compare-row"><b>{esc(item.get("label"))}</b><div class="compare-track">'
        f'<i class="latest" style="width:{pct(item.get("latest_width", 0))}%"></i>'
        f'<i class="hot" style="width:{pct(item.get("hot_width", 0))}%"></i></div>'
        f'<span>最新 {number(item.get("latest"))}</span><strong>高表现 {number(item.get("hot"))}</strong></div>'
        for item in comparison
    )
    hooks = data.get("hook_patterns", [])
    hook_html = "".join(
        f'<article class="hook-item"><div class="hook-top"><span>{esc(item.get("share"))}%</span><b>{esc(item.get("label"))}</b>'
        f'<em>{esc(item.get("evidence_level", "标题编码"))}</em></div><div class="hook-meter"><i style="width:{pct(item.get("share"))}%"></i></div>'
        f'<p>{esc(item.get("mechanism"))}</p><small>{esc("｜".join(item.get("examples", [])))}</small></article>'
        for item in hooks
    )
    methods = "".join(
        f'<tr><td><span class="step-no">{i:02d}</span><b>{esc(item.get("stage"))}</b></td>'
        f'<td>{esc(item.get("action"))}</td><td>{esc(item.get("proof"))}</td><td>{esc(item.get("purpose"))}</td>'
        f'<td><span class="evidence-tag">{esc(item.get("evidence_level", "综合归纳"))}</span></td></tr>'
        for i, item in enumerate(data.get("method_matrix", []), 1)
    )
    cases = "".join(
        f'<article class="case-teardown"><div class="case-head"><span>{esc(item.get("duration"))}</span><h3>{esc(item.get("title"))}</h3><em>{esc(item.get("evidence_level", "逐字稿验证"))}</em></div>'
        f'<dl><div><dt>开头钩子</dt><dd>{esc(item.get("hook"))}</dd></div><div><dt>内容方法</dt><dd>{esc(item.get("method"))}</dd></div>'
        f'<div><dt>证明方式</dt><dd>{esc(item.get("proof"))}</dd></div><div><dt>结尾动作</dt><dd>{esc(item.get("cta"))}</dd></div></dl>'
        f'<p><b>云途判断</b>{esc(item.get("yuntu_take"))}</p>{link(item.get("url"), "打开原作品")}</article>'
        for item in data.get("case_teardowns", [])
    )
    funnel = "".join(
        f'<article style="--funnel-width:{pct(item.get("width", 100))}%"><span>{esc(item.get("stage"))}</span>'
        f'<h3>{esc(item.get("label"))}</h3><p>{esc(item.get("detail"))}</p><small>{esc(item.get("metric", ""))}</small></article>'
        for item in data.get("conversion_funnel", [])
    )
    scatter = "".join(
        f'<a class="scatter-dot" href="{esc(item.get("url", "#"))}" target="_blank" rel="noreferrer" '
        f'style="left:{pct(item.get("save_rate", 0) * 100)}%;bottom:{pct(item.get("share_rate", 0) * 250)}%;--dot:{max(10, min(30, 10 + float(item.get("likes", 0)) / 2000))}px" '
        f'title="{esc(item.get("title"))} · 收藏率{float(item.get("save_rate", 0)):.0%} · 转发率{float(item.get("share_rate", 0)):.0%}"></a>'
        for item in data.get("engagement_scatter", [])
    )
    insights = "".join(
        f'<article class="insight"><span>0{i}</span><h3>{esc(item.get("title"))}</h3><p>{esc(item.get("detail"))}</p>'
        f'<small>{esc(item.get("boundary", ""))}</small></article>'
        for i, item in enumerate(data.get("insights", []), 1)
    )
    parts = [section("账号定位与内容生意", f'<div class="profile-strip">{profile_html}</div>')]
    parts.append(section("账号内容地图", f'<div class="bars">{horizontal_bars(data.get("content_map", []))}</div>'))
    if comparison:
        parts.append(section("最新样本 vs 高表现样本", f'<div class="compare"><div class="legend"><i></i>最新20条 <i></i>高表现20条</div>{comparison_html}</div>'))
    if data.get("duration_distribution"):
        parts.append(section("时长与发布节奏", f'<div class="split-chart"><div class="bars">{horizontal_bars(data.get("duration_distribution", []))}</div><div class="rhythm">{pills(data.get("publishing_rhythm", []))}<p>{esc(data.get("rhythm_note", ""))}</p></div></div>'))
    if hooks:
        parts.append(section("钩子系统：他怎么让人停下来", f'<div class="hook-grid">{hook_html}</div>'))
    if methods:
        parts.append(section("内容方法：一条视频怎么往前推", '<div class="table-wrap"><table><thead><tr><th>阶段</th><th>内容动作</th><th>证明方式</th><th>观众作用</th><th>证据级别</th></tr></thead><tbody>' + methods + '</tbody></table></div>'))
    if cases:
        parts.append(section("三条高表现作品：钩子到CTA逐条拆解", f'<div class="case-grid">{cases}</div>'))
    if funnel:
        parts.append(section("从停留到领取：内容转化路径", f'<div class="funnel">{funnel}</div>'))
    if scatter:
        parts.append(section("高表现作品的收藏 / 转发结构", f'<div class="scatter"><div class="axis y">转发率 ↑</div><div class="axis x">收藏率 →</div>{scatter}<div class="quadrant q1">方法资产</div><div class="quadrant q2">话题传播</div></div><p class="chart-note">横轴为收藏/点赞，纵轴为转发/点赞，点越大代表点赞越高。悬停可查看具体作品。</p>'))
    parts.append(section("账号内高表现作品", source_table(data.get("sources", []))))
    parts.append(section("可以借鉴，但不能照搬", f'<div class="insight-grid">{insights}</div>'))
    return "".join(parts)


def structure_body(data):
    stages = "".join(
        f'<article class="stage"><time>{esc(item.get("time"))}</time><div><span>{esc(item.get("role"))}</span>'
        f'<h3>{esc(item.get("title"))}</h3><p>{esc(item.get("detail"))}</p>'
        f'<small>画面：{esc(item.get("visual"))}</small></div></article>'
        for item in data.get("stages", [])
    )
    reuse = "".join(f'<li><b>{esc(item.get("title"))}</b><span>{esc(item.get("detail"))}</span></li>' for item in data.get("reusable_patterns", []))
    draft = data.get("draft_direction", {})
    draft_html = f'<div class="draft"><span>云途改写方向</span><h3>{esc(draft.get("title"))}</h3><p>{esc(draft.get("opening"))}</p><div>{pills(draft.get("proofs", []))}</div></div>'
    source = f'<div class="draft"><span>公开分析对象</span><h3>{esc(data.get("source_title", "单条公开作品"))}</h3><p>{esc(data.get("source_note", ""))}</p>{link(data.get("source_url"), "打开原作品")}</div>'
    attention = "".join(
        f'<div><i style="height:{pct(item.get("strength", 0))}%"></i><span>{esc(item.get("time"))}</span><small>{esc(item.get("label"))}</small></div>'
        for item in data.get("attention_curve", [])
    )
    visual_mix = "".join(
        f'<article style="--mix:{pct(item.get("share", 0))}%"><span>{esc(item.get("share"))}%</span><b>{esc(item.get("label"))}</b><p>{esc(item.get("purpose"))}</p></article>'
        for item in data.get("visual_mix", [])
    )
    density = "".join(
        f'<article><time>{esc(item.get("time"))}</time><b>{esc(item.get("label"))}</b><div class="density-dots">'
        + "".join(f'<i class="{"on" if dot < int(item.get("level", 0)) else ""}"></i>' for dot in range(5))
        + f'</div><p>{esc(item.get("detail"))}</p></article>'
        for item in data.get("information_density", [])
    )
    proof_chain = "".join(
        f'<div><span>{i:02d}</span><h3>{esc(item.get("label"))}</h3><p>{esc(item.get("detail"))}</p><small>{esc(item.get("visual"))}</small></div>'
        for i, item in enumerate(data.get("proof_chain", []), 1)
    )
    shot_map = "".join(
        f'<tr><td>{esc(item.get("time"))}</td><td><span class="shot-type">{esc(item.get("type"))}</span></td>'
        f'<td>{esc(item.get("spoken_role"))}</td><td>{esc(item.get("visual_task"))}</td><td>{esc(item.get("max_hold"))}</td></tr>'
        for item in data.get("shot_map", [])
    )
    parts = [section("分析对象", source)]
    if attention:
        parts.append(section("注意力曲线：什么时候必须换信息", f'<div class="attention-chart">{attention}</div>'))
    if visual_mix:
        parts.append(section("画面组成：A-roll、录屏与结果页", f'<div class="visual-mix">{visual_mix}</div>'))
    if density:
        parts.append(section("信息密度分布", f'<div class="density-grid">{density}</div>'))
    parts.append(section("内容推进时间轴", f'<div class="timeline">{stages}</div>'))
    if proof_chain:
        parts.append(section("证明链：不是只说“很强”", f'<div class="proof-chain">{proof_chain}</div>'))
    if shot_map:
        parts.append(section("口播与画面对应表", '<div class="table-wrap"><table><thead><tr><th>时段</th><th>画面类型</th><th>话语作用</th><th>画面任务</th><th>建议最长停留</th></tr></thead><tbody>' + shot_map + '</tbody></table></div>'))
    parts.append(section("可复用结构", f'<ol class="reuse">{reuse}</ol>'))
    parts.append(section("不是照抄，而是进入自己的任务", draft_html))
    return "".join(parts)


def section(title, body):
    return f'<section><div class="section-head"><span></span><h2>{esc(title)}</h2></div>{body}</section>'


def render(data):
    report_type = data.get("report_type")
    if report_type not in ACCENTS:
        raise ValueError(f"unsupported report_type: {report_type}")
    accent, accent2 = ACCENTS[report_type]
    body = {"topic-research": topic_body, "creator-analysis": creator_body, "content-structure-analysis": structure_body}[report_type](data)
    limitations = "".join(f"<li>{esc(item)}</li>" for item in data.get("limitations", []))
    return f'''<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(data.get("title"))}</title><style>
:root{{--bg:#090806;--panel:#151411;--panel2:#1d1b17;--text:#f3efe8;--muted:#a8a39a;--line:#34312b;--accent:{accent};--accent2:{accent2};}}
*{{box-sizing:border-box}}html{{scroll-behavior:smooth}}body{{margin:0;background:var(--bg);color:var(--text);font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei",sans-serif;letter-spacing:0;}}
body:before{{content:"";position:fixed;inset:0;pointer-events:none;background-image:linear-gradient(rgba(255,255,255,.025) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,.025) 1px,transparent 1px);background-size:48px 48px;mask-image:linear-gradient(to bottom,#000,transparent 70%);}}
a{{color:var(--accent2);text-decoration:none}}a:hover{{text-decoration:underline}}.shell{{width:min(1440px,calc(100% - 48px));margin:auto;position:relative}}header{{min-height:440px;display:grid;align-content:center;padding:72px 0 56px;border-bottom:1px solid var(--line)}}
.brand{{display:flex;align-items:center;gap:12px;color:var(--muted);font-size:13px;font-weight:700;text-transform:uppercase}}.brand i{{width:28px;height:28px;display:grid;place-items:center;border:1px solid var(--accent);color:var(--accent);font-style:normal}}.eyebrow{{margin:64px 0 16px;color:var(--accent2);font-size:14px;font-weight:700}}
h1{{max-width:1100px;margin:0;font-size:clamp(42px,6vw,86px);line-height:1.05;letter-spacing:0}}.summary{{max-width:840px;margin:26px 0 0;color:#cbc6bc;font-size:19px;line-height:1.8}}.meta{{display:flex;flex-wrap:wrap;gap:10px;margin-top:28px}}.pill,.status{{border:1px solid var(--line);padding:7px 11px;font-size:12px;color:#d5d0c6;background:#11100e}}
.metrics{{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:1px;background:var(--line);margin:0 0 80px;border:1px solid var(--line)}}.metric{{min-height:145px;padding:24px;background:var(--panel)}}.metric span,.metric small{{display:block;color:var(--muted);font-size:12px}}.metric strong{{display:block;margin:16px 0 8px;font-size:34px;color:var(--accent)}}
main{{padding:64px 0 100px}}section{{margin-bottom:84px}}.section-head{{display:flex;align-items:center;gap:14px;margin-bottom:26px}}.section-head>span{{width:34px;height:2px;background:linear-gradient(90deg,var(--accent),var(--accent2))}}h2{{margin:0;font-size:26px}}h3{{letter-spacing:0}}
.table-wrap{{overflow:auto;border:1px solid var(--line)}}table{{width:100%;border-collapse:collapse;min-width:900px}}th,td{{padding:18px;text-align:left;border-bottom:1px solid var(--line);vertical-align:top}}th{{color:var(--muted);font-size:12px;background:#11100e}}td{{font-size:14px}}td b,td small{{display:block;max-width:560px}}td small{{margin-top:8px;color:var(--muted)}}
.candidate-grid{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px}}.candidate{{display:grid;grid-template-columns:44px 1fr;gap:16px;padding:24px;background:var(--panel);border:1px solid var(--line);border-top:3px solid var(--accent)}}.rank{{color:var(--accent);font-weight:800}}.row{{display:flex;justify-content:space-between;gap:12px}}.score{{font-size:12px;color:var(--muted)}}.candidate h3{{font-size:22px;line-height:1.4;margin:22px 0 12px}}.candidate p{{color:#cbc6bc;line-height:1.75}}dl{{margin:24px 0}}dl div{{padding:12px 0;border-top:1px solid var(--line)}}dt{{color:var(--muted);font-size:12px}}dd{{margin:6px 0 0;line-height:1.6}}.proof{{padding:14px;background:#0f0e0c;border-left:2px solid var(--accent2)}}.proof b,.proof span{{display:block}}.proof span{{margin-top:6px;color:var(--muted);font-size:13px;line-height:1.6}}.footer-link{{margin-top:18px}}
.signal-grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:12px}}.signal-grid article{{padding:22px;border:1px solid var(--line);background:var(--panel)}}.signal-grid article>span{{font-size:28px;color:var(--accent)}}.signal-grid p{{color:#cbc6bc;line-height:1.7}}.signal-grid small{{color:var(--muted);line-height:1.6}}.signal-meter{{height:5px;background:#292620;margin:14px 0}}.signal-meter i{{display:block;height:100%;background:var(--accent)}}
.evidence-ladder{{display:grid;grid-template-columns:repeat(4,1fr);gap:1px;background:var(--line);border:1px solid var(--line)}}.evidence-ladder>div{{padding:22px;background:var(--panel)}}.evidence-ladder span{{color:var(--accent)}}.evidence-ladder p{{color:#cbc6bc;line-height:1.7}}.evidence-ladder small{{color:var(--accent2)}}.source-signal-grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}}.source-signal-grid article{{padding:20px;border:1px solid var(--line);background:var(--panel)}}.ratio-row{{display:grid;grid-template-columns:90px 1fr 46px;gap:10px;align-items:center;margin-top:16px;font-size:12px}}.ratio-row i{{height:6px;background:var(--accent)}}.score-cell{{min-width:100px}}.score-cell i{{display:block;height:6px;background:var(--accent);margin-bottom:6px}}.score-cell span{{font-size:11px;color:var(--muted)}}.flow-strip{{display:grid;grid-template-columns:repeat(5,1fr);border:1px solid var(--line)}}.flow-strip>div{{padding:20px;border-right:1px solid var(--line);background:var(--panel)}}.flow-strip>div:last-child{{border:0}}.flow-strip span{{color:var(--accent)}}.flow-strip p{{color:var(--muted);line-height:1.7}}
.bars{{padding:26px;border:1px solid var(--line);background:var(--panel)}}.bar-row{{display:grid;grid-template-columns:260px 1fr 60px;gap:18px;align-items:center;padding:16px 0}}.bar-row span{{display:block;color:var(--muted);font-size:12px;margin-top:5px}}.bar{{height:8px;background:#292620}}.bar i{{display:block;height:100%;background:linear-gradient(90deg,var(--accent),var(--accent2))}}.insight-grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:16px}}.insight{{padding:24px;border:1px solid var(--line);background:var(--panel)}}.insight>span{{color:var(--accent)}}.insight p{{color:#cbc6bc;line-height:1.8}}.insight small{{display:block;color:var(--muted);border-top:1px solid var(--line);padding-top:14px}}
.profile-strip{{display:grid;grid-template-columns:repeat(4,1fr);border:1px solid var(--line)}}.profile-strip>div{{padding:22px;border-right:1px solid var(--line);background:var(--panel)}}.profile-strip>div:last-child{{border:0}}.profile-strip span,.profile-strip strong{{display:block}}.profile-strip span{{font-size:12px;color:var(--muted);margin-bottom:10px}}.profile-strip strong{{line-height:1.55}}
.compare{{border:1px solid var(--line);padding:26px;background:var(--panel)}}.legend{{display:flex;gap:14px;align-items:center;color:var(--muted);font-size:12px;margin-bottom:16px}}.legend i{{width:11px;height:11px;background:var(--accent)}}.legend i:nth-child(2){{background:var(--accent2)}}.compare-row{{display:grid;grid-template-columns:120px 1fr 130px 150px;gap:16px;align-items:center;padding:13px 0}}.compare-row span,.compare-row strong{{font-size:13px}}.compare-track{{display:grid;gap:5px}}.compare-track i{{display:block;height:7px}}.compare-track .latest{{background:var(--accent)}}.compare-track .hot{{background:var(--accent2)}}
.split-chart{{display:grid;grid-template-columns:1.4fr .6fr;gap:18px}}.rhythm{{border:1px solid var(--line);padding:26px;background:var(--panel)}}.rhythm .pill{{display:inline-block;margin:0 6px 8px 0}}.rhythm p{{color:var(--muted);line-height:1.8;margin:18px 0 0}}
.hook-grid{{display:grid;grid-template-columns:repeat(2,1fr);gap:14px}}.hook-item{{padding:22px;border:1px solid var(--line);background:var(--panel)}}.hook-top{{display:grid;grid-template-columns:52px 1fr auto;align-items:center;gap:10px}}.hook-top span{{font-size:22px;color:var(--accent)}}.hook-top em,.evidence-tag{{font-style:normal;font-size:11px;color:var(--muted);border:1px solid var(--line);padding:5px 7px}}.hook-meter{{height:5px;background:#292620;margin:16px 0}}.hook-meter i{{display:block;height:100%;background:linear-gradient(90deg,var(--accent),var(--accent2))}}.hook-item p{{line-height:1.7;color:#cbc6bc}}.hook-item small{{color:var(--muted);line-height:1.7}}.step-no{{color:var(--accent);margin-right:12px}}
.case-grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}}.case-teardown{{padding:24px;border:1px solid var(--line);border-top:3px solid var(--accent);background:var(--panel)}}.case-head{{display:grid;grid-template-columns:auto 1fr;gap:10px;align-items:center}}.case-head span{{color:var(--accent);font-weight:800}}.case-head h3{{margin:0;font-size:20px}}.case-head em{{grid-column:2;font-style:normal;color:var(--muted);font-size:11px}}.case-teardown dl{{margin:20px 0}}.case-teardown p{{padding-top:14px;border-top:1px solid var(--line);color:var(--muted);line-height:1.7}}.case-teardown p b{{display:block;color:var(--accent2);margin-bottom:6px}}
.funnel{{display:grid;gap:8px;justify-items:center}}.funnel article{{width:var(--funnel-width);min-width:46%;padding:18px 24px;border:1px solid var(--line);background:var(--panel);display:grid;grid-template-columns:90px 190px 1fr auto;gap:18px;align-items:center}}.funnel article span,.funnel article small{{color:var(--muted);font-size:12px}}.funnel article h3,.funnel article p{{margin:0}}.funnel article p{{color:#cbc6bc;line-height:1.6}}
.scatter{{height:420px;position:relative;border-left:1px solid var(--line);border-bottom:1px solid var(--line);background:linear-gradient(90deg,transparent 49.8%,var(--line) 50%,transparent 50.2%),linear-gradient(transparent 49.8%,var(--line) 50%,transparent 50.2%)}}.scatter-dot{{position:absolute;width:var(--dot);height:var(--dot);border-radius:50%;background:var(--accent);border:2px solid #efe9df;transform:translate(-50%,50%);opacity:.86;z-index:2}}.scatter-dot:hover{{opacity:1;box-shadow:0 0 0 7px rgba(84,200,177,.18)}}.axis{{position:absolute;color:var(--muted);font-size:12px}}.axis.y{{left:10px;top:10px}}.axis.x{{right:10px;bottom:10px}}.quadrant{{position:absolute;color:rgba(255,255,255,.18);font-size:22px;font-weight:700}}.q1{{right:8%;top:10%}}.q2{{left:8%;top:10%}}.chart-note{{color:var(--muted);font-size:12px}}
.timeline{{border-left:1px solid var(--line);margin-left:70px}}.stage{{display:grid;grid-template-columns:74px 1fr;gap:24px;margin-left:-70px;padding:0 0 28px}}.stage time{{color:var(--accent);font-weight:800;padding-top:22px}}.stage>div{{position:relative;padding:20px 24px;background:var(--panel);border:1px solid var(--line)}}.stage>div:before{{content:"";position:absolute;width:9px;height:9px;left:-29px;top:26px;background:var(--accent);border-radius:50%}}.stage span,.stage small{{color:var(--muted);font-size:12px}}.stage h3{{margin:8px 0}}.stage p{{color:#cbc6bc;line-height:1.75}}.reuse{{display:grid;grid-template-columns:repeat(3,1fr);gap:1px;background:var(--line);padding:1px;list-style-position:inside}}.reuse li{{padding:24px;background:var(--panel)}}.reuse b,.reuse span{{display:block}}.reuse span{{margin-top:10px;color:var(--muted);line-height:1.7}}.draft{{padding:36px;border:1px solid var(--accent);background:linear-gradient(120deg,rgba(158,149,255,.08),rgba(215,169,111,.05))}}.draft>span{{color:var(--accent2)}}.draft h3{{font-size:30px;margin:14px 0}}.draft p{{font-size:17px;line-height:1.8;max-width:900px}}
.attention-chart{{height:300px;display:grid;grid-template-columns:repeat(6,1fr);gap:12px;align-items:end;padding:28px 28px 18px;border:1px solid var(--line);background:repeating-linear-gradient(to top,transparent 0,transparent 59px,var(--line) 60px)}}.attention-chart>div{{height:240px;display:grid;grid-template-rows:1fr auto auto;align-items:end;text-align:center}}.attention-chart i{{width:64%;justify-self:center;background:linear-gradient(to top,var(--accent2),var(--accent));min-height:20px}}.attention-chart span{{font-size:12px;margin-top:10px}}.attention-chart small{{color:var(--muted);margin-top:5px}}.visual-mix{{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}}.visual-mix article{{padding:24px;border-top:6px solid var(--accent);background:linear-gradient(90deg,var(--panel) var(--mix),#0f0e0c var(--mix));border-left:1px solid var(--line);border-right:1px solid var(--line);border-bottom:1px solid var(--line)}}.visual-mix span{{font-size:30px;color:var(--accent)}}.visual-mix b{{display:block;margin-top:10px}}.visual-mix p{{color:var(--muted);line-height:1.7}}.density-grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}}.density-grid article{{padding:20px;border:1px solid var(--line);background:var(--panel)}}.density-grid time,.density-grid b{{display:block}}.density-grid time{{color:var(--accent);font-size:12px}}.density-grid b{{margin:8px 0}}.density-grid p{{color:var(--muted);line-height:1.65}}.density-dots{{display:flex;gap:5px;margin:12px 0}}.density-dots i{{width:24px;height:5px;background:#292620}}.density-dots i.on{{background:var(--accent)}}.proof-chain{{display:grid;grid-template-columns:repeat(4,1fr);gap:1px;background:var(--line);border:1px solid var(--line)}}.proof-chain>div{{padding:22px;background:var(--panel)}}.proof-chain span{{color:var(--accent)}}.proof-chain p{{color:#cbc6bc;line-height:1.7}}.proof-chain small{{color:var(--muted)}}.shot-type{{display:inline-block;border:1px solid var(--accent);color:var(--accent);padding:5px 8px;font-size:11px}}
.audit{{display:grid;grid-template-columns:1fr 1fr;gap:24px;padding:28px;background:#11100e;border:1px solid var(--line)}}.audit h3{{margin-top:0}}.audit ul{{margin:0;padding-left:20px;color:var(--muted);line-height:1.8}}.muted{{color:var(--muted)}}footer{{padding:32px 0 56px;color:var(--muted);font-size:12px;border-top:1px solid var(--line)}}
@media(max-width:900px){{.shell{{width:min(100% - 28px,1440px)}}header{{min-height:380px}}.metrics,.candidate-grid,.insight-grid,.reuse,.profile-strip,.split-chart,.hook-grid,.case-grid,.signal-grid,.evidence-ladder,.source-signal-grid,.flow-strip,.visual-mix,.density-grid,.proof-chain{{grid-template-columns:1fr}}.profile-strip>div,.flow-strip>div{{border-right:0;border-bottom:1px solid var(--line)}}.bar-row,.compare-row{{grid-template-columns:1fr}}.funnel article{{width:100%;grid-template-columns:1fr}}.attention-chart{{overflow-x:auto;grid-template-columns:repeat(6,120px)}}.audit{{grid-template-columns:1fr}}h1{{font-size:42px}}}}
</style></head><body><div class="shell"><header><div class="brand"><i>YT</i> YUNTU MEDIA RESEARCH</div><div class="eyebrow">{esc(data.get("kicker", "真实公开数据 · 可追溯研究"))}</div><h1>{esc(data.get("title"))}</h1><p class="summary">{esc(data.get("summary"))}</p><div class="meta">{pills(data.get("meta", []))}</div></header><main><div class="metrics">{metric_cards(data.get("metrics", []))}</div>{body}<section class="audit"><div><h3>数据与方法</h3><p class="muted">{esc(data.get("method", ""))}</p></div><div><h3>限制与失败记录</h3><ul>{limitations}</ul></div></section></main><footer>YUNTU MEDIA RESEARCH · 生成时间 {esc(data.get("generated_at", ""))} · 页面为独立HTML，可离线打开</footer></div></body></html>'''


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    data = json.loads(Path(args.input).read_text(encoding="utf-8"))
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render(data), encoding="utf-8")
    print(f"wrote {output}")


if __name__ == "__main__":
    main()
